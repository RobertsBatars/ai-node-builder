# nodes/dictionary_nodes.py
# Dictionary manipulation nodes for the AI Node Builder

import json
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT, MessageType

class DictionaryInputNode(BaseNode):
    """
    Creates a dictionary from JSON text input via widget.
    Note: Using regular TEXT widget for now, larger widget planned for future.
    """
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"dictionary_out": {"type": SocketType.DICTIONARY}}
    
    json_input = InputWidget(
        widget_type="TEXT", 
        default='{"name": "John", "age": 30, "score": 95.5}',
    )

    def load(self):
        pass

    def _validate_dictionary(self, data):
        """Validate that the data is a proper dictionary with string keys and string/number values."""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        validated = {}
        for key, value in data.items():
            if not isinstance(key, str):
                raise ValueError(f"All keys must be strings, got {type(key).__name__}: {key}")
            if not isinstance(value, (str, int, float)):
                raise ValueError(f"Value for key '{key}' must be string or number, got {type(value).__name__}")
            validated[key] = value
        
        return validated

    async def execute(self):
        json_text = self.get_widget_value_safe('json_input', str)
        
        # Check if user provided empty input
        if not json_text or json_text.strip() == "":
            await self.send_message_to_client(
                MessageType.ERROR, 
                {"message": "JSON input cannot be empty"}
            )
            return ({},)
        
        try:
            # Parse JSON
            parsed_dict = json.loads(json_text)
            
            # Validate dictionary structure
            validated_dict = self._validate_dictionary(parsed_dict)
            
            return (validated_dict,)
            
        except json.JSONDecodeError as e:
            # Return empty dict and log JSON parsing error
            await self.send_message_to_client(
                MessageType.ERROR, 
                {"message": f"Invalid JSON syntax: {str(e)}"}
            )
            return ({},)
            
        except ValueError as e:
            # Return empty dict for validation errors
            await self.send_message_to_client(
                MessageType.ERROR, 
                {"message": f"Dictionary validation error: {str(e)}"}
            )
            return ({},)
        
        except Exception as e:
            # Catch any unexpected errors
            await self.send_message_to_client(
                MessageType.ERROR, 
                {"message": f"Unexpected error creating dictionary: {str(e)}"}
            )
            return ({},)


class DictionaryGetElementNode(BaseNode):
    """
    Retrieves an element from a dictionary by key.
    Returns either the value or an error message using SKIP_OUTPUT pattern.
    """
    CATEGORY = "Dictionary"
    INPUT_SOCKETS = {
        "dictionary": {"type": SocketType.DICTIONARY, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "value": {"type": SocketType.ANY},
        "error": {"type": SocketType.TEXT}
    }
    
    key_to_get = InputWidget(
        widget_type="TEXT", 
        default="name"
    )

    def load(self):
        pass

    async def execute(self, dictionary):
        key = self.get_widget_value_safe('key_to_get', str)
        
        # Validate inputs
        if not isinstance(dictionary, dict):
            error_msg = f"Expected dictionary input, got {type(dictionary).__name__}"
            await self.send_message_to_client(
                MessageType.ERROR, 
                {"message": error_msg}
            )
            return (SKIP_OUTPUT, error_msg)
        
        # Check if key is empty or just whitespace
        if not key or key.strip() == "":
            error_msg = "Key cannot be empty"
            await self.send_message_to_client(
                MessageType.ERROR, 
                {"message": error_msg}
            )
            return (SKIP_OUTPUT, error_msg)
        
        # Try to get the value
        if key in dictionary:
            value = dictionary[key]
            return (value, SKIP_OUTPUT)
        else:
            error_msg = f"Key '{key}' not found in dictionary"
            await self.send_message_to_client(
                MessageType.ERROR, 
                {"message": error_msg}
            )
            return (SKIP_OUTPUT, error_msg)


class DictionarySetElementNode(BaseNode):
    """
    Sets or updates an element in a dictionary.
    Takes dictionary input, key from widget, and value from input socket.
    Returns updated dictionary (immutable operation - creates new dict).
    """
    CATEGORY = "Dictionary"
    INPUT_SOCKETS = {
        "dictionary": {"type": SocketType.DICTIONARY, "is_dependency": True},
        "value": {"type": SocketType.ANY, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "updated_dictionary": {"type": SocketType.DICTIONARY}
    }
    
    key_to_set = InputWidget(
        widget_type="TEXT", 
        default="new_key"
    )

    def load(self):
        pass

    async def execute(self, dictionary, value):
        key = self.get_widget_value_safe('key_to_set', str)
        
        # Validate inputs
        if not isinstance(dictionary, dict):
            # Return original dictionary if input is invalid
            return (dictionary,)
        
        # Check if key is empty or just whitespace
        if not key or key.strip() == "":
            # Send error to frontend and return original dictionary
            await self.send_message_to_client(
                MessageType.ERROR, 
                {"message": "Key cannot be empty"}
            )
            return (dictionary,)
        
        # Validate value type (must be string, int, or float)
        if not isinstance(value, (str, int, float)):
            # Convert to string if it's not a supported type
            value = str(value)
        
        # Create new dictionary with updated value (immutable operation)
        updated_dict = dictionary.copy()
        updated_dict[key] = value
        
        return (updated_dict,)