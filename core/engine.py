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
        
        source_for_target_input = {}
        targets_for_source_output = defaultdict(list)
        for link in graph_data['links']:
            link_id, source_id, source_slot, target_id, target_slot, link_type = link
            source_id, target_id = str(source_id), str(target_id)
            source_for_target_input[f"{target_id}:{target_slot}"] = f"{source_id}:{source_slot}"
            targets_for_source_output[f"{source_id}:{source_slot}"].append(f"{target_id}:{target_slot}")

        async def execute_node(node_id):
            """Main recursive execution function. Ensures a node is only run once."""
            if node_id in outputs_cache:
                print(f"LOG: Cache hit for node {node_id}.")
                return outputs_cache[node_id]
            
            if node_id in active_tasks:
                print(f"LOG: Awaiting existing task for node {node_id}.")
                return await active_tasks[node_id]

            # Create and store the task *before* awaiting it to prevent re-runs in parallel branches
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
            
            kwargs = {}
            dependency_tasks = []
            
            for i, (name, socket_def) in enumerate(node_instance.INPUT_SOCKETS.items()):
                source_info = source_for_target_input.get(f"{node_id}:{i}")
                if source_info:
                    source_node_id, source_slot_str = source_info.split(':')
                    print(f"LOG: Node {node_id} needs input '{name}'. Getting from {source_node_id}.")
                    dependency_tasks.append(
                        resolve_dependency(source_node_id, int(source_slot_str), name)
                    )

            if dependency_tasks:
                dependency_results = await asyncio.gather(*dependency_tasks)
                for dep_result in dependency_results:
                    kwargs.update(dep_result)
            
            await websocket.send_text(f"Executing: {node_instance.__class__.__name__} (ID: {node_id})")
            print(f"LOG: All inputs for {node_id} resolved. Calling execute() with args: {kwargs}")
            try:
                node_outputs = node_instance.execute(**kwargs)
                print(f"LOG: Node {node_id} executed. Outputs: {node_outputs}")
                
                # --- Push Phase ---
                if node_outputs:
                    downstream_tasks = []
                    for i, output_value in enumerate(node_outputs):
                        for target_info in targets_for_source_output.get(f"{node_id}:{i}", []):
                            target_node_id, _ = target_info.split(':')
                            print(f"LOG: Pushing output from {node_id} to {target_node_id}.")
                            # This creates a new, independent task for the downstream node.
                            # The current task does NOT wait for it, preventing deadlock.
                            downstream_tasks.append(asyncio.create_task(execute_node(target_node_id)))
                    if downstream_tasks:
                        # This was the source of the deadlock. We should not wait here.
                        # The main loop will handle waiting for all tasks to complete.
                        # await asyncio.gather(*downstream_tasks)
                        pass
                
                return node_outputs
            except Exception as e:
                error_msg = f"Error executing {node_instance.__class__.__name__}: {e}"
                await websocket.send_text(error_msg)
                print(f"Execution Error: {error_msg}")
                import traceback
                traceback.print_exc()
                return None

        async def resolve_dependency(source_node_id, source_slot_idx, kwarg_name):
            """Helper to resolve a single dependency and return it as a dict."""
            source_outputs = await execute_node(source_node_id)
            if source_outputs and len(source_outputs) > source_slot_idx:
                return {kwarg_name: source_outputs[source_slot_idx]}
            return {kwarg_name: None}

        # --- Kick off the workflow ---
        if start_node_id in nodes_map:
            # We create the main task but don't need to await it here,
            # as the recursive calls will handle the entire chain.
            main_task = asyncio.create_task(execute_node(start_node_id))
            # FIX: Wait for the main task and any spawned tasks to complete.
            while True:
                if not active_tasks:
                    break
                await asyncio.sleep(0.01)
        else:
            await websocket.send_text(f"Error: Start node {start_node_id} not found.")
            return

        await websocket.send_text("Engine: Workflow finished.")
        print("--- WORKFLOW RUN FINISHED ---\n")
