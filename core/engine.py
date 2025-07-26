# core/engine.py
# FINAL REWRITE to be a robust, non-locking, parallel execution engine with verbose logging.

import inspect
import json
import pkgutil
import importlib
import asyncio
from collections import defaultdict
import hashlib
import copy

from core.definitions import BaseNode, EventNode, InputWidget, SKIP_OUTPUT, NodeStateUpdate

class NodeEngine:
    def __init__(self):
        self.node_classes = {}
        self.discover_nodes()
        self._broadcast_callback = None

    def set_broadcast_callback(self, callback):
        self._broadcast_callback = callback

    async def broadcast(self, message):
        if self._broadcast_callback:
            await self._broadcast_callback(copy.deepcopy(message))

    def discover_nodes(self):
        import nodes
        for _, name, _ in pkgutil.walk_packages(nodes.__path__, nodes.__name__ + '.'):
            try:
                module = importlib.import_module(name)
                for _, item in inspect.getmembers(module, inspect.isclass):
                    if issubclass(item, BaseNode) and item is not BaseNode and item is not EventNode:
                        self.node_classes[item.__name__] = item
            except Exception as e:
                print(f"Error importing node module {name}: {e}")
        print(f"Discovered nodes: {list(self.node_classes.keys())}")

    def _generate_graph_hash(self, graph_data):
        # Create a simplified, position-independent representation of the graph for hashing.
        structural_info = {
            "nodes": sorted([{"id": n["id"], "type": n["type"]} for n in graph_data["nodes"]], key=lambda x: x["id"]),
            "links": sorted([link[1:] for link in graph_data["links"]])
        }
        structural_json = json.dumps(structural_info, sort_keys=True)
        return hashlib.sha256(structural_json.encode()).hexdigest()

    def generate_ui_blueprints(self):
        all_node_definitions = []
        for name, node_class in self.node_classes.items():
            inputs_def = [{"name": n, **s} for n, s in node_class.INPUT_SOCKETS.items()]
            outputs_def = [{"name": n, **s} for n, s in node_class.OUTPUT_SOCKETS.items()]
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

    async def run_workflow(self, graph_data, start_node_id, websocket, run_id, global_state, initial_payload=None):
        current_hash = self._generate_graph_hash(graph_data)
        global_state["graph_hash"] = current_hash

        # --- Workflow Change Warning Logic ---
        is_context_populated = bool(global_state.get("display_context"))
        initial_hash = global_state.get("initial_graph_hash")

        # Set the initial hash when the context first becomes populated
        # We store the hash from the PREVIOUS run, not the current one
        if is_context_populated and not initial_hash:
            # Check if we have a previous hash stored
            previous_hash = global_state.get("previous_graph_hash")
            if previous_hash:
                global_state['initial_graph_hash'] = previous_hash
                initial_hash = previous_hash
        
        # Store current hash as previous for next run
        global_state["previous_graph_hash"] = current_hash
        
        # If the context is populated and we have an initial hash, compare it with current hash
        if is_context_populated and initial_hash and current_hash != initial_hash:
            warning_msg = {
                "node_id": None,
                "node_title": "Engine Warning",
                "content_type": "warning",
                "data": "Workflow has changed since the context was started. Node filtering may be unreliable."
            }
            global_state['display_context'].append(warning_msg)
            await self.broadcast({
                "source": "node",
                "type": "display",
                "payload": {"data": warning_msg}
            })
        
        node_id_to_name = {
            str(node['id']): node.get('title', node['type'].split('/')[-1]) 
            for node in graph_data['nodes']
        }
        
        async def send_engine_log(message, node_id=None):
            log_message = {
                "type": "engine_log",
                "run_id": run_id,
                "message": message
            }
            if node_id:
                log_message["node_id"] = node_id
                log_message["node_name"] = node_id_to_name.get(node_id, "Unknown Node")
            await websocket.send_text(json.dumps(log_message))

        await send_engine_log("Engine: Initializing workflow...")
        print(f"\n--- NEW WORKFLOW RUN (ID: {run_id}) ---")
        
        # Send the current graph hash to the frontend
        await self.broadcast({
            "type": "graph_hash_updated",
            "payload": {"graph_hash": current_hash}
        })

        # 1. --- Initialization ---
        node_memory = defaultdict(dict)
        nodes_map = {
            str(n['id']): self.node_classes[n['type'].split('/')[-1]](self, n, node_memory[str(n['id'])], run_id, global_state)
            for n in graph_data['nodes'] if n['type'].split('/')[-1] in self.node_classes
        }

        # Inject the websocket context into each node instance for this run.
        for node in nodes_map.values():
            node._websocket = websocket

        for node_id, node in nodes_map.items():
            node.load()
            node_name = node_id_to_name.get(node_id, "Unknown Node")
            await send_engine_log(f"Engine: Node '{node_name}' loaded.", node_id)
        await send_engine_log("Engine: All nodes loaded.")

        # Inject the initial payload into the start node's memory if provided.
        if initial_payload is not None and start_node_id in node_memory:
            node_memory[start_node_id]['initial_payload'] = initial_payload
            print(f"LOG: Injected initial payload into memory for start node {start_node_id}.")

        # 2. --- Context Setup ---
        run_context = {
            "run_id": run_id,
            "nodes": nodes_map, "websocket": websocket,
            "node_states": defaultdict(lambda: "PENDING"),
            "input_cache": defaultdict(dict), "input_cache_run_ids": defaultdict(dict), "waiting_on": defaultdict(list),
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
                    node_name = node_id_to_name.get(node_id, "Unknown Node")
                    
                    print(f"LOG: Resetting completed node {node_id} ({node_name}) for re-trigger.")
                    run_context["node_states"][node_id] = "PENDING"
                    node_state = "PENDING"
                    
                    # Use the (potentially dynamic) wait config for the reset
                    wait_config = run_context["node_wait_configs"][node_id]
                    
                    # Only wait for inputs that aren't already cached from the same run
                    cache = run_context["input_cache"][node_id]
                    cache_run_ids = run_context["input_cache_run_ids"][node_id]
                    current_run_id = run_context["run_id"]
                    input_sockets = run_context["nodes"][node_id].INPUT_SOCKETS
                    waiting_for = []
                    
                    for input_name in wait_config:
                        socket_def = input_sockets.get(input_name, {})
                        is_dependency = socket_def.get("is_dependency", False)
                        
                        # If it's a dependency and cached from the same run, don't wait for it
                        if is_dependency and input_name in cache and cache_run_ids.get(input_name) == current_run_id:
                            continue
                        else:
                            waiting_for.append(input_name)
                    
                    run_context["waiting_on"][node_id] = waiting_for

                    # Clear only non-dependency inputs that the node is now waiting for.
                    # Also clear dependencies from different runs.
                    keys_to_delete = []
                    for key in cache:
                        if key in wait_config:
                            socket_def = input_sockets.get(key, {})
                            is_dependency = socket_def.get("is_dependency", False)
                            # Clear non-dependencies or dependencies from different runs
                            if not is_dependency or cache_run_ids.get(key) != current_run_id:
                                keys_to_delete.append(key)
                    
                    for key in keys_to_delete:
                        del cache[key]
                        if key in cache_run_ids:
                            del cache_run_ids[key]
                    
                    print(f"LOG: Cleared waiting inputs for {node_id} ({node_name}). Waiting for: {run_context['waiting_on'][node_id]}")


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
                node_name = node_id_to_name.get(node_id, "Unknown Node")
                run_context["node_states"][node_id] = "WAITING"
                await send_engine_log(f"Preparing: {node_name} ({node_instance.__class__.__name__})", node_id)

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
                print(f"LOG: Node {node_id} ({node_name}) is WAITING for: {initial_wait_list}")
                if dependency_tasks: await asyncio.gather(*dependency_tasks)

            async def process_incoming_data(node_id, push_datas):
                node_name = node_id_to_name.get(node_id, "Unknown Node")
                for push_data in push_datas:
                    target_input_name = push_data['target_input_name']
                    value = push_data['value']
                    run_context["input_cache"][node_id][target_input_name] = value
                    run_context["input_cache_run_ids"][node_id][target_input_name] = run_context["run_id"]
                    if target_input_name in run_context["waiting_on"][node_id]:
                        run_context["waiting_on"][node_id].remove(target_input_name)
                print(f"LOG: Node {node_id} ({node_name}) waiting for: {run_context['waiting_on'][node_id]}")

            async def execute_node(node_id):
                node_instance = run_context["nodes"][node_id]
                node_name = node_id_to_name.get(node_id, "Unknown Node")
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
                await send_engine_log(f"Executing: {node_name} ({node_instance.__class__.__name__})", node_id)
                print(f"LOG: Executing {node_id} ({node_name}) with grouped inputs: {kwargs}")

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
                            print(f"LOG: Node {node_id} ({node_name}) updated its wait config to: {state_update.wait_for_inputs}")

                    run_context["node_states"][node_id] = "DONE"
                    run_context["outputs_cache"][node_id] = node_outputs
                    if node_outputs: await push_to_downstream(node_id, node_outputs)
                except Exception as e:
                    error_msg = f"Error in {node_name} ({node_instance.__class__.__name__}): {e}"
                    await send_engine_log(error_msg, node_id)
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
                print(f"--- KICKING OFF WORKFLOW FROM START NODE {start_node_id} (ID: {run_id}) ---")
                main_task = asyncio.create_task(trigger_node(start_node_id))
                run_context["active_tasks"].add(main_task)
                while run_context["active_tasks"]:
                    done, pending = await asyncio.wait(run_context["active_tasks"], return_when=asyncio.FIRST_COMPLETED)
                    run_context["active_tasks"] = pending
            else:
                await send_engine_log(f"Error: Start node {start_node_id} not found.")
                return
            
            await send_engine_log("Engine: Workflow finished.")
            print(f"--- WORKFLOW RUN FINISHED (ID: {run_id}) ---\n")

        except asyncio.CancelledError:
            print(f"--- WORKFLOW CANCELLED BY USER (ID: {run_id}) ---")
            # Cancel all lingering tasks
            for task in run_context["active_tasks"]:
                task.cancel()
            # Wait for all tasks to acknowledge cancellation
            if run_context["active_tasks"]:
                await asyncio.gather(*run_context["active_tasks"], return_exceptions=True)
            
            await send_engine_log("Engine: Workflow stopped by user.")
            print(f"--- WORKFLOW CANCELLATION COMPLETE (ID: {run_id}) ---\n")
        
        except Exception as e:
            # Catch any other unexpected errors during the main workflow execution
            print(f"--- UNEXPECTED WORKFLOW ERROR (ID: {run_id}): {e} ---")
            import traceback; traceback.print_exc()
            await send_engine_log(f"Engine: A critical error occurred: {e}")
            print(f"--- WORKFLOW TERMINATED DUE TO ERROR (ID: {run_id}) ---\n")