# nodes/trigger_detection_node.py
from core.definitions import BaseNode, SocketType, SKIP_OUTPUT

class TriggerDetectionNode(BaseNode):
    """
    A simple node that outputs which socket triggered it.
    Has two input sockets: one dependency and one do_not_wait.
    Outputs the name of the socket that triggered the execution.
    """
    CATEGORY = "Utility"
    
    INPUT_SOCKETS = {
        "dependency_input": {"type": SocketType.ANY, "is_dependency": True},
        "trigger_input": {"type": SocketType.ANY, "do_not_wait": True}
    }
    
    OUTPUT_SOCKETS = {
        "trigger_source": {"type": SocketType.TEXT}
    }

    def load(self):
        """Initialize the node."""
        pass

    def execute(self, dependency_input=None, trigger_input=None):
        """
        Determine which socket triggered this execution and output its name.
        
        Logic:
        - If trigger_input has data, it was triggered by the do_not_wait socket
        - Otherwise, it was triggered by the dependency socket
        """
        if trigger_input is not None:
            # Triggered by the do_not_wait socket
            return (trigger_input,)
        else:
            # Triggered by the dependency socket
            return (dependency_input,)