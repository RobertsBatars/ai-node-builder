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

        # 1. --- Initialization ---
        nodes_map = {
            str(n['id']): self.node_classes[n['type'].split('/')[-1]](self, n)
            for n in graph_data['nodes'] if n['type'].split('/')[-1] in self.node_classes
        }
        for node in nodes_map.values():
            node.load()
        await websocket.send_text("Engine: All nodes loaded.")

        # 2. --- Context Setup ---
        # This context will hold the state for the entire workflow run
        run_context = {
            "nodes": nodes_map,
            "websocket": websocket,
            "node_states": defaultdict(lambda: "PENDING"), # PENDING, WAITING, EXECUTING, DONE
            "input_cache": defaultdict(dict), # Cache for incoming data
            "waiting_on": defaultdict(list), # List of inputs a node is waiting for
            "outputs_cache": {}, # Cache for node results
            "active_tasks": set(), # To track all running asyncio tasks
            "source_map": {}, # { "target_id:slot": "source_id:slot" }
            "target_map": defaultdict(list) # { "source_id:slot": ["target_id:slot", ...] }
        }
        for link in graph_data['links']:
            _, source_id, source_slot, target_id, target_slot, _ = link
            source_id, target_id = str(source_id), str(target_id)
            run_context["source_map"][f"{target_id}:{target_slot}"] = f"{source_id}:{source_slot}"
            run_context["target_map"][f"{source_id}:{source_slot}"].append(f"{target_id}:{target_slot}")

        # 3. --- Core Execution Logic ---
        async def trigger_node(node_id, activated_by_input=None):
            """The main entry point for processing a node."""
            node_state = run_context["node_states"][node_id]
            if node_state in ["EXECUTING", "DONE"]:
                print(f"LOG: Node {node_id} is already {node_state}. Skipping.")
                return

            node_instance = run_context["nodes"][node_id]
            print(f"LOG: Triggering node {node_id} ({node_instance.__class__.__name__}). Current state: {node_state}")

            # If this is the first time we're seeing this node, set it up.
            if node_state == "PENDING":
                await setup_node_for_execution(node_id, activated_by_input)
            
            # If the node was activated by an input, process that data.
            if activated_by_input:
                await process_incoming_data(node_id, activated_by_input)

            # Check if the node is now ready to execute.
            if run_context["node_states"][node_id] == "WAITING" and not run_context["waiting_on"][node_id]:
                await execute_node(node_id)

        async def setup_node_for_execution(node_id, activated_by_input):
            """Identifies dependencies and prepares a node to receive inputs."""
            node_instance = run_context["nodes"][node_id]
            run_context["node_states"][node_id] = "WAITING"
            await websocket.send_text(f"Preparing: {node_instance.__class__.__name__}")
            
            connected_inputs = []
            dependency_tasks = []

            for i, (name, socket_def) in enumerate(node_instance.INPUT_SOCKETS.items()):
                if f"{node_id}:{i}" in run_context["source_map"]:
                    connected_inputs.append(name)
                    
                    # If this input is a dependency, we need to pull it.
                    if socket_def.get("is_dependency", False):
                        # CRITICAL: Don't pull if this is the input that just activated us.
                        if activated_by_input and activated_by_input['target_input_name'] == name:
                            print(f"LOG: Node {node_id} was activated by dependency '{name}', not pulling.")
                            continue
                        
                        source_info = run_context["source_map"][f"{node_id}:{i}"]
                        source_node_id, _ = source_info.split(':')
                        print(f"LOG: Node {node_id} requires dependency '{name}' from {source_node_id}. Triggering pull.")
                        task = asyncio.create_task(trigger_node(source_node_id))
                        dependency_tasks.append(task)
                        run_context["active_tasks"].add(task)

            # A node is waiting for all its connected inputs.
            run_context["waiting_on"][node_id] = connected_inputs
            print(f"LOG: Node {node_id} is now WAITING for inputs: {connected_inputs}")

            if dependency_tasks:
                await asyncio.gather(*dependency_tasks)

        async def process_incoming_data(node_id, push_data):
            """Caches incoming data and checks if the node is ready to run."""
            target_input_name = push_data['target_input_name']
            value = push_data['value']
            
            print(f"LOG: Node {node_id} received data for input '{target_input_name}'.")
            run_context["input_cache"][node_id][target_input_name] = value
            
            # Remove the input from the waiting list.
            if target_input_name in run_context["waiting_on"][node_id]:
                run_context["waiting_on"][node_id].remove(target_input_name)
            
            print(f"LOG: Node {node_id} is now waiting for: {run_context['waiting_on'][node_id]}")

        async def execute_node(node_id):
            """Executes the node's logic and pushes results to downstream nodes."""
            node_instance = run_context["nodes"][node_id]
            kwargs = run_context["input_cache"][node_id]

            run_context["node_states"][node_id] = "EXECUTING"
            await websocket.send_text(f"Executing: {node_instance.__class__.__name__}")
            print(f"LOG: All inputs for {node_id} resolved. Executing with: {kwargs}")

            try:
                node_outputs = node_instance.execute(**kwargs)
                run_context["node_states"][node_id] = "DONE"
                run_context["outputs_cache"][node_id] = node_outputs
                print(f"LOG: Node {node_id} executed. Outputs: {node_outputs}")

                if node_outputs:
                    await push_to_downstream(node_id, node_outputs)
            except Exception as e:
                error_msg = f"Error executing {node_instance.__class__.__name__}: {e}"
                await websocket.send_text(error_msg)
                print(f"Execution Error: {error_msg}")
                import traceback
                traceback.print_exc()
                run_context["node_states"][node_id] = "ERROR"

        async def push_to_downstream(source_node_id, outputs):
            """Pushes output data to all connected downstream nodes."""
            push_tasks = []
            for i, value in enumerate(outputs):
                source_slot_key = f"{source_node_id}:{i}"
                for target_info in run_context["target_map"].get(source_slot_key, []):
                    target_node_id, target_slot_str = target_info.split(':')
                    target_node = run_context["nodes"][target_node_id]
                    target_input_name = target_node.get_input_name_by_slot(int(target_slot_str))
                    
                    print(f"LOG: Pushing data from {source_node_id} to {target_node_id} ('{target_input_name}').")
                    
                    push_data = {
                        "target_input_name": target_input_name,
                        "value": value
                    }
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

            # Wait for all tasks to complete.
            while run_context["active_tasks"]:
                done, pending = await asyncio.wait(run_context["active_tasks"], return_when=asyncio.FIRST_COMPLETED)
                run_context["active_tasks"] = pending
        else:
            await websocket.send_text(f"Error: Start node {start_node_id} not found.")
            return

        await websocket.send_text("Engine: Workflow finished.")
        print("--- WORKFLOW RUN FINISHED ---\n")
