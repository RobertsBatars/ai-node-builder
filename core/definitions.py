# core/definitions.py
# This file contains the foundational, abstract classes and types for the entire application.

from abc import ABC, abstractmethod
from enum import Enum

class SocketType(Enum):
    """
    Defines the types of data that can flow through node connections.
    This ensures that nodes can only be connected if their types are compatible.
    """
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    IMAGE = "IMAGE"
    ANY = "ANY"  # A generic type that can connect to anything
    # Add more specific AI types later
    # MODEL = "MODEL"
    # TOOL_DEFINITION = "TOOL_DEFINITION"
    # TOOL_CALL = "TOOL_CALL"

class InputWidget:
    """
    A data container class used to declare a UI widget for a node's properties.
    The engine inspects node classes for attributes of this type to auto-generate the UI.
    """
    def __init__(self, widget_type="STRING", default=None, **properties):
        """
        Initializes the widget definition.

        Args:
            widget_type (str): The type of widget for the frontend (e.g., "SLIDER", "COMBOBOX").
            default: The default value for the widget.
            **properties: Any other widget-specific properties (e.g., min, max, step, options_callback).
        """
        self.widget_type = widget_type
        self.default = default
        self.properties = properties

class BaseNode(ABC):
    """
    The Abstract Base Class for all nodes in the application.
    It acts as a contract, ensuring that any new node created by a developer
    adheres to a standard structure.
    """
    # Default attributes that can be overridden by subclasses
    CATEGORY = "Default"
    INPUT_SOCKETS = {}
    OUTPUT_SOCKETS = {}

    def __init__(self, engine):
        """
        Initializes the node instance, giving it a reference to the engine.
        """
        self.engine = engine

    @abstractmethod
    def load(self):
        """
        Perform one-time setup. This method MUST be implemented by every node.
        It is called once when the workflow starts.
        If a node has no setup, it should just contain 'pass'.
        """
        pass

    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        Perform the node's main work. This method MUST be implemented.
        It is called every time the dataflow reaches the node.
        """
        pass
