# core/event_manager.py
import asyncio
import uuid
from collections import defaultdict

class EventManager:
    def __init__(self, engine, websocket, global_state):
        self.engine = engine
        self.websocket = websocket
        self.global_state = global_state
        self.listening_nodes = {} # {node_id: node_instance}
        self.active_listeners = {} # {node_id: asyncio.Task}
        
        # Internal event communication system
        self.internal_listeners = {} # {event_id: callback_function}
        self.await_responses = defaultdict(list) # {await_id: [response1, response2, ...]}
        self.await_waiters = {} # {await_id: asyncio.Event}

    async def start_listeners(self, event_nodes, graph_data, active_workflows_ref, client_tasks_ref):
        """
        Starts listening for events on all provided event nodes.
        """
        print(f"Event Manager: Starting listeners for {len(event_nodes)} event node(s).")
        
        def on_task_done(run_id, ws):
            """Callback to clean up a finished task."""
            task = active_workflows_ref.pop(run_id, None)
            if task:
                print(f"Event-triggered task {run_id} finished and removed from global registry.")
            if ws in client_tasks_ref and run_id in client_tasks_ref:
                client_tasks_ref.remove(run_id)
                print(f"Event-triggered task {run_id} removed from client {ws.client}.")

        for node in event_nodes:
            node_id = str(node.node_info['id'])
            if node_id in self.active_listeners:
                print(f"Warning: Listener for node {node_id} is already active.")
                continue

            self.listening_nodes[node_id] = node
            
            # Define the callback that the event node will use to trigger a workflow
            async def trigger_callback(payload, start_node_id=node_id, current_graph_data=graph_data):
                # Special handling for DisplayInputEventNode to use more descriptive run_id
                if node.__class__.__name__ == "DisplayInputEventNode":
                    run_id = f"display_input_{uuid.uuid4().hex[:8]}"
                else:
                    run_id = f"event_{uuid.uuid4()}"
                print(f"Event received from node {start_node_id} ({node.__class__.__name__}). Triggering workflow with run_id: {run_id}")
                
                task = asyncio.create_task(
                    self.engine.run_workflow(
                        graph_data=current_graph_data, 
                        start_node_id=start_node_id, 
                        websocket=self.websocket, 
                        run_id=run_id,
                        global_state=self.global_state,
                        initial_payload=payload,
                        event_manager=self
                    )
                )
                active_workflows_ref[run_id] = task
                client_tasks_ref.add(run_id)
                task.add_done_callback(lambda t: on_task_done(run_id, self.websocket))

            # Start the node's listener and store the task
            task = asyncio.create_task(node.start_listening(trigger_callback))
            self.active_listeners[node_id] = task
            print(f"Event Manager: Listener for node {node_id} ({node.__class__.__name__}) is active.")

    async def stop_listeners(self):
        """
        Stops all active event listeners.
        """
        print(f"Event Manager: Stopping {len(self.active_listeners)} active listener(s).")
        for node_id, task in self.active_listeners.items():
            task.cancel()
            node = self.listening_nodes.get(node_id)
            if node:
                # stop_listening might be async, so we should await it.
                await asyncio.create_task(node.stop_listening())
        
        self.active_listeners.clear()
        self.listening_nodes.clear()
        
        # Clear internal event system
        self.internal_listeners.clear()
        self.await_responses.clear()
        self.await_waiters.clear()
        print("Event Manager: All listeners stopped.")

    # Internal Event Communication Methods
    
    async def register_internal_listener(self, event_id, callback):
        """
        Register a callback function to listen for internal events with specific ID.
        """
        self.internal_listeners[event_id] = callback
        print(f"EventManager: Registered internal listener for event_id '{event_id}'")

    async def unregister_internal_listener(self, event_id):
        """
        Unregister an internal event listener.
        """
        if event_id in self.internal_listeners:
            del self.internal_listeners[event_id]
            print(f"EventManager: Unregistered internal listener for event_id '{event_id}'")

    async def send_internal_event(self, event_id, payload):
        """
        Send an internal event to registered listeners.
        Returns True if event was sent, False if no listener found.
        """
        if event_id in self.internal_listeners:
            callback = self.internal_listeners[event_id]
            try:
                await callback(payload)
                print(f"EventManager: Sent internal event to '{event_id}' with payload: {payload}")
                return True
            except Exception as e:
                print(f"EventManager: Error sending internal event to '{event_id}': {e}")
                return False
        else:
            print(f"EventManager: No listener found for event_id '{event_id}'")
            return False

    async def send_internal_event_with_await(self, event_id, payload, await_id):
        """
        Send an internal event and prepare to collect responses for await functionality.
        """
        # Initialize await tracking
        if await_id not in self.await_waiters:
            self.await_waiters[await_id] = asyncio.Event()
        
        # Send the event with await_id embedded in payload
        enhanced_payload = {
            'data': payload,
            'await_id': await_id
        }
        
        return await self.send_internal_event(event_id, enhanced_payload)

    async def send_await_response(self, await_id, response_data):
        """
        Send a response back to an awaiting workflow.
        """
        if await_id in self.await_waiters:
            self.await_responses[await_id].append(response_data)
            print(f"EventManager: Added response to await_id '{await_id}': {response_data}")
            
            # Notify waiters that a response is available
            self.await_waiters[await_id].set()
            return True
        else:
            print(f"EventManager: No awaiting workflow found for await_id '{await_id}'")
            return False

    async def collect_await_responses(self, await_id, expected_count):
        """
        Collect responses for an await operation. Returns when expected_count is reached.
        """
        if await_id not in self.await_waiters:
            return []
        
        # Start by collecting any responses that already exist
        responses = self.await_responses[await_id].copy() if await_id in self.await_responses else []
        print(f"EventManager: collect_await_responses for '{await_id}': starting with {len(responses)} existing responses")
        
        while len(responses) < expected_count:
            # If we already have enough responses, break immediately
            if len(responses) >= expected_count:
                break
                
            # Wait for new responses
            await self.await_waiters[await_id].wait()
            
            # Collect available responses
            available_responses = self.await_responses[await_id]
            if len(available_responses) > len(responses):
                responses = available_responses.copy()
            
            # Reset the event for next wait cycle
            self.await_waiters[await_id].clear()
        
        # Clean up
        if await_id in self.await_waiters:
            del self.await_waiters[await_id]
        if await_id in self.await_responses:
            del self.await_responses[await_id]
        
        print(f"EventManager: Collected {len(responses)} responses for await_id '{await_id}'")
        return responses[:expected_count]  # Return only the expected count

