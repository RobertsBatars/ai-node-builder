# nodes/conditional_nodes.py
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT, MessageType

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


class NumberClassifierNode(BaseNode):
    """
    Classifies a numeric value into a group based on configurable thresholds.
    Outputs the original value (passthrough) and the zero-based group index.
    Useful for equivalence partitioning and boundary value testing workflows.
    """
    CATEGORY = "Conditional"

    INPUT_SOCKETS = {
        "value": {"type": SocketType.NUMBER, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "value_out": {"type": SocketType.ANY},
        "group_index": {"type": SocketType.NUMBER}
    }

    thresholds = InputWidget(
        widget_type="TEXT",
        default="50, 80"
    )
    boundary_rule = InputWidget(
        widget_type="COMBO",
        default="upper_exclusive (<)",
        properties={"values": ["upper_exclusive (<)", "upper_inclusive (<=)"]}
    )

    def load(self):
        pass

    async def execute(self, value):
        thresholds_str = self.get_widget_value_safe('thresholds', str)
        boundary_rule_val = self.get_widget_value_safe('boundary_rule', str)

        # Parse and sort thresholds, warn on invalid entries
        try:
            sorted_thresholds = sorted(
                [float(t.strip()) for t in thresholds_str.split(',') if t.strip()]
            )
        except ValueError:
            await self.send_message_to_client(
                MessageType.ERROR,
                {"message": f"NumberClassifierNode: could not parse thresholds '{thresholds_str}'. Using no thresholds (single group)."}
            )
            sorted_thresholds = []

        try:
            num_value = float(value)
        except (ValueError, TypeError):
            await self.send_message_to_client(
                MessageType.ERROR,
                {"message": f"NumberClassifierNode: could not convert value '{value}' to float. Defaulting to 0.0."}
            )
            num_value = 0.0

        # Determine group index — default is the last group (value exceeds all thresholds)
        group_index = len(sorted_thresholds)
        if boundary_rule_val == "upper_exclusive (<)":
            for i, threshold in enumerate(sorted_thresholds):
                if num_value < threshold:
                    group_index = i
                    break
        else:  # upper_inclusive (<=)
            for i, threshold in enumerate(sorted_thresholds):
                if num_value <= threshold:
                    group_index = i
                    break

        return (value, group_index)
