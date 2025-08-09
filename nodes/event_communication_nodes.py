# nodes/event_communication_nodes.py
# Implementation of inter-workflow event communication nodes

import asyncio
import uuid
from core.definitions import BaseNode, EventNode, SocketType, InputWidget, MessageType

class ReceiveEventNode(EventNode):
    """
    Event node that listens for internal events and starts parallel workflows.
    Inherits from EventNode for event-driven behavior.
    """
    CATEGORY = "Events"
    
    INPUT_SOCKETS = {}
    OUTPUT_SOCKETS = {
        "data": {"type": SocketType.ANY},
        "event_id": {"type": SocketType.TEXT},
        "await_id": {"type": SocketType.TEXT}
    }
    
    listen_id = InputWidget(widget_type="TEXT", default="event_1")

    def load(self):
        self.trigger_callback = None
        self.listening_id = None

    async def start_listening(self, trigger_workflow_callback):
        """
        Register this node with the EventManager for internal event listening.
        """
        self.trigger_callback = trigger_workflow_callback
        self.listening_id = self.widget_values.get('listen_id', self.listen_id.default)
        
        # Register with event manager for internal events
        if self.event_manager:
            await self.event_manager.register_internal_listener(self.listening_id, self.trigger_callback)
            print(f"ReceiveEventNode: Listening for internal events with ID '{self.listening_id}'")
        else:
            print("Warning: EventManager not available for internal event registration")

    async def stop_listening(self):
        """
        Unregister from the EventManager.
        """
        if self.event_manager and self.listening_id:
            await self.event_manager.unregister_internal_listener(self.listening_id)
            print(f"ReceiveEventNode: Stopped listening for events with ID '{self.listening_id}'")
        
        self.trigger_callback = None
        self.listening_id = None

    def execute(self, *args, **kwargs):
        """
        Called when workflow starts from internal event.
        Returns the received data, event ID, and await_id if present.
        """
        payload = self.memory.get('initial_payload', "")
        # Use the widget value for event_id since listening_id might not be set at execute time
        event_id = self.widget_values.get('listen_id', self.listen_id.default)
        
        # Handle enhanced payload format for await functionality
        if isinstance(payload, dict) and 'data' in payload and 'await_id' in payload:
            actual_data = payload['data']
            await_id = payload['await_id']
            return (actual_data, event_id, await_id)
        else:
            # Simple payload without await functionality - skip empty await_id
            from core.definitions import SKIP_OUTPUT
            return (payload, event_id, SKIP_OUTPUT)


class SendEventNode(BaseNode):
    """
    Sends events to parallel workflows using event IDs.
    Accepts both single event ID string or array of event IDs.
    """
    CATEGORY = "Events"
    
    INPUT_SOCKETS = {
        "event_ids": {"type": SocketType.ANY, "is_dependency": True}, # CHANGE BACK TO NO DEPENDENCY AFTER TESTING
        "data": {"type": SocketType.ANY}
    }
    OUTPUT_SOCKETS = {
        "sent_count": {"type": SocketType.NUMBER}
    }
    
    event_id_widget = InputWidget(widget_type="TEXT", default="event_1")

    def load(self):
        pass

    async def execute(self, event_ids=None, data=None):
        """
        Send events to registered ReceiveEventNodes.
        Auto-detects if event_ids is string or array.
        """
        # Determine event IDs to use
        if event_ids is not None:
            # Use connected input
            if isinstance(event_ids, (list, tuple)):
                ids_to_send = event_ids
            else:
                ids_to_send = [str(event_ids)]
        else:
            # Use widget value
            widget_id = self.widget_values.get('event_id_widget', self.event_id_widget.default)
            ids_to_send = [widget_id]
        
        # Prepare data for sending
        if data is None:
            data = ""
        
        sent_count = 0
        
        # Send to event manager
        if self.event_manager:
            if isinstance(data, (list, tuple)) and len(ids_to_send) > 1:
                # Array data with array IDs - match element count
                for i, event_id in enumerate(ids_to_send):
                    payload = data[i] if i < len(data) else None
                    if payload is not None:
                        success = await self.event_manager.send_internal_event(str(event_id), payload)
                        if success:
                            sent_count += 1
            else:
                # Single data to all IDs or single ID
                for event_id in ids_to_send:
                    success = await self.event_manager.send_internal_event(str(event_id), data)
                    if success:
                        sent_count += 1
        else:
            print("Warning: EventManager not available for event sending")
        
        return (sent_count,)


