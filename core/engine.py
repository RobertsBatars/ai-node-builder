# core/engine.py
# This is the heart of the backend, responsible for discovering, defining, and running nodes.

import inspect
import json
import pkgutil
import importlib

# Import the foundational classes from our framework
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
        This allows for drop-in modularity; just add a new file to add a new node.
        """
        import nodes # The main nodes package
        
        # We scan all modules within the 'nodes' package
        for _, name, _ in pkgutil.walk_packages(nodes.__path__, nodes.__name__ + '.'):
            module = importlib.import_module(name)
            # Find any classes within the module that are subclasses of BaseNode
            for item_name, item in inspect.getmembers(module, inspect.isclass):
                if issubclass(item, BaseNode) and item is not BaseNode:
                    # We found a node. Store it by its class name.
                    self.node_classes[item.__name__] = item
        print(f"Discovered nodes: {list(self.node_classes.keys())}")

    def generate_ui_blueprints(self):
        """
        Scans all discovered node classes and generates a JSON blueprint for the UI.
        This blueprint tells the frontend how to draw each node, its sockets, and its widgets.
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

            # Inspect class attributes to find InputWidget declarations
            for attr_name, attr_value in inspect.getmembers(node_class):
                if isinstance(attr_value, InputWidget):
                    widget_def = {
                        "name": attr_name,
                        "type": attr_value.widget_type,
                        "default": attr_value.default,
                        "properties": attr_value.properties
                    }
                    node_def["widgets"].append(widget_def)
            
            all_node_definitions.append(node_def)
        
        return json.dumps(all_node_definitions, indent=2)

    async def run_workflow(self, graph_data, websocket):
        """
        Executes a workflow graph.
        For now, this is a simplified push-based execution model.
        """
        await websocket.send_text("Engine: Starting workflow execution...")
        print("Received graph for execution.")

        # In a real engine, you would:
        # 1. Validate the graph.
        # 2. Instantiate all nodes from graph_data, passing self (the engine) to their constructor.
        # 3. Call .load() on all instantiated nodes.
        # 4. Determine the execution order (topological sort).
        # 5. Execute each node in order, passing outputs of one node to the inputs of the next.
        
        # Simplified execution for this first step:
        # We will just print the graph data to show it was received.
        print(json.dumps(graph_data, indent=2))

        # Simulate some work
        import asyncio
        for i in range(5):
            await websocket.send_text(f"Engine: Processing step {i+1}...")
            await asyncio.sleep(0.5)

        await websocket.send_text("Engine: Workflow finished.")
        print("Workflow execution finished.")

