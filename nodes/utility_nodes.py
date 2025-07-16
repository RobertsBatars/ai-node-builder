# nodes/utility_nodes.py
import asyncio
from core.definitions import BaseNode, SocketType, InputWidget

class WaitNode(BaseNode):
    """
    A node that waits for a specified duration before passing through the input.
    This is useful for testing workflow cancellation and for creating delays.
    """
    CATEGORY = "Utility"

    INPUT_SOCKETS = {
        "trigger": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }

    # A widget to get the wait time from the user in the UI
    wait_time_seconds = InputWidget(
        widget_type="NUMBER",
        default=5,
        properties={"min": 0, "step": 0.1}
    )

    def load(self):
        """Called once when the workflow is initialized."""
        pass

    async def execute(self, trigger):
        """
        Waits for the specified duration, then returns the input value.
        The 'async' keyword is crucial here to allow non-blocking waits.
        """
        # Get the wait duration from the widget's value
        duration = self.widget_values.get('wait_time_seconds', self.wait_time_seconds.default)
        
        # Ensure duration is a non-negative number
        try:
            duration = float(duration)
            if duration < 0:
                duration = 0
        except (ValueError, TypeError):
            duration = self.wait_time_seconds.default

        print(f"WaitNode: Waiting for {duration} seconds...")
        await asyncio.sleep(duration)
        print("WaitNode: Finished waiting.")

        # Pass the original trigger value to the output
        return (trigger,)