class AwaitEventNode(BaseNode):
    """
    Sends events and awaits responses from all parallel workflows.
    Collects responses into an array with timeout handling.
    """
    CATEGORY = "Events"
    
    INPUT_SOCKETS = {
        "event_ids": {"type": SocketType.ANY, "is_dependency": True}, # CHANGE BACK TO NO DEPENDENCY AFTER TESTING
        "data": {"type": SocketType.ANY},
        "timeout": {"type": SocketType.NUMBER}
    }
    OUTPUT_SOCKETS = {
        "results": {"type": SocketType.ANY},
        "sent_count": {"type": SocketType.NUMBER}
    }
    
    event_id_widget = InputWidget(widget_type="TEXT", default="event_1")
    timeout_seconds = InputWidget(widget_type="NUMBER", default=30, properties={"min": 1, "max": 300})

    def load(self):
        pass

    async def execute(self, event_ids=None, data=None, timeout=None):
        """
        Send events and await responses with timeout handling.
        """
        # Determine event IDs
        if event_ids is not None:
            if isinstance(event_ids, (list, tuple)):
                ids_to_send = event_ids
            else:
                ids_to_send = [str(event_ids)]
        else:
            widget_id = self.widget_values.get('event_id_widget', self.event_id_widget.default)
            ids_to_send = [widget_id]
        
        # Determine timeout
        if timeout is not None:
            timeout_val = float(timeout)
        else:
            timeout_val = float(self.widget_values.get('timeout_seconds', self.timeout_seconds.default))
        
        # Prepare data
        if data is None:
            data = ""
        
        sent_count = 0
        results = []
        
        if self.event_manager:
            # Create awaitable ID for this node
            await_id = f"await_{self.node_info.get('id', 'unknown')}_{uuid.uuid4().hex[:8]}"
            print(f"AwaitEventNode: Created await_id '{await_id}' for collecting responses")
            
            # Send events with await ID for responses
            if isinstance(data, (list, tuple)) and len(ids_to_send) > 1:
                # Array data with array IDs
                for i, event_id in enumerate(ids_to_send):
                    payload = data[i] if i < len(data) else None
                    if payload is not None:
                        success = await self.event_manager.send_internal_event_with_await(
                            str(event_id), payload, await_id
                        )
                        if success:
                            sent_count += 1
            else:
                # Single data to all IDs
                for event_id in ids_to_send:
                    success = await self.event_manager.send_internal_event_with_await(
                        str(event_id), data, await_id
                    )
                    if success:
                        sent_count += 1
            
            # Await responses with timeout
            if sent_count > 0:
                print(f"AwaitEventNode: Waiting for {sent_count} responses for await_id '{await_id}'")
                try:
                    results = await asyncio.wait_for(
                        self.event_manager.collect_await_responses(await_id, sent_count),
                        timeout=timeout_val
                    )
                except asyncio.TimeoutError:
                    # Get the actual responses that were collected before timeout
                    partial_results = self.event_manager.await_responses.get(await_id, [])
                    timeout_msg = f"AwaitEventNode: Timeout after {timeout_val} seconds, collected {len(partial_results)} of {sent_count} responses"
                    print(timeout_msg)
                    # Use the partial results that were collected
                    results = partial_results
                    # Send warning to frontend
                    await self.send_message_to_client(MessageType.DEBUG, {"message": timeout_msg})
        else:
            print("Warning: EventManager not available for await functionality")
        
        # If only 1 result, output as single data instead of array
        if len(results) == 1:
            output_data = results[0]
        else:
            output_data = results
            
        print(f"AwaitEventNode: Returning results={output_data}, sent_count={sent_count}")
        return (output_data, sent_count)


class ReturnEventDataNode(BaseNode):
    """
    Returns data back to awaiting workflows.
    Used to complete the await/return cycle.
    """
    CATEGORY = "Events"
    
    INPUT_SOCKETS = {
        "return_data": {"type": SocketType.ANY},
        "await_id": {"type": SocketType.TEXT}
    }
    OUTPUT_SOCKETS = {
        "confirmed": {"type": SocketType.TEXT}
    }

    def load(self):
        pass

    async def execute(self, return_data=None, await_id=None):
        """
        Send return data back to specified awaiting workflow.
        """
        if await_id is None:
            return ("Error: No await_id provided",)
        
        if return_data is None:
            return_data = ""
        
        success = False
        if self.event_manager:
            success = await self.event_manager.send_await_response(str(await_id), return_data)
        else:
            print("Warning: EventManager not available for return data functionality")
        
        if success:
            return ("Data returned successfully",)
        else:
            return ("Failed to return data",)