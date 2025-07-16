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

# --- ARRAY TEST NODE ---

class ConcatenateArrayNode(BaseNode):
    CATEGORY = "Text"
    INPUT_SOCKETS = {
        "texts": {"type": SocketType.TEXT, "array": True, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "full_text": {"type": SocketType.TEXT}
    }
    separator = InputWidget(widget_type="TEXT", default=", ")

    def load(self):
        """
        Required by the BaseNode.
        """
        pass

    def execute(self, texts):
        separator_value = self.widget_values.get('separator', self.separator.default)
        # 'texts' will be a list of strings
        result = separator_value.join(texts)
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

class WidgetTestNode(BaseNode):
    CATEGORY = "Test"
    OUTPUT_SOCKETS = {"output": {"type": SocketType.TEXT}}

    # Test all supported widget types by defining the 'properties' object
    # with the exact structure that LiteGraph.js expects for its 'options'.
    text_widget = InputWidget(widget_type="TEXT", default="Test String")
    number_widget = InputWidget(widget_type="NUMBER", default=42, properties={"min": 0, "max": 100, "step": 1})
    slider_widget = InputWidget(widget_type="SLIDER", default=5, properties={"min": 0, "max": 10, "step": 0.1})
    boolean_widget = InputWidget(widget_type="BOOLEAN", default=True)
    combo_widget = InputWidget(widget_type="COMBO", default="Option 2", properties={"values": ["Option 1", "Option 2", "Option 3"]})

    def load(self):
        pass

    def execute(self):
        text_val = self.widget_values.get('text_widget', self.text_widget.default)
        number_val = self.widget_values.get('number_widget', self.number_widget.default)
        slider_val = self.widget_values.get('slider_widget', self.slider_widget.default)
        boolean_val = self.widget_values.get('boolean_widget', self.boolean_widget.default)
        combo_val = self.widget_values.get('combo_widget', self.combo_widget.default)

        output_string = f"Text: {text_val}, Number: {number_val}, Slider: {slider_val}, Boolean: {boolean_val}, Combo: {combo_val}"
        return (output_string,)