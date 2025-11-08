# nodes/dictionary_nodes.py
# Dictionary manipulation nodes for the AI Node Builder

import json
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT, MessageType

class DictionaryInputNode(BaseNode):
    """
    Creates a dictionary from JSON text input via widget.
    Supports nested structures including arrays, nested dictionaries, and all JSON types.
    """
    CATEGORY = "Input"
    OUTPUT_SOCKETS = {"dictionary_out": {"type": SocketType.DICTIONARY}}

    json_input = InputWidget(
        widget_type="TEXT",
        default='{"name": "John", "age": 30, "score": 95.5}',
    )

    max_nesting_depth = InputWidget(
        widget_type="NUMBER",
        default=10,
        properties={"min": 1, "max": 50}
    )

    def load(self):
        pass

    def _validate_value(self, value, depth, max_depth):
        """Validate individual values recursively."""
        if depth > max_depth:
            raise ValueError(f"Nesting depth exceeds maximum of {max_depth}")

        # Primitives - accept as-is
        if isinstance(value, (str, int, float, bool, type(None))):
            return value

        # Arrays - validate each element recursively
        elif isinstance(value, list):
            return [self._validate_value(item, depth + 1, max_depth) for item in value]

        # Nested dictionaries - validate recursively
        elif isinstance(value, dict):
            return self._validate_dictionary(value, depth + 1, max_depth)

        # Unsupported type
        else:
            raise ValueError(f"Unsupported type: {type(value).__name__}")

    def _validate_dictionary(self, data, depth=0, max_depth=10):
        """Validate dictionary structure with support for nested structures."""
        if depth > max_depth:
            raise ValueError(f"Nesting depth exceeds maximum of {max_depth}")

        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")

        validated = {}
        for key, value in data.items():
            if not isinstance(key, str):
                raise ValueError(f"All keys must be strings, got {type(key).__name__}: {key}")

            # Validate value recursively
            validated[key] = self._validate_value(value, depth, max_depth)

        return validated

    async def execute(self):
        json_text = self.get_widget_value_safe('json_input', str)
        max_depth = self.get_widget_value_safe('max_nesting_depth', int)

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

            # Validate dictionary structure with nesting depth limit
            validated_dict = self._validate_dictionary(parsed_dict, 0, max_depth)

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
    Supports primitives, arrays, and nested dictionaries as values.
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

    def _is_valid_value(self, value):
        """Check if value is a valid dictionary value type."""
        # Primitives
        if isinstance(value, (str, int, float, bool, type(None))):
            return True
        # Arrays
        elif isinstance(value, (list, tuple)):
            return all(self._is_valid_value(item) for item in value)
        # Nested dictionaries
        elif isinstance(value, dict):
            if not all(isinstance(k, str) for k in value.keys()):
                return False
            return all(self._is_valid_value(v) for v in value.values())
        else:
            return False

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

        # Validate value type - accept extended types, convert invalid ones to string
        if not self._is_valid_value(value):
            # Convert to string for backward compatibility
            value = str(value)

        # Create new dictionary with updated value (immutable operation)
        # Use deep copy for nested structures
        import copy
        updated_dict = copy.deepcopy(dictionary)
        updated_dict[key] = value

        return (updated_dict,)


class ArrayElementGetNode(BaseNode):
    """
    Extract specific element from array by index.
    Supports negative indexing for accessing from the end.
    """
    CATEGORY = "Dictionary"

    INPUT_SOCKETS = {
        "array_in": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "element": {"type": SocketType.ANY},
        "error": {"type": SocketType.TEXT}
    }

    index = InputWidget(widget_type="NUMBER", default=0)
    allow_negative = InputWidget(widget_type="BOOLEAN", default=True)

    def load(self):
        pass

    async def execute(self, array_in):
        idx = self.get_widget_value_safe('index', int)
        allow_neg = self.get_widget_value_safe('allow_negative', bool)

        # Validate input is array
        if not isinstance(array_in, (list, tuple)):
            error_msg = f"Input must be an array, got {type(array_in).__name__}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        # Validate negative index setting
        if not allow_neg and idx < 0:
            error_msg = "Negative indices not allowed (check allow_negative widget)"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        # Bounds checking
        try:
            element = array_in[idx]
            return (element, SKIP_OUTPUT)
        except IndexError:
            error_msg = f"Index {idx} out of range for array of length {len(array_in)}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)


