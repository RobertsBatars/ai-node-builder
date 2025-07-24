# nodes/logging_test_nodes.py
# Test nodes for verifying the logging functionality

import asyncio
from core.definitions import BaseNode, SocketType, MessageType

class LoggingTestNode(BaseNode):
    """
    A test node that sends various types of messages to the frontend.
    """
    CATEGORY = "Test"
    INPUT_SOCKETS = {
        "trigger": {"type": SocketType.ANY}
    }
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.TEXT}
    }

    def load(self):
        pass

    async def execute(self, trigger):
        # Send a log message
        await self.send_message_to_client(
            MessageType.LOG,
            {"message": "This is a log message from LoggingTestNode"}
        )
        
        # Send a debug message
        await self.send_message_to_client(
            MessageType.DEBUG,
            {"message": "This is a debug message with more details"}
        )
        
        # Send a test event message
        await self.send_message_to_client(
            MessageType.TEST_EVENT,
            {"message": "This is a test event", "status": "success"}
        )
        
        # Simulate some work
        await asyncio.sleep(1)
        
        # Send an error message
        await self.send_message_to_client(
            MessageType.ERROR,
            {"message": "This is a simulated error message"}
        )
        
        return ("Test completed",)