# nodes/simple_nodes.py
# A collection of basic nodes to test the core functionality.

from core.definitions import BaseNode, SocketType, InputWidget

# --- INPUT NODES ---

class TextNode(BaseNode):
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"text_out": SocketType.TEXT}
    
    value = InputWidget(widget_type="TEXT", default="Hello, World!")

    def load(self):
        pass # Nothing to load

    def execute(self):
        # In a real implementation, the engine would pass widget values.
        # For now, we just return the default.
        return (self.value.default,)

class NumberNode(BaseNode):
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"number_out": SocketType.NUMBER}

    value = InputWidget(widget_type="NUMBER", default=10)

    def load(self):
        pass

    def execute(self):
        return (self.value.default,)


# --- PROCESSING NODE ---

class AddNode(BaseNode):
    CATEGORY = "Math"
    INPUT_SOCKETS = {"a": SocketType.NUMBER, "b": SocketType.NUMBER}
    OUTPUT_SOCKETS = {"result": SocketType.NUMBER}

    def load(self):
        pass

    def execute(self, a, b):
        # The engine will pass the values from connected nodes as arguments.
        result = a + b
        return (result,)


# --- OUTPUT NODE ---

class DisplayNode(BaseNode):
    CATEGORY = "Output"
    INPUT_SOCKETS = {"value_in": SocketType.ANY}

    def load(self):
        pass

    def execute(self, value_in):
        # This node just prints the value it receives to the backend console.
        print(f"--- DISPLAY NODE: {value_in} ---")
        return () # No output
