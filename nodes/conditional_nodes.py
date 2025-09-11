# nodes/conditional_nodes.py
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT

class DecisionNode(BaseNode):
    """
    A node that routes an input value to one of two outputs based on a condition.
    """
    CATEGORY = "Conditional"

    # --- Sockets ---
    INPUT_SOCKETS = {
        "input_value": {"type": SocketType.NUMBER, "is_dependency": True},
        "comparison_value": {"type": SocketType.NUMBER, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "true_output": {"type": SocketType.ANY},
        "false_output": {"type": SocketType.ANY}
    }

    # --- Widgets ---
    operator = InputWidget(
        widget_type="COMBO",
        default="==",
        properties={"values": ["==", "!=", ">", "<", ">=", "<="]}
    )

    def load(self):
        pass

    def execute(self, input_value, comparison_value):
        """
        Compares the input_value to the comparison_value and routes it
        to the appropriate output.
        """
        op_str = self.widget_values.get('operator', self.operator.default)
        
        # Attempt to convert to numbers for comparison if possible
        try:
            val1 = float(input_value)
            val2 = float(comparison_value)
        except (ValueError, TypeError):
            # Fallback to string comparison
            val1 = str(input_value)
            val2 = str(comparison_value)

        # --- Comparison Logic ---
        result = False
        if op_str == "==":
            result = val1 == val2
        elif op_str == "!=":
            result = val1 != val2
        elif op_str == ">":
            # Type check for numeric comparison
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                result = val1 > val2  # type: ignore
            else:
                result = str(val1) > str(val2)
        elif op_str == "<":
            # Type check for numeric comparison
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                result = val1 < val2  # type: ignore
            else:
                result = str(val1) < str(val2)
        elif op_str == ">=":
            # Type check for numeric comparison
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                result = val1 >= val2  # type: ignore
            else:
                result = str(val1) >= str(val2)
        elif op_str == "<=":
            # Type check for numeric comparison
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                result = val1 <= val2  # type: ignore
            else:
                result = str(val1) <= str(val2)
            
        # --- Routing Logic ---
        if result:
            # Send data to true_output, skip false_output
            return (input_value, SKIP_OUTPUT)
        else:
            # Send data to false_output, skip true_output
            return (SKIP_OUTPUT, input_value)
