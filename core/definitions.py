# core/definitions.py
# This file contains the foundational, abstract classes and types for the entire application.

from abc import ABC, abstractmethod
from enum import Enum
import inspect

# A special sentinel object to indicate that an output should be skipped.
SKIP_OUTPUT = object()

# A global counter to ensure widgets are ordered correctly
WIDGET_ORDER_COUNTER = 0

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

    def __init__(self, engine, node_info, memory):
        self.engine = engine
        self.node_info = node_info
        self.memory = memory
        
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
