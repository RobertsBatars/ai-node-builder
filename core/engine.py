# core/engine.py
# REWRITTEN AGAIN to be a robust, non-locking, parallel execution engine with verbose logging.

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
            node_def = {
                "name": name, "category": node_class.CATEGORY,
                "inputs": [{"name": n, "type": s["type"].value} for n, s in node_class.INPUT_SOCKETS.items()],
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
        
        nodes_map = {
            str(n['id']): self.node_classes[n['type'].split('/')[-1]](self, n)
            for n in graph_data['nodes'] if n['type'].split('/')[-1] in self.node_classes
        }

        for node in nodes_map.values():
            node.load()
        await websocket.send_text("Engine: All nodes loaded.")

        # --- State for this specific run ---
        outputs_cache = {}
        active_tasks = {}
        
        # Build maps for easy link lookups
        source_for_target_input = {}
        targets_for_source_output = defaultdict(list)
        for link in graph_data['links']:
            link_id, source_id, source_slot, target_id, target_slot, link_type = link
            source_id, target_id = str(source_id), str(target_id)
            source_for_target_input[f"{target_id}:{target_slot}"] = f"{source_id}:{source_slot}"
            targets_for_source_output[f"{source_id}:{source_slot}"].append(f"{target_id}:{target_slot}")

        # --- NEW: State for managing data flow and readiness ---
        input_data_cache = defaultdict(dict)
        # Count how many non-dependency inputs each node is waiting for
        inputs_to_satisfy = defaultdict(int)
        for node_id, node_instance in nodes_map.items():
            for i, (name, socket_def) in enumerate(node_instance.INPUT_SOCKETS.items()):
                if not socket_def.get("is_dependency", False):
                    if f"{node_id}:{i}" in source_for_target_input:
                        inputs_to_satisfy[node_id] += 1

        async def process_node(node_id):
            """Main recursive execution function. Ensures a node is only run once."""
            if node_id in outputs_cache:
                print(f"LOG: Cache hit for node {node_id}.")
                return outputs_cache[node_id]
            if node_id in active_tasks:
                print(f"LOG: Awaiting existing task for node {node_id}.")
                return await active_tasks[node_id]

            task = asyncio.create_task(_resolve_and_execute(node_id))
            active_tasks[node_id] = task
            
            try:
                result = await task
                outputs_cache[node_id] = result
                return result
            finally:
                if node_id in active_tasks:
                    del active_tasks[node_id]

        async def _resolve_and_execute(node_id):
            node_instance = nodes_map[node_id]
            await websocket.send_text(f"Resolving: {node_instance.__class__.__name__} (ID: {node_id})")
            print(f"LOG: Preparing to execute node {node_id} ({node_instance.__class__.__name__})")
            
            kwargs = input_data_cache[node_id].copy()
            dependency_tasks = []
            
            for i, (name, socket_def) in enumerate(node_instance.INPUT_SOCKETS.items()):
                if socket_def.get("is_dependency", False):
                    source_info = source_for_target_input.get(f"{node_id}:{i}")
                    if source_info:
                        source_node_id, _ = source_info.split(':')
                        print(f"LOG: Node {node_id} has dependency '{name}'. Pulling from {source_node_id}.")
                        dependency_tasks.append(process_node(source_node_id))

            if dependency_tasks:
                await asyncio.gather(*dependency_tasks)

            # Now populate kwargs with all inputs (pushed and pulled)
            for i, (name, socket_def) in enumerate(node_instance.INPUT_SOCKETS.items()):
                if name not in kwargs:
                    source_info = source_for_target_input.get(f"{node_id}:{i}")
                    if source_info:
                        source_node_id, source_slot_str = source_info.split(':')
                        source_slot_idx = int(source_slot_str)
                        if source_node_id in outputs_cache and outputs_cache[source_node_id] is not None:
                            kwargs[name] = outputs_cache[source_node_id][source_slot_idx]

            await websocket.send_text(f"Executing: {node_instance.__class__.__name__} (ID: {node_id})")
            print(f"LOG: All inputs for {node_id} resolved. Calling execute() with args: {kwargs}")
            try:
                node_outputs = node_instance.execute(**kwargs)
                print(f"LOG: Node {node_id} executed. Outputs: {node_outputs}")
                
                if node_outputs:
                    downstream_tasks = []
                    for i, output_value in enumerate(node_outputs):
                        for target_info in targets_for_source_output.get(f"{node_id}:{i}", []):
                            target_node_id, target_slot_str = target_info.split(':')
                            target_node = nodes_map[target_node_id]
                            target_input_name = target_node.get_input_name_by_slot(int(target_slot_str))
                            
                            # Cache the pushed data
                            input_data_cache[target_node_id][target_input_name] = output_value
                            print(f"LOG: Pushing data to {target_node_id}. Cached input '{target_input_name}'.")

                            # Check if the target node is now ready to run
                            if len(input_data_cache[target_node_id]) == inputs_to_satisfy[target_node_id]:
                                print(f"LOG: Node {target_node_id} is now ready to execute.")
                                downstream_tasks.append(process_node(target_node_id))
                    if downstream_tasks:
                        await asyncio.gather(*downstream_tasks)
                
                return node_outputs
            except Exception as e:
                error_msg = f"Error executing {node_instance.__class__.__name__}: {e}"
                await websocket.send_text(error_msg)
                print(f"Execution Error: {error_msg}")
                import traceback
                traceback.print_exc()
                return None

        if start_node_id in nodes_map:
            await process_node(start_node_id)
        else:
            await websocket.send_text(f"Error: Start node {start_node_id} not found.")
            return

        await websocket.send_text("Engine: Workflow finished.")
        print("--- WORKFLOW RUN FINISHED ---\n")
