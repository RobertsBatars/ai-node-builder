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

class TestDisplayFeatureNode(BaseNode):
    """
    A self-contained node to test the display feature end-to-end.
    """
    CATEGORY = "Test"
    # No inputs/outputs needed
    
    def load(self):
        pass

    async def execute(self):
        import time
        my_id = self.node_info.get('id')
        test_message = f"Test message from {my_id} at {time.time()}"
        
        # 1. Send a message to the display
        display_payload = {"node_title": "Test Node", "content_type": "text", "data": test_message}
        context_entry = {"node_id": my_id, **display_payload}
        
        self.global_state['display_context'].append(context_entry)
        await self.send_message_to_client(MessageType.DISPLAY, display_payload)
        
        # 2. Retrieve context and verify the message was added
        retrieved_context = self.get_display_context()
        found = any(msg.get('data') == test_message and msg.get('node_id') == my_id for msg in retrieved_context)
        
        if found:
            await self.send_message_to_client(MessageType.LOG, {"message": "SUCCESS: Test node found its message in the global context."})
        else:
            await self.send_message_to_client(MessageType.ERROR, {"message": "FAILURE: Test node did not find its message in the global context."})
        
        return ()


