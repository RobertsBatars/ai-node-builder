# core/definitions.py
# This file contains the foundational, abstract classes and types for the entire application.

from abc import ABC, abstractmethod
from enum import Enum
import inspect

# A global counter to ensure widgets are ordered correctly
WIDGET_ORDER_COUNTER = 0

class SocketType(Enum):
    """
    Defines the types of data that can flow through node connections.
    """
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    IMAGE = "IMAGE"
    # FIX: Use "*" as the wildcard type, as expected by litegraph.js
    ANY = "*"

class InputWidget:
    """
    A data container class used to declare a UI widget for a node's properties.
    The engine inspects node classes for attributes of this type to auto-generate the UI.
    """
    def __init__(self, widget_type="STRING", default=None, **properties):
        """
        Initializes the widget definition.
        """
        global WIDGET_ORDER_COUNTER
        self.widget_type = widget_type
        self.default = default
        self.properties = properties
        self.order = WIDGET_ORDER_COUNTER
        WIDGET_ORDER_COUNTER += 1


class BaseNode(ABC):
    """
    The Abstract Base Class for all nodes in the application.
    """
    CATEGORY = "Default"
    INPUT_SOCKETS = {}
    OUTPUT_SOCKETS = {}

    def __init__(self, engine, node_info):
        """
        Initializes the node instance.
        """
        self.engine = engine
        self.node_info = node_info
        
        self.widget_values = {}
        # This logic correctly parses the 'widgets_values' array from LiteGraph
        if 'widgets_values' in self.node_info and self.node_info['widgets_values'] is not None:
            # Sort the declared widgets by their creation order to match the frontend
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
        """Perform the node's main work."""
        pass
