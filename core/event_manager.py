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
                run_id = f"event_{uuid.uuid4()}"
                print(f"Event received from node {start_node_id}. Triggering workflow with run_id: {run_id}")
                
                task = asyncio.create_task(
                    self.engine.run_workflow(
                        graph_data=current_graph_data, 
                        start_node_id=start_node_id, 
                        websocket=self.websocket, 
                        run_id=run_id,
                        global_state=self.global_state,
                        initial_payload=payload
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
        print("Event Manager: All listeners stopped.")

