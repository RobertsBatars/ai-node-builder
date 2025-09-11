# nodes/simple_nodes.py
# Updated nodes to use the new socket definition format.
from core.definitions import BaseNode, SocketType, InputWidget, MessageType

# --- INPUT NODES ---

class TextNode(BaseNode):
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"text_out": {"type": SocketType.TEXT}}
    
    value = InputWidget(widget_type="TEXT", default="Hello from backend!")

    def load(self):
        pass

    def execute(self):
        text_value = self.get_widget_value_safe('value', str)  # Uses InputWidget default
        return (text_value,)

class NumberNode(BaseNode):
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"number_out": {"type": SocketType.NUMBER}}

    value = InputWidget(widget_type="NUMBER", default=10)

    def load(self):
        pass

    def execute(self):
        num_value = self.get_widget_value_safe('value', int)  # Uses InputWidget default=10
        return (num_value,)

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

    async def execute(self, texts):
        separator_value = self.get_widget_value_safe('separator', str)
        # 'texts' will be a list of strings
        if isinstance(separator_value, str):
            result = separator_value.join(texts)
        else:
            await self.send_message_to_client(
                MessageType.ERROR,
                {"message": f"Separator widget returned non-string value: {type(separator_value).__name__} = {repr(separator_value)}. Using default ', ' separator."}
            )
            result = ', '.join(texts)  # fallback
        return (result,)

# --- OUTPUT NODE ---

class LogNode(BaseNode):
    CATEGORY = "Output"
    # This is a dependency input that pulls data from connected nodes.
    INPUT_SOCKETS = {"value_in": {"type": SocketType.ANY, "is_dependency": True}}
    # Output socket to pass through the input data
    OUTPUT_SOCKETS = {"value_out": {"type": SocketType.ANY}}
    
    # Combo widget to select message type
    message_type = InputWidget(
        widget_type="COMBO", 
        default="LOG", 
        properties={"values": ["LOG", "DEBUG", "TEST_EVENT", "ERROR", "DISPLAY"]}
    )

    def load(self):
        pass

    async def execute(self, value_in=None):
        from core.definitions import MessageType
        
        # Get the selected message type from the widget
        msg_type = self.get_widget_value_safe('message_type', str)
        
        # Map string to MessageType enum
        message_type_map = {
            "LOG": MessageType.LOG,
            "DEBUG": MessageType.DEBUG,
            "TEST_EVENT": MessageType.TEST_EVENT,
            "ERROR": MessageType.ERROR,
            "DISPLAY": MessageType.DISPLAY
        }
        
        selected_type = message_type_map.get(msg_type, MessageType.LOG)
        
        # Prepare data dictionary based on message type
        if selected_type == MessageType.DISPLAY:
            # Special structure for DISPLAY messages
            data_dict = {
                "node_title": self.node_info.get('title', self.__class__.__name__),
                "content_type": "text",
                "data": str(value_in)
            }
        else:
            # Standard structure for other message types
            data_dict = {
                "message": str(value_in),
                "node_id": self.node_info.get('id', 'unknown'),
                "timestamp": __import__('time').time()
            }
        
        # Send message to client using the proper method
        await self.send_message_to_client(selected_type, data_dict)
        
        # Pass through the input value to the output
        return (value_in,)

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
        text_val = self.get_widget_value_safe('text_widget', str)  # Uses widget default
        number_val = self.get_widget_value_safe('number_widget', int)  # Uses widget default
        slider_val = self.get_widget_value_safe('slider_widget', float)  # Uses widget default
        boolean_val = self.get_widget_value_safe('boolean_widget', bool)  # Uses widget default
        combo_val = self.get_widget_value_safe('combo_widget', str)  # Uses widget default

        output_string = f"Text: {text_val}, Number: {number_val}, Slider: {slider_val}, Boolean: {boolean_val}, Combo: {combo_val}"
        return (output_string,)