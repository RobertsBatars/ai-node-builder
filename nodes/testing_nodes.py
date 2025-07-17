# nodes/testing_nodes.py
# nodes/testing_nodes.py
from core.definitions import BaseNode, SocketType, SKIP_OUTPUT, MessageType

class AssertNode(BaseNode):
    """
    A node to assert that a value matches an expected value.
    Crucial for automated testing of workflows.
    """
    CATEGORY = "Testing"

    INPUT_SOCKETS = {
        "actual": {"type": SocketType.ANY},
        "expected": {"type": SocketType.ANY, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "on_success": {"type": SocketType.ANY},
        "on_failure": {"type": SocketType.ANY}
    }

    def load(self):
        pass

    async def execute(self, actual, expected):
        """
        Compares the 'actual' and 'expected' inputs.
        Raises an exception if they do not match.
        """
        # Attempt to cast to float for numerical comparison if possible
        try:
            actual_val = float(actual)
            expected_val = float(expected)
        except (ValueError, TypeError, AttributeError):
            actual_val = str(actual)
            expected_val = str(expected)

        print(f"--- ASSERT NODE ---")
        print(f"  Actual: {actual_val} (type: {type(actual_val)})")
        print(f"  Expected: {expected_val} (type: {type(expected_val)})")

        is_match = actual_val == expected_val
        status = "SUCCESS" if is_match else "FAILURE"

        # Use the new API to send a structured message for the test runner
        await self.send_message_to_client(
            MessageType.TEST_EVENT,
            {"status": status, "actual": actual_val, "expected": expected_val}
        )

        if is_match:
            print("  Result: SUCCESS")
            return (actual, SKIP_OUTPUT)  # Pass value to on_success
        else:
            print("  Result: FAILURE")
            # The exception remains the primary failure mechanism for the engine
            raise AssertionError(f"Assertion Failed: Actual value '{actual_val}' does not match expected value '{expected_val}'.")


