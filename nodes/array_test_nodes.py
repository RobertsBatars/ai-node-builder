# nodes/array_test_nodes.py
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT

class InputOutputArrayTestNode(BaseNode):
    """
    A test node to validate the implementation of both input and output dynamic arrays.
    """
    CATEGORY = "Test"

    # --- Sockets ---
    INPUT_SOCKETS = {
        "in_array": {"type": SocketType.TEXT, "array": True, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "out_array": {"type": SocketType.TEXT, "array": True}
    }

    # --- Widgets ---
    prefix = InputWidget(widget_type="TEXT", default="pre-")

    def load(self):
        pass

    def execute(self, in_array):
        """
        Adds a prefix to each input string and returns them as an output array.
        If an input string is "skip", it places SKIP_OUTPUT in the output array.
        """
        prefix_val = self.widget_values.get('prefix', self.prefix.default)
        
        output_list = []
        for item in in_array:
            if str(item).strip().lower() == "skip":
                output_list.append(SKIP_OUTPUT)
            else:
                output_list.append(f"{prefix_val}{item}")
        
        # The list is returned inside a tuple, as it corresponds to a single output socket.
        return (output_list,)
