# nodes/simple_nodes.py
# Updated nodes to use the new socket definition format.
from core.definitions import BaseNode, SocketType, InputWidget

# --- INPUT NODES ---

class TextNode(BaseNode):
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"text_out": {"type": SocketType.TEXT}}
    
    value = InputWidget(widget_type="TEXT", default="Hello from backend!")

    def load(self):
        pass

    def execute(self):
        text_value = self.widget_values.get('value', self.value.default)
        return (text_value,)

class NumberNode(BaseNode):
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"number_out": {"type": SocketType.NUMBER}}

    value = InputWidget(widget_type="NUMBER", default=10)

    def load(self):
        pass

    def execute(self):
        num_value = self.widget_values.get('value', self.value.default)
        return (float(num_value),)

# --- PROCESSING NODE ---

class AddNode(BaseNode):
    CATEGORY = "Math"
    # FIX: Sockets are now defined with properties. 'is_dependency' tells the engine to pull them.
    # The data type is NUMBER, so the frontend allows the connection.
    INPUT_SOCKETS = {
        "a": {"type": SocketType.NUMBER, "is_dependency": True},
        "b": {"type": SocketType.NUMBER, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {"result": {"type": SocketType.NUMBER}}

    def load(self):
        pass

    def execute(self, a, b):
        # This node's logic is driven by its inputs, which are now pulled by the engine.
        result = float(a) + float(b)
        return (result,)

# --- OUTPUT NODE ---

class DisplayNode(BaseNode):
    CATEGORY = "Output"
    # This is a standard "push" input.
    INPUT_SOCKETS = {"value_in": {"type": SocketType.ANY}}

    def load(self):
        pass

    def execute(self, value_in=None):
        print(f"--- DISPLAY NODE RECEIVED: {value_in} ---")
        return ()
