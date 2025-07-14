# core/engine.py
# This is the heart of the backend, responsible for discovering, defining, and running nodes.

import inspect
import json
import pkgutil
import importlib
import asyncio

from core.definitions import BaseNode, InputWidget

class NodeEngine:
    """
    Manages node discovery, UI blueprint generation, and workflow execution.
    """
    def __init__(self):
        self.node_classes = {}
        self.discover_nodes()

    def discover_nodes(self):
        """
        Automatically scans the 'nodes' directory to find and load all valid node classes.
        """
        import nodes
        
        for _, name, _ in pkgutil.walk_packages(nodes.__path__, nodes.__name__ + '.'):
            try:
                module = importlib.import_module(name)
                for item_name, item in inspect.getmembers(module, inspect.isclass):
                    if issubclass(item, BaseNode) and item is not BaseNode:
                        self.node_classes[item.__name__] = item
            except Exception as e:
                print(f"Error importing node module {name}: {e}")

        print(f"Discovered nodes: {list(self.node_classes.keys())}")

    def generate_ui_blueprints(self):
        """
        Scans all discovered node classes and generates a JSON blueprint for the UI.
        """
        all_node_definitions = []
        for name, node_class in self.node_classes.items():
            node_def = {
                "name": name,
                "category": node_class.CATEGORY,
                "inputs": [{"name": n, "type": t.value} for n, t in node_class.INPUT_SOCKETS.items()],
                "outputs": [{"name": n, "type": t.value} for n, t in node_class.OUTPUT_SOCKETS.items()],
                "widgets": []
            }
            # Ensure consistent widget order by sorting them
            widget_declarations = sorted(
                [w for w in inspect.getmembers(node_class) if isinstance(w[1], InputWidget)],
                key=lambda x: x[1].order
            )
            for attr_name, attr_value in widget_declarations:
                widget_def = {
                    "name": attr_name,
                    "type": attr_value.widget_type,
                    "default": attr_value.default,
                    "properties": attr_value.properties
                }
                node_def["widgets"].append(widget_def)
            all_node_definitions.append(node_def)
        return json.dumps(all_node_definitions, indent=2)

    async def run_workflow(self, graph_data, start_node_id, websocket):
        """
        Executes a workflow graph using an event-driven, parallel push model.
        """
        await websocket.send_text("Engine: Initializing workflow...")
        
        nodes_map = {}
        for node_info in graph_data['nodes']:
            node_id = str(node_info['id'])
            node_type_name = node_info['type'].split('/')[-1]
            if node_type_name in self.node_classes:
                NodeClass = self.node_classes[node_type_name]
                nodes_map[node_id] = NodeClass(self, node_info)
            else:
                await websocket.send_text(f"Error: Unknown node type '{node_type_name}'")
                return

        for node in nodes_map.values():
            node.load()
        await websocket.send_text("Engine: All nodes loaded.")

        input_data_cache = {node_id: {} for node_id in nodes_map}
        inputs_to_satisfy = {node_id: 0 for node_id in nodes_map}
        for link_info in graph_data['links']:
            target_id = str(link_info[3])
            inputs_to_satisfy[target_id] += 1
        
        execution_tasks = set()

        async def schedule_node_execution(node_id):
            if inputs_to_satisfy[node_id] == len(input_data_cache[node_id]):
                task = asyncio.create_task(execute_node(node_id))
                execution_tasks.add(task)
                task.add_done_callback(execution_tasks.discard)

        async def execute_node(node_id):
            node_instance = nodes_map[node_id]
            await websocket.send_text(f"Executing: {node_instance.__class__.__name__} (ID: {node_id})")
            
            kwargs = input_data_cache[node_id]

            try:
                node_outputs = node_instance.execute(**kwargs)
                if not node_outputs:
                    return

                for i, output_value in enumerate(node_outputs):
                    for link_info in graph_data['links']:
                        if str(link_info[1]) == node_id and link_info[2] == i:
                            target_node_id = str(link_info[3])
                            target_input_slot = link_info[4]
                            target_input_name = nodes_map[target_node_id].get_input_name_by_slot(target_input_slot)
                            
                            input_data_cache[target_node_id][target_input_name] = output_value
                            
                            await schedule_node_execution(target_node_id)
            
            except Exception as e:
                error_msg = f"Error executing {node_instance.__class__.__name__}: {e}"
                await websocket.send_text(error_msg)
                print(error_msg)

        if start_node_id in nodes_map:
            await websocket.send_text(f"Engine: Kicking off from start node {start_node_id}.")
            await schedule_node_execution(start_node_id)
        else:
            await websocket.send_text(f"Error: Start node {start_node_id} not found in graph.")
            return

        while execution_tasks:
            await asyncio.sleep(0.1)

        await websocket.send_text("Engine: Workflow finished.")
