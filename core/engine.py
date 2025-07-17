# core/engine.py
# FINAL REWRITE to be a robust, non-locking, parallel execution engine with verbose logging.

import inspect
import json
import pkgutil
import importlib
import asyncio
from collections import defaultdict

from core.definitions import BaseNode, InputWidget, SKIP_OUTPUT, NodeStateUpdate

class NodeEngine:
    def __init__(self):
        self.node_classes = {}
        self.discover_nodes()

    def discover_nodes(self):
        import nodes
        for _, name, _ in pkgutil.walk_packages(nodes.__path__, nodes.__name__ + '.'):
            try:
                module = importlib.import_module(name)
                for _, item in inspect.getmembers(module, inspect.isclass):
                    if issubclass(item, BaseNode) and item is not BaseNode:
                        self.node_classes[item.__name__] = item
            except Exception as e:
                print(f"Error importing node module {name}: {e}")
        print(f"Discovered nodes: {list(self.node_classes.keys())}")

    def generate_ui_blueprints(self):
        all_node_definitions = []
        for name, node_class in self.node_classes.items():
            # Pass the full socket definition to the frontend
            inputs_def = [
                {"name": n, **s} for n, s in node_class.INPUT_SOCKETS.items()
            ]
            outputs_def = [
                {"name": n, **s} for n, s in node_class.OUTPUT_SOCKETS.items()
            ]
            # Convert enums to string values for JSON serialization
            for item_def in inputs_def + outputs_def:
                if 'type' in item_def and hasattr(item_def['type'], 'value'):
                    item_def['type'] = item_def['type'].value

            node_def = {
                "name": name, "category": node_class.CATEGORY,
                "inputs": inputs_def,
                "outputs": outputs_def,
                "widgets": []
            }
            widget_declarations = sorted(
                [w for w in inspect.getmembers(node_class) if isinstance(w[1], InputWidget)],
                key=lambda x: x[1].order
            )
            for attr_name, attr_value in widget_declarations:
                node_def["widgets"].append({
                    "name": attr_name, "type": attr_value.widget_type,
                    "default": attr_value.default, "properties": attr_value.properties
                })
            all_node_definitions.append(node_def)
        return json.dumps(all_node_definitions, indent=2)

    async def run_workflow(self, graph_data, start_node_id, websocket):
        await websocket.send_text("Engine: Initializing workflow...")
        print("\n--- NEW WORKFLOW RUN ---")

        # 1. --- Initialization ---
        node_memory = defaultdict(dict)
        nodes_map = {
            str(n['id']): self.node_classes[n['type'].split('/')[-1]](self, n, node_memory[str(n['id'])])
            for n in graph_data['nodes'] if n['type'].split('/')[-1] in self.node_classes
        }

        # Inject the websocket context into each node instance for this run.
        for node in nodes_map.values():
            node._websocket = websocket

        for node in nodes_map.values():
            node.load()
        await websocket.send_text("Engine: All nodes loaded.")

        # 2. --- Context Setup ---
        run_context = {
            "nodes": nodes_map, "websocket": websocket,
            "node_states": defaultdict(lambda: "PENDING"),
            "input_cache": defaultdict(dict), "waiting_on": defaultdict(list),
            "outputs_cache": {}, "active_tasks": set(),
            "source_map": {}, "target_map": defaultdict(list),
            "node_memory": node_memory,
            "node_wait_configs": defaultdict(list)
        }
        for link_data in graph_data['links']:
            _, source_id, source_slot, target_id, target_slot, _ = link_data
            source_id, target_id = str(source_id), str(target_id)
            source_key = f"{source_id}:{source_slot}"
            target_key = f"{target_id}:{target_slot}"
            run_context["source_map"][target_key] = source_key
            run_context["target_map"][source_key].append(target_key)


        # 3. --- Main Execution Block ---
        try:
            # ... (All the inner function definitions like trigger_node, execute_node, etc. go here)
            async def trigger_node(node_id, activated_by_inputs=None):
                node_state = run_context["node_states"][node_id]

                if node_state == "EXECUTING":
                    return

                if node_state == "DONE":
                    node_instance = run_context["nodes"][node_id]
                    
                    print(f"LOG: Resetting completed node {node_id} for re-trigger.")
                    run_context["node_states"][node_id] = "PENDING"
                    node_state = "PENDING"
                    
                    # Use the (potentially dynamic) wait config for the reset
                    wait_config = run_context["node_wait_configs"][node_id]
                    run_context["waiting_on"][node_id] = list(wait_config)

                    # Clear only the inputs that the node is now waiting for.
                    cache = run_context["input_cache"][node_id]
                    keys_to_delete = [key for key in cache if key in wait_config]
                    for key in keys_to_delete:
                        del cache[key]
                    
                    print(f"LOG: Cleared waiting inputs for {node_id}. Waiting for: {run_context['waiting_on'][node_id]}")


                if node_state == "PENDING":
                    first_input = activated_by_inputs[0] if activated_by_inputs else None
                    await setup_node_for_execution(node_id, graph_data, first_input)
                
                if activated_by_inputs:
                    await process_incoming_data(node_id, activated_by_inputs)

                if run_context["node_states"][node_id] == "WAITING" and not run_context["waiting_on"][node_id]:
                    await execute_node(node_id)

            async def setup_node_for_execution(node_id, graph_data, activated_by_input):
                # This function now only runs if the node's wait config has NOT been set.
                # For re-triggered nodes, the config is already set by the reset logic in trigger_node.
                if node_id in run_context["node_wait_configs"]:
                    run_context["node_states"][node_id] = "WAITING"
                    # Potentially trigger dependencies if they haven't been resolved,
                    # though in a loop this is less common.
                    return

                node_instance = run_context["nodes"][node_id]
                run_context["node_states"][node_id] = "WAITING"
                await websocket.send_text(f"Preparing: {node_instance.__class__.__name__}")

                node_data = next((n for n in graph_data['nodes'] if str(n['id']) == node_id), None)
                if not node_data or 'inputs' not in node_data: return
                
                initial_wait_list, dependency_tasks = [], []

                for i, input_data in enumerate(node_data['inputs']):
                    target_key = f"{node_id}:{i}"
                    if target_key not in run_context["source_map"]:
                        continue

                    input_name = input_data['name']
                    
                    # Resolve the socket definition, including for dynamic array sockets
                    socket_def = node_instance.INPUT_SOCKETS.get(input_name)
                    if not socket_def:
                        base_name, _, index = input_name.rpartition('_')
                        if base_name and index.isdigit():
                            array_socket_def = node_instance.INPUT_SOCKETS.get(base_name)
                            if array_socket_def and array_socket_def.get('array', False):
                                socket_def = array_socket_def
                    
                    if not socket_def: continue

                    # Check flags: do_not_wait has priority over is_dependency
                    do_not_wait = socket_def.get('do_not_wait', False)
                    is_dependency = socket_def.get('is_dependency', False) and not do_not_wait

                    if not do_not_wait:
                        initial_wait_list.append(input_name)

                    if is_dependency:
                        if activated_by_input and activated_by_input['target_input_name'] == input_name: continue
                        source_info = run_context["source_map"][target_key]
                        source_node_id, _ = source_info.split(':')
                        task = asyncio.create_task(trigger_node(source_node_id))
                        dependency_tasks.append(task)
                        run_context["active_tasks"].add(task)
                
                run_context["node_wait_configs"][node_id] = initial_wait_list
                run_context["waiting_on"][node_id] = list(initial_wait_list)
                print(f"LOG: Node {node_id} is WAITING for: {initial_wait_list}")
                if dependency_tasks: await asyncio.gather(*dependency_tasks)

            async def process_incoming_data(node_id, push_datas):
                for push_data in push_datas:
                    target_input_name = push_data['target_input_name']
                    value = push_data['value']
                    run_context["input_cache"][node_id][target_input_name] = value
                    if target_input_name in run_context["waiting_on"][node_id]:
                        run_context["waiting_on"][node_id].remove(target_input_name)
                print(f"LOG: Node {node_id} waiting for: {run_context['waiting_on'][node_id]}")

            async def execute_node(node_id):
                node_instance = run_context["nodes"][node_id]
                kwargs, temp_cache = {}, run_context["input_cache"][node_id].copy()
                array_inputs = defaultdict(list)
                for input_name, value in temp_cache.items():
                    base_name, _, index = input_name.rpartition('_')
                    if not base_name: base_name = input_name
                    socket_def = node_instance.INPUT_SOCKETS.get(base_name)
                    if socket_def and socket_def.get('array', False) and index.isdigit():
                        array_inputs[base_name].append((int(index), value))
                    else:
                        kwargs[input_name] = value
                for base_name, values in array_inputs.items():
                    values.sort(key=lambda x: x[0])
                    kwargs[base_name] = [v for i, v in values]
                
                run_context["node_states"][node_id] = "EXECUTING"
                await websocket.send_text(f"Executing: {node_instance.__class__.__name__}")
                print(f"LOG: Executing {node_id} with grouped inputs: {kwargs}")

                try:
                    # Check if the execute method is an async function
                    if inspect.iscoroutinefunction(node_instance.execute):
                        result = await node_instance.execute(**kwargs)
                    else:
                        result = node_instance.execute(**kwargs)
                    
                    # Unpack result for potential NodeStateUpdate
                    node_outputs, state_update = (result, None)
                    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], NodeStateUpdate):
                        node_outputs, state_update = result
                        if state_update.wait_for_inputs is not None:
                            run_context["node_wait_configs"][node_id] = state_update.wait_for_inputs
                            print(f"LOG: Node {node_id} updated its wait config to: {state_update.wait_for_inputs}")

                    run_context["node_states"][node_id] = "DONE"
                    run_context["outputs_cache"][node_id] = node_outputs
                    if node_outputs: await push_to_downstream(node_id, node_outputs)
                except Exception as e:
                    error_msg = f"Error in {node_instance.__class__.__name__}: {e}"
                    await websocket.send_text(error_msg)
                    print(f"Execution Error: {error_msg}")
                    import traceback; traceback.print_exc()
                    run_context["node_states"][node_id] = "ERROR"

            async def push_to_downstream(source_node_id, outputs):
                pushes_by_node = defaultdict(list)
                node_instance = run_context["nodes"][source_node_id]
                node_data = next((n for n in graph_data['nodes'] if str(n['id']) == source_node_id), None)
                
                if not node_data:
                    print(f"ERROR: Could not find node data for {source_node_id} during push.")
                    return

                output_socket_defs = list(node_instance.OUTPUT_SOCKETS.items())
                physical_slot_index = 0

                # Ensure outputs is a tuple for consistent processing
                if not isinstance(outputs, tuple):
                    outputs = (outputs,)

                # Iterate through the outputs returned by the node's execute() method
                for logical_index, value in enumerate(outputs):
                    if logical_index >= len(output_socket_defs):
                        break # Should not happen in normal execution

                    socket_name, socket_def = output_socket_defs[logical_index]
                    is_array = socket_def.get('array', False)

                    if is_array:
                        # This output is a dynamic array. The 'value' should be a list.
                        if not isinstance(value, list):
                            print(f"WARNING: Output for array socket '{socket_name}' is not a list. Skipping.")
                            # We still need to account for the outputs that *should* have been there
                            # Count how many frontend slots this array has.
                            num_physical_slots = sum(1 for o in node_data.get('outputs', []) if o['name'].startswith(socket_name + '_'))
                            physical_slot_index += num_physical_slots
                            continue
                        
                        # Iterate through each item in the returned list
                        for item in value:
                            if item is SKIP_OUTPUT:
                                print(f"LOG: Skipping an item in output array {socket_name}")
                            else:
                                source_key = f"{source_node_id}:{physical_slot_index}"
                                for target_key in run_context["target_map"].get(source_key, []):
                                    target_node_id, target_slot_str = target_key.split(':')
                                    target_node_data = next((n for n in graph_data['nodes'] if str(n['id']) == target_node_id), None)
                                    target_input_info = target_node_data['inputs'][int(target_slot_str)]
                                    target_input_name = target_input_info['name']
                                    push_data = {"target_input_name": target_input_name, "value": item}
                                    pushes_by_node[target_node_id].append(push_data)
                            
                            # Move to the next physical slot for the next item in the array
                            physical_slot_index += 1

                    else:
                        # This is a standard, single output
                        if value is not SKIP_OUTPUT:
                            source_key = f"{source_node_id}:{physical_slot_index}"
                            for target_key in run_context["target_map"].get(source_key, []):
                                target_node_id, target_slot_str = target_key.split(':')
                                target_node_data = next((n for n in graph_data['nodes'] if str(n['id']) == target_node_id), None)
                                target_input_info = target_node_data['inputs'][int(target_slot_str)]
                                target_input_name = target_input_info['name']
                                push_data = {"target_input_name": target_input_name, "value": value}
                                pushes_by_node[target_node_id].append(push_data)
                        
                        # Move to the next physical slot for the next standard output
                        physical_slot_index += 1

                # Create a single trigger task for each downstream node
                push_tasks = []
                for target_node_id, push_datas in pushes_by_node.items():
                    task = asyncio.create_task(trigger_node(target_node_id, activated_by_inputs=push_datas))
                    push_tasks.append(task)
                    run_context["active_tasks"].add(task)
                
                if push_tasks: await asyncio.gather(*push_tasks)

            # --- Workflow Kick-off ---
            if start_node_id in nodes_map:
                print(f"--- KICKING OFF WORKFLOW FROM START NODE {start_node_id} ---")
                main_task = asyncio.create_task(trigger_node(start_node_id))
                run_context["active_tasks"].add(main_task)
                while run_context["active_tasks"]:
                    done, pending = await asyncio.wait(run_context["active_tasks"], return_when=asyncio.FIRST_COMPLETED)
                    run_context["active_tasks"] = pending
            else:
                await websocket.send_text(f"Error: Start node {start_node_id} not found.")
                return
            
            await websocket.send_text("Engine: Workflow finished.")
            print("--- WORKFLOW RUN FINISHED ---\n")

        except asyncio.CancelledError:
            print("--- WORKFLOW CANCELLED BY USER ---")
            # Cancel all lingering tasks
            for task in run_context["active_tasks"]:
                task.cancel()
            # Wait for all tasks to acknowledge cancellation
            if run_context["active_tasks"]:
                await asyncio.gather(*run_context["active_tasks"], return_exceptions=True)
            
            await websocket.send_text("Engine: Workflow stopped by user.")
            print("--- WORKFLOW CANCELLATION COMPLETE ---\n")
        
        except Exception as e:
            # Catch any other unexpected errors during the main workflow execution
            print(f"--- UNEXPECTED WORKFLOW ERROR: {e} ---")
            import traceback; traceback.print_exc()
            await websocket.send_text(f"Engine: A critical error occurred: {e}")
            print("--- WORKFLOW TERMINATED DUE TO ERROR ---\n")