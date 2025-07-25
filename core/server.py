# core/server.py
# This file sets up the FastAPI web server and its endpoints.

import json
import asyncio
import uuid
from collections import defaultdict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

from core.engine import NodeEngine
from core.event_manager import EventManager
from core.definitions import EventNode

# Initialize the main FastAPI application and the Node Engine
app = FastAPI()
engine = NodeEngine()

# --- Global State Management ---
GLOBAL_DISPLAY_STATE = {
    "display_context": [],
    "graph_hash": None,
    "initial_graph_hash": None,
    "previous_graph_hash": None
}
ACTIVE_WEBSOCKET = None

# {run_id: asyncio.Task} - Keeps track of all running workflow tasks globally.
active_workflows = {} 
# {websocket: {run_id_1, run_id_2, ...}} - Maps each client to their set of active run_ids.
client_tasks = defaultdict(set)
# {websocket: EventManager} - Maps each client to their dedicated EventManager instance.
event_managers = {}


@app.get("/")
async def get_frontend():
    """Serves the main HTML file for the frontend."""
    return FileResponse('web/index.html')

@app.get("/get_nodes")
async def get_nodes():
    """Provides the UI blueprint for all available nodes."""
    blueprints_json_string = engine.generate_ui_blueprints()
    blueprints_object = json.loads(blueprints_json_string)
    return JSONResponse(content=blueprints_object)

async def broadcast_to_frontend(message: dict):
    if ACTIVE_WEBSOCKET:
        try:
            await ACTIVE_WEBSOCKET.send_json(message)
        except Exception as e:
            print(f"Failed to broadcast message: {e}")

# Set the callback on the engine instance
engine.set_broadcast_callback(broadcast_to_frontend)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles the real-time communication with the frontend."""
    global ACTIVE_WEBSOCKET
    await websocket.accept()
    ACTIVE_WEBSOCKET = websocket
    print("Frontend connected. Active WebSocket set.")
    
    # Create and store an EventManager for this client session
    # Pass the global state to the event manager so it can pass it to event-triggered workflows
    event_managers[websocket] = EventManager(engine, websocket, GLOBAL_DISPLAY_STATE)

    def on_task_done(run_id, ws):
        """Callback to clean up a finished task."""
        task = active_workflows.pop(run_id, None)
        if task:
            print(f"Task {run_id} finished and removed from global registry.")
        if ws in client_tasks and run_id in client_tasks[ws]:
            client_tasks[ws].remove(run_id)
            print(f"Task {run_id} removed from client {ws.client}.")

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            graph_data = data.get("graph")

            if action == "get_initial_context":
                await websocket.send_json({
                    "type": "display_context_state",
                    "payload": GLOBAL_DISPLAY_STATE
                })

            elif action == "load_display_context":
                loaded_data = data.get("payload", {})
                GLOBAL_DISPLAY_STATE["display_context"] = loaded_data.get("context", [])
                GLOBAL_DISPLAY_STATE["graph_hash"] = loaded_data.get("graph_hash")
                # Set the initial_graph_hash when loading a saved context with a hash
                if loaded_data.get("graph_hash"):
                    GLOBAL_DISPLAY_STATE["initial_graph_hash"] = loaded_data.get("graph_hash")
                await broadcast_to_frontend({
                    "type": "display_context_state",
                    "payload": GLOBAL_DISPLAY_STATE
                })

            elif action == "clear_display_context":
                GLOBAL_DISPLAY_STATE["display_context"].clear()
                # Reset the hash and warning flags as well
                GLOBAL_DISPLAY_STATE["initial_graph_hash"] = None
                GLOBAL_DISPLAY_STATE["previous_graph_hash"] = None
                GLOBAL_DISPLAY_STATE.pop("warning_issued", None)
                GLOBAL_DISPLAY_STATE["graph_hash"] = None
                await broadcast_to_frontend({"type": "display_context_cleared"})

            elif action == "run":
                run_id = "frontend_run"
                # If a frontend-initiated workflow is already running, cancel it before starting a new one.
                if websocket in client_tasks and run_id in client_tasks[websocket]:
                    if run_id in active_workflows:
                        active_workflows[run_id].cancel()

                start_node_id = data.get("start_node_id")
                if start_node_id is None:
                    await websocket.send_text(json.dumps({"type": "error", "message": "No start node selected."}))
                    continue

                task = asyncio.create_task(engine.run_workflow(graph_data, str(start_node_id), websocket, run_id, GLOBAL_DISPLAY_STATE))
                active_workflows[run_id] = task
                client_tasks[websocket].add(run_id)
                task.add_done_callback(lambda t: on_task_done(run_id, websocket))

            elif action == "stop":
                if websocket in client_tasks:
                    await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "all", "message": "Stopping all workflows for this client..."}))
                    # Create a copy of the set to iterate over, as it will be modified
                    for run_id in list(client_tasks[websocket]):
                        if run_id in active_workflows:
                            active_workflows[run_id].cancel()
                    # The on_task_done callback will handle cleanup
                else:
                    await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "none", "message": "No workflows are currently running."}))

            elif action == "start_listening":
                if not graph_data:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Graph data is required to start listening."}))
                    continue
                
                # Instantiate all nodes to find the event nodes
                all_nodes = [
                    engine.node_classes[n['type'].split('/')[-1]](engine, n, {}, None, GLOBAL_DISPLAY_STATE)
                    for n in graph_data['nodes'] if n['type'].split('/')[-1] in engine.node_classes
                ]
                event_nodes = [node for node in all_nodes if isinstance(node, EventNode)]

                if not event_nodes:
                    await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "events", "message": "No event nodes found in the graph."}))
                    continue

                manager = event_managers[websocket]
                # The manager's start_listeners now needs to handle the task creation and tracking
                await manager.start_listeners(event_nodes, graph_data, active_workflows, client_tasks[websocket])
                await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "events", "message": "Now listening for events."}))


            elif action == "stop_listening":
                manager = event_managers.get(websocket)
                if manager:
                    await manager.stop_listeners()
                await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "events", "message": "Stopped listening for events."}))


    except WebSocketDisconnect:
        print(f"Client {websocket.client} disconnected.")
        ACTIVE_WEBSOCKET = None
        # If the client disconnects, cancel all their running tasks
        if websocket in client_tasks:
            for run_id in client_tasks[websocket]:
                if run_id in active_workflows:
                    active_workflows[run_id].cancel()
            del client_tasks[websocket]
        
        # Stop any active listeners for the disconnected client
        manager = event_managers.pop(websocket, None)
        if manager:
            await manager.stop_listeners()
        
        print(f"All tasks and listeners for client {websocket.client} have been stopped.")