class ArrayElementSetNode(BaseNode):
    """
    Update specific array element by index.
    Returns new array with element updated (immutable operation).
    """
    CATEGORY = "Dictionary"

    INPUT_SOCKETS = {
        "array_in": {"type": SocketType.ANY, "is_dependency": True},
        "value": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "updated_array": {"type": SocketType.ANY},
        "error": {"type": SocketType.TEXT}
    }

    index = InputWidget(widget_type="NUMBER", default=0)
    allow_append = InputWidget(widget_type="BOOLEAN", default=True)

    def load(self):
        pass

    async def execute(self, array_in, value):
        idx = self.get_widget_value_safe('index', int)
        allow_append_val = self.get_widget_value_safe('allow_append', bool)

        # Validate input is array
        if not isinstance(array_in, (list, tuple)):
            error_msg = f"Input must be an array, got {type(array_in).__name__}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        # Convert to list for modification (immutable operation)
        import copy
        result = copy.deepcopy(list(array_in))

        # Handle append case
        if idx == len(result) and allow_append_val:
            result.append(value)
            return (result, SKIP_OUTPUT)

        # Bounds checking
        if idx < 0 or idx >= len(result):
            error_msg = f"Index {idx} out of range for array of length {len(result)}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        # Update element
        result[idx] = value
        return (result, SKIP_OUTPUT)


class ArrayLengthNode(BaseNode):
    """
    Get the length/size of an array.
    Returns number of elements in the array.
    """
    CATEGORY = "Dictionary"

    INPUT_SOCKETS = {
        "array_in": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "length": {"type": SocketType.NUMBER},
        "error": {"type": SocketType.TEXT}
    }

    def load(self):
        pass

    async def execute(self, array_in):
        # Validate input is array
        if not isinstance(array_in, (list, tuple)):
            error_msg = f"Input must be an array, got {type(array_in).__name__}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        return (len(array_in), SKIP_OUTPUT)


class ArrayAppendNode(BaseNode):
    """
    Append or prepend elements to arrays.
    Returns new array with element added (immutable operation).
    """
    CATEGORY = "Dictionary"

    INPUT_SOCKETS = {
        "array_in": {"type": SocketType.ANY, "is_dependency": True},
        "value": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "updated_array": {"type": SocketType.ANY},
        "error": {"type": SocketType.TEXT}
    }

    position = InputWidget(
        widget_type="COMBO",
        default="end",
        properties={"values": ["end", "start"]}
    )

    def load(self):
        pass

    async def execute(self, array_in, value):
        pos = self.get_widget_value_safe('position', str)

        # Validate input is array
        if not isinstance(array_in, (list, tuple)):
            error_msg = f"Input must be an array, got {type(array_in).__name__}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        # Immutable operation - create new list
        import copy
        result = copy.deepcopy(list(array_in))

        if pos == "start":
            result.insert(0, value)
        else:  # "end"
            result.append(value)

        return (result, SKIP_OUTPUT)


class ArraySliceNode(BaseNode):
    """
    Extract a slice/segment from an array.
    Supports Python-style slicing with start, end, and step parameters.
    """
    CATEGORY = "Dictionary"

    INPUT_SOCKETS = {
        "array_in": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "sliced_array": {"type": SocketType.ANY},
        "error": {"type": SocketType.TEXT}
    }

    start_index = InputWidget(widget_type="NUMBER", default=0)
    end_index = InputWidget(widget_type="NUMBER", default=-1)
    step = InputWidget(widget_type="NUMBER", default=1)

    def load(self):
        pass

    async def execute(self, array_in):
        start = self.get_widget_value_safe('start_index', int)
        end = self.get_widget_value_safe('end_index', int)
        step_val = self.get_widget_value_safe('step', int)

        # Validate input is array
        if not isinstance(array_in, (list, tuple)):
            error_msg = f"Input must be an array, got {type(array_in).__name__}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        # Validate step
        if step_val == 0:
            error_msg = "Step cannot be zero"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        # Handle end = -1 as "end of array" (None in Python slicing)
        if end == -1:
            end_slice = None
        else:
            end_slice = end

        # Slice the array
        try:
            result = list(array_in[start:end_slice:step_val])
            return (result, SKIP_OUTPUT)
        except Exception as e:
            error_msg = f"Slice error: {str(e)}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)


