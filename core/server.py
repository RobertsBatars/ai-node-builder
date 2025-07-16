# core/server.py
# This file sets up the FastAPI web server and its endpoints.

import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from core.engine import NodeEngine

# Initialize the main FastAPI application and the Node Engine
app = FastAPI()
engine = NodeEngine()

# A dictionary to keep track of the running workflow task for each client
active_workflows = {}

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles the real-time communication with the frontend."""
    await websocket.accept()

    def on_task_done(task):
        """Callback to remove the task from the active workflows."""
        if websocket in active_workflows:
            del active_workflows[websocket]
        print(f"Task for client {websocket.client} finished and removed.")

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "run":
                # If a workflow is already running for this client, stop it first.
                if websocket in active_workflows:
                    active_workflows[websocket].cancel()
                    del active_workflows[websocket]

                graph_data = data.get("graph")
                start_node_id = data.get("start_node_id")
                if start_node_id is None:
                    await websocket.send_text("Error: No start node selected.")
                    continue

                # Create a new task for the workflow and store it
                task = asyncio.create_task(engine.run_workflow(graph_data, str(start_node_id), websocket))
                task.add_done_callback(on_task_done)
                active_workflows[websocket] = task

            elif action == "stop":
                if websocket in active_workflows:
                    await websocket.send_text("Engine: Stopping workflow...")
                    active_workflows[websocket].cancel()
                    # The task will be removed by the on_task_done callback
                else:
                    await websocket.send_text("Engine: No workflow is currently running.")

    except WebSocketDisconnect:
        # If the client disconnects, cancel their running task
        if websocket in active_workflows:
            active_workflows[websocket].cancel()
            del active_workflows[websocket]
        print(f"Client {websocket.client} disconnected. Any running workflow has been stopped.")
