# nodes/simple_nodes.py
# Updated nodes that correctly use widget values and passed arguments.
import inspect
from core.definitions import BaseNode, SocketType, InputWidget

# --- INPUT NODES ---

class TextNode(BaseNode):
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"text_out": SocketType.TEXT}
    
    value = InputWidget(widget_type="TEXT", default="Hello from backend!")

    def load(self):
        pass

    def execute(self):
        # This node has no inputs, so it uses its widget value.
        text_value = self.widget_values.get('value', self.value.default)
        return (text_value,)

class NumberNode(BaseNode):
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"number_out": SocketType.NUMBER}

    value = InputWidget(widget_type="NUMBER", default=10)

    def load(self):
        pass

    def execute(self):
        num_value = self.widget_values.get('value', self.value.default)
        return (float(num_value),) # Ensure it's a float

# --- PROCESSING NODE ---

class AddNode(BaseNode):
    CATEGORY = "Math"
    INPUT_SOCKETS = {"a": SocketType.NUMBER, "b": SocketType.NUMBER}
    OUTPUT_SOCKETS = {"result": SocketType.NUMBER}

    def load(self):
        pass

    def execute(self, a, b):
        # This node's logic is driven by its inputs, which are passed by the engine.
        result = float(a) + float(b)
        return (result,)

# --- OUTPUT NODE ---

class DisplayNode(BaseNode):
    CATEGORY = "Output"
    INPUT_SOCKETS = {"value_in": SocketType.ANY}

    def load(self):
        pass

    # FIX: Make 'value_in' optional with a default value of None.
    # This prevents an error if the node is run without an input connection.
    def execute(self, value_in=None):
        # This node just prints the value it receives to the backend console.
        print(f"--- DISPLAY NODE RECEIVED: {value_in} ---")
        return () # No output