class ArrayFilterNode(BaseNode):
    """
    Filter array elements by type or condition.
    Returns new array with filtered elements.
    """
    CATEGORY = "Dictionary"

    INPUT_SOCKETS = {
        "array_in": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "filtered_array": {"type": SocketType.ANY},
        "error": {"type": SocketType.TEXT}
    }

    filter_type = InputWidget(
        widget_type="COMBO",
        default="remove_null",
        properties={"values": [
            "remove_null",
            "remove_empty",
            "remove_duplicates",
            "numeric_only",
            "string_only",
            "dict_only",
            "array_only"
        ]}
    )

    def load(self):
        pass

    async def execute(self, array_in):
        filter_val = self.get_widget_value_safe('filter_type', str)

        # Validate input is array
        if not isinstance(array_in, (list, tuple)):
            error_msg = f"Input must be an array, got {type(array_in).__name__}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        # Apply filter
        try:
            if filter_val == "remove_null":
                result = [x for x in array_in if x is not None]
            elif filter_val == "remove_empty":
                result = [x for x in array_in if x not in (None, "", [], {})]
            elif filter_val == "remove_duplicates":
                seen = set()
                result = []
                for item in array_in:
                    # Handle unhashable types (like dicts, lists)
                    try:
                        if item not in seen:
                            seen.add(item)
                            result.append(item)
                    except TypeError:
                        # Unhashable type, always include
                        result.append(item)
            elif filter_val == "numeric_only":
                result = [x for x in array_in if isinstance(x, (int, float)) and not isinstance(x, bool)]
            elif filter_val == "string_only":
                result = [x for x in array_in if isinstance(x, str)]
            elif filter_val == "dict_only":
                result = [x for x in array_in if isinstance(x, dict)]
            elif filter_val == "array_only":
                result = [x for x in array_in if isinstance(x, (list, tuple))]
            else:
                result = list(array_in)

            return (result, SKIP_OUTPUT)
        except Exception as e:
            error_msg = f"Filter error: {str(e)}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)


class ArrayToStringNode(BaseNode):
    """
    Convert arrays to formatted strings.
    Supports multiple output formats including JSON, CSV, and custom separators.
    """
    CATEGORY = "Dictionary"

    INPUT_SOCKETS = {
        "array_in": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "string_out": {"type": SocketType.TEXT},
        "error": {"type": SocketType.TEXT}
    }

    format_type = InputWidget(
        widget_type="COMBO",
        default="json",
        properties={"values": ["json", "comma_separated", "newline_separated", "custom"]}
    )
    separator = InputWidget(widget_type="TEXT", default=", ")
    indent_json = InputWidget(widget_type="BOOLEAN", default=True)

    def load(self):
        pass

    async def execute(self, array_in):
        format_val = self.get_widget_value_safe('format_type', str)
        sep = self.get_widget_value_safe('separator', str)
        indent = self.get_widget_value_safe('indent_json', bool)

        # Validate input is array
        if not isinstance(array_in, (list, tuple)):
            error_msg = f"Input must be an array, got {type(array_in).__name__}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)

        try:
            if format_val == "json":
                result = json.dumps(list(array_in), indent=2 if indent else None)
            elif format_val == "comma_separated":
                result = ", ".join(str(x) for x in array_in)
            elif format_val == "newline_separated":
                result = "\n".join(str(x) for x in array_in)
            elif format_val == "custom":
                result = sep.join(str(x) for x in array_in)
            else:
                result = str(array_in)

            return (result, SKIP_OUTPUT)
        except Exception as e:
            error_msg = f"Conversion error: {str(e)}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)


class ArrayToDictionaryNode(BaseNode):
    """
    Wraps an array in a dictionary with a specified key name.
    Converts array format [1, 2, 3] to dictionary format {"items": [1, 2, 3]}.
    This node is useful for converting plain arrays into the dictionary format expected by dictionary nodes.
    """
    CATEGORY = "Dictionary"

    INPUT_SOCKETS = {
        "array_in": {"type": SocketType.ANY, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "dictionary_out": {"type": SocketType.DICTIONARY},
        "error": {"type": SocketType.TEXT}
    }

    key_name = InputWidget(
        widget_type="TEXT",
        default="items",
        properties={"placeholder": "Key name for array"}
    )

    def load(self):
        pass

    async def execute(self, array_in):
        try:
            # Get the key name from widget
            key = self.get_widget_value_safe('key_name', str)
            if not key:
                error_msg = "Key name cannot be empty"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return (SKIP_OUTPUT, error_msg)

            # Validate that key is a valid string (no special characters that would break JSON)
            if not isinstance(key, str) or not key.strip():
                error_msg = "Key name must be a non-empty string"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return (SKIP_OUTPUT, error_msg)

            # Validate that input is an array
            if not isinstance(array_in, (list, tuple)):
                error_msg = f"Input must be an array, got {type(array_in).__name__}"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return (SKIP_OUTPUT, error_msg)

            # Create dictionary with array
            result = {key.strip(): list(array_in)}

            await self.send_message_to_client(
                MessageType.DEBUG,
                {"message": f"Wrapped array of length {len(array_in)} in dictionary with key '{key.strip()}'"}
            )

            return (result, SKIP_OUTPUT)

        except Exception as e:
            error_msg = f"Conversion error: {str(e)}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return (SKIP_OUTPUT, error_msg)