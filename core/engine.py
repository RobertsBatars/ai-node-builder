# core/engine.py
# FINAL REWRITE to be a robust, non-locking, parallel execution engine with verbose logging.

import inspect
import json
import pkgutil
import importlib
import asyncio
from collections import defaultdict

from core.definitions import BaseNode, InputWidget

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
            # Convert enums to string values for JSON serialization
            for input_def in inputs_def:
                if 'type' in input_def and hasattr(input_def['type'], 'value'):
                    input_def['type'] = input_def['type'].value

            node_def = {
                "name": name, "category": node_class.CATEGORY,
                "inputs": inputs_def,
                "outputs": [{"name": n, "type": s["type"].value} for n, s in node_class.OUTPUT_SOCKETS.items()],
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
        nodes_map = {
            str(n['id']): self.node_classes[n['type'].split('/')[-1]](self, n)
            for n in graph_data['nodes'] if n['type'].split('/')[-1] in self.node_classes
        }
        for node in nodes_map.values():
            node.load()
        await websocket.send_text("Engine: All nodes loaded.")

        # 2. --- Context Setup ---
        run_context = {
            "nodes": nodes_map, "websocket": websocket,
            "node_states": defaultdict(lambda: "PENDING"),
            "input_cache": defaultdict(dict), "waiting_on": defaultdict(list),
            "outputs_cache": {}, "active_tasks": set(),
            "source_map": {}, "target_map": defaultdict(list)
        }
        for link_data in graph_data['links']:
            _, source_id, source_slot, target_id, target_slot, _ = link_data
            source_id, target_id = str(source_id), str(target_id)
            source_key = f"{source_id}:{source_slot}"
            target_key = f"{target_id}:{target_slot}"
            run_context["source_map"][target_key] = source_key
            run_context["target_map"][source_key].append(target_key)

        # 3. --- Core Execution Logic ---
        async def trigger_node(node_id, activated_by_input=None):
            node_state = run_context["node_states"][node_id]
            if node_state in ["EXECUTING", "DONE"]:
                return

            if node_state == "PENDING":
                await setup_node_for_execution(node_id, graph_data, activated_by_input)
            
            if activated_by_input:
                await process_incoming_data(node_id, activated_by_input)

            if run_context["node_states"][node_id] == "WAITING" and not run_context["waiting_on"][node_id]:
                await execute_node(node_id)

        async def setup_node_for_execution(node_id, graph_data, activated_by_input):
            node_instance = run_context["nodes"][node_id]
            run_context["node_states"][node_id] = "WAITING"
            await websocket.send_text(f"Preparing: {node_instance.__class__.__name__}")

            # Get the node's data from the graph to inspect its actual inputs
            node_data = next((n for n in graph_data['nodes'] if str(n['id']) == node_id), None)
            if not node_data or 'inputs' not in node_data:
                return

            waiting_list = []
            dependency_tasks = []

            # Map slot index to input name from the node's actual data in the graph
            slot_to_name_map = {i: inp['name'] for i, inp in enumerate(node_data.get('inputs', []))}

            for i, input_data in enumerate(node_data['inputs']):
                target_key = f"{node_id}:{i}"
                if target_key in run_context["source_map"]:
                    input_name = input_data['name']
                    waiting_list.append(input_name)

                    # Determine if this input is a dependency
                    base_name, _, _ = input_name.rpartition('_')
                    # Handle cases where there is no underscore in the name
                    if not base_name:
                        base_name = input_name
                    
                    socket_def = node_instance.INPUT_SOCKETS.get(base_name)
                    is_dependency = socket_def and socket_def.get('is_dependency', False)

                    if is_dependency:
                        if activated_by_input and activated_by_input['target_input_name'] == input_name:
                            continue
                        
                        source_info = run_context["source_map"][target_key]
                        source_node_id, _ = source_info.split(':')
                        task = asyncio.create_task(trigger_node(source_node_id))
                        dependency_tasks.append(task)
                        run_context["active_tasks"].add(task)
            
            run_context["waiting_on"][node_id] = waiting_list
            print(f"LOG: Node {node_id} is WAITING for: {waiting_list}")
            if dependency_tasks:
                await asyncio.gather(*dependency_tasks)

        async def process_incoming_data(node_id, push_data):
            target_input_name = push_data['target_input_name']
            value = push_data['value']
            
            run_context["input_cache"][node_id][target_input_name] = value
            if target_input_name in run_context["waiting_on"][node_id]:
                run_context["waiting_on"][node_id].remove(target_input_name)
            
            print(f"LOG: Node {node_id} waiting for: {run_context['waiting_on'][node_id]}")

        async def execute_node(node_id):
            node_instance = run_context["nodes"][node_id]
            
            # --- Start Array Input Grouping ---
            kwargs = {}
            temp_cache = run_context["input_cache"][node_id].copy()
            
            array_inputs = defaultdict(list)
            # First, identify all array inputs and group them
            for input_name, value in temp_cache.items():
                base_name, _, index = input_name.rpartition('_')
                
                # Handle cases where there is no underscore in the name
                if not base_name:
                    base_name = input_name

                socket_def = node_instance.INPUT_SOCKETS.get(base_name)
                if socket_def and socket_def.get('array', False) and index.isdigit():
                    array_inputs[base_name].append((int(index), value))
                else:
                    kwargs[input_name] = value # It's a regular input

            # Sort the array inputs by index and add them to kwargs
            for base_name, values in array_inputs.items():
                values.sort(key=lambda x: x[0]) # Sort by index
                kwargs[base_name] = [v for i, v in values] # Store just the values in order
            # --- End Array Input Grouping ---

            run_context["node_states"][node_id] = "EXECUTING"
            await websocket.send_text(f"Executing: {node_instance.__class__.__name__}")
            print(f"LOG: Executing {node_id} with grouped inputs: {kwargs}")

            try:
                node_outputs = node_instance.execute(**kwargs)
                run_context["node_states"][node_id] = "DONE"
                run_context["outputs_cache"][node_id] = node_outputs
                if node_outputs:
                    await push_to_downstream(node_id, node_outputs)
            except Exception as e:
                error_msg = f"Error in {node_instance.__class__.__name__}: {e}"
                await websocket.send_text(error_msg)
                print(f"Execution Error: {error_msg}")
                import traceback; traceback.print_exc()
                run_context["node_states"][node_id] = "ERROR"

        async def push_to_downstream(source_node_id, outputs):
            push_tasks = []
            for i, value in enumerate(outputs):
                source_key = f"{source_node_id}:{i}"
                for target_key in run_context["target_map"].get(source_key, []):
                    target_node_id, target_slot_str = target_key.split(':')
                    target_node = run_context["nodes"][target_node_id]
                    
                    # Find the actual input name from the graph data
                    target_node_data = next((n for n in graph_data['nodes'] if str(n['id']) == target_node_id), None)
                    target_input_info = target_node_data['inputs'][int(target_slot_str)]
                    target_input_name = target_input_info['name']

                    push_data = {"target_input_name": target_input_name, "value": value}
                    task = asyncio.create_task(trigger_node(target_node_id, activated_by_input=push_data))
                    push_tasks.append(task)
                    run_context["active_tasks"].add(task)
            if push_tasks:
                await asyncio.gather(*push_tasks)

        # 4. --- Workflow Kick-off ---
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