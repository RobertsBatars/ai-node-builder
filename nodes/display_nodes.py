# nodes/display_nodes.py
import copy
import json
from core.definitions import BaseNode, SocketType, InputWidget, MessageType

class DisplayOutputNode(BaseNode):
    """
    A node to send data to the frontend display panel and save it to the global context.
    """
    CATEGORY = "Output"
    INPUT_SOCKETS = {"data": {"type": SocketType.ANY}}
    
    content_type = InputWidget(widget_type="COMBO", default="text", properties={"values": ["text", "image", "video"]})

    def load(self):
        pass

    async def execute(self, data):
        ctype = self.widget_values.get('content_type', self.content_type.default)
        
        # If the input data is a list or dict, format it as a JSON string for display.
        display_data = data
        if isinstance(data, (list, dict)):
            try:
                display_data = json.dumps(data, indent=2)
            except TypeError:
                display_data = "Error: Could not serialize complex object."

        # This is the payload for the frontend message
        display_payload = {
            "node_title": self.node_info.get('title', self.__class__.__name__),
            "content_type": ctype,
            "data": display_data,
        }
        
        # This is the entry that gets stored in the persistent server context
        context_entry = {
            "node_id": self.node_info.get('id'),
            **display_payload
        }
        
        # 1. Append the message to the global server-side context
        self.global_state['display_context'].append(context_entry)
        
        # 2. Send the message to the client for immediate display
        await self.send_message_to_client(MessageType.DISPLAY, display_payload)
        
        return ()

class GetDisplayContextNode(BaseNode):
    """
    A node to retrieve the display context from the global state.
    """
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"context": {"type": SocketType.ANY}}
    
    filter_by_node_id = InputWidget(widget_type="BOOLEAN", default=False, properties={"on": "self", "off": "all"})

    def load(self):
        pass

    def execute(self):
        should_filter = self.widget_values.get('filter_by_node_id', self.filter_by_node_id.default)
        # Always work with a deep copy to prevent circular references in the workflow.
        full_context = copy.deepcopy(self.global_state['display_context'])
        
        if should_filter:
            my_node_id = self.node_info.get('id')
            # Filter the context for messages that originated from this specific node ID
            filtered_context = [msg for msg in full_context if msg.get("node_id") == my_node_id]
            return (filtered_context,)
        
        # Return the entire context if no filtering is requested
        return (full_context,)
