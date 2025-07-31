# core/definitions.py
# This file contains the foundational, abstract classes and types for the entire application.

from abc import ABC, abstractmethod
from enum import Enum
import inspect
import json

# A special sentinel object to indicate that an output should be skipped.
SKIP_OUTPUT = object()

# A global counter to ensure widgets are ordered correctly
WIDGET_ORDER_COUNTER = 0

class MessageType(Enum):
    """Defines the valid types for messages sent from a node to the client."""
    LOG = "log"          # For general information
    DEBUG = "debug"      # For detailed, verbose information for developers
    TEST_EVENT = "test"  # For events specifically related to testing, like an assertion
    ERROR = "error"      # For reporting non-fatal errors from within a node
    DISPLAY = "display"  # For rich content display

class SocketType(Enum):
    """
    Defines the data types for connections. The frontend uses these for validation.
    """
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    IMAGE = "IMAGE"
    ANY = "*"
    # The concept of a dependency is now a property of the socket, not its data type.

class InputWidget:
    """
    A data container class used to declare a UI widget for a node's properties.
    """
    def __init__(self, widget_type="STRING", default=None, properties=None, **kwargs):
        global WIDGET_ORDER_COUNTER
        self.widget_type = widget_type
        self.default = default
        # If 'properties' is passed as a keyword argument, use its value.
        # Otherwise, assume the remaining kwargs are the properties.
        self.properties = properties if properties is not None else kwargs
        self.order = WIDGET_ORDER_COUNTER
        WIDGET_ORDER_COUNTER += 1

class NodeStateUpdate:
    """
    A data container used by nodes to request changes to their own state for subsequent executions.
    This is the mechanism for creating dynamic behavior, such as loops.
    """
    def __init__(self, wait_for_inputs=None):
        """
        Args:
            wait_for_inputs (list[str], optional): A list of input socket names that the node
                                                   should wait for in the next execution cycle.
                                                   If None, the wait configuration is not changed.
        """
        self.wait_for_inputs = wait_for_inputs


class BaseNode(ABC):
    """
    The Abstract Base Class for all nodes in the application.
    """
    CATEGORY = "Default"
    # Sockets are now defined as dictionaries containing their type and other properties.
    INPUT_SOCKETS = {}
    OUTPUT_SOCKETS = {}

    def __init__(self, engine, node_info, memory, run_id, global_state, event_manager=None):
        self.engine = engine
        self.node_info = node_info
        self.memory = memory
        self.run_id = run_id
        self.global_state = global_state
        self.event_manager = event_manager
        
        self.widget_values = {}
        if 'widgets_values' in self.node_info and self.node_info['widgets_values'] is not None:
            widget_declarations = sorted(
                [w for w in inspect.getmembers(self.__class__) if isinstance(w[1], InputWidget)],
                key=lambda x: x[1].order
            )
            for i, value in enumerate(self.node_info['widgets_values']):
                if i < len(widget_declarations):
                    widget_name = widget_declarations[i][0]
                    self.widget_values[widget_name] = value

    async def send_message_to_client(self, message_type: MessageType, data: dict):
        """Sends a structured, type-safe message to the connected client via the engine's broadcast system."""
        full_message = {
            "source": "node",
            "type": message_type.value, # Use the enum's value for the JSON string
            "run_id": self.run_id,
            "payload": {
                "node_id": self.node_info.get('id'),
                "node_type": self.__class__.__name__,
                "data": data
            }
        }
        await self.engine.broadcast(full_message)

    def get_input_name_by_slot(self, slot_index):
        """Helper to find an input socket's name by its position."""
        return list(self.INPUT_SOCKETS.keys())[slot_index]

    @abstractmethod
    def load(self):
        """Perform one-time setup."""
        pass

    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        Perform the node's main work.

        This method can return one of two things:
        1. A tuple of output values, e.g., (value_for_output_1, value_for_output_2)
        2. A tuple containing two elements:
           - The tuple of output values.
           - A NodeStateUpdate object to dynamically change the node's behavior.
           e.g., ((value_for_output_1,), NodeStateUpdate(wait_for_inputs=['new_input']))
        """
        pass


class EventNode(BaseNode):
    """
    Abstract Base Class for nodes that can trigger workflows based on external events.
    """
    @abstractmethod
    async def start_listening(self, trigger_workflow_callback):
        """
        Start listening for the external event. When the event occurs, this method
        should call the provided `trigger_workflow_callback` function.
        """
        pass

    @abstractmethod
    async def stop_listening(self):
        """Stop listening for the external event."""
        pass
