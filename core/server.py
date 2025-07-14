# core/server.py
# This file sets up the FastAPI web server and its endpoints.

import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from core.engine import NodeEngine

# Initialize the main FastAPI application and the Node Engine
app = FastAPI()
engine = NodeEngine()

@app.get("/")
async def get_frontend():
    """Serves the main HTML file for the frontend."""
    return FileResponse('web/index.html')

@app.get("/get_nodes")
async def get_nodes():
    """Provides the UI blueprint for all available nodes."""
    blueprints_json_string = engine.generate_ui_blueprints()
    # The JSON string is already formatted, but we need to parse it back to a Python object
    # for JSONResponse to work correctly and set the right content-type header.
    blueprints_object = json.loads(blueprints_json_string)
    return JSONResponse(content=blueprints_object)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles the real-time communication with the frontend."""
    await websocket.accept()
    try:
        while True:
            # Wait for a message from the frontend
            data = await websocket.receive_json()
            
            # Check if it's a 'run' command
            if data.get("action") == "run":
                graph_data = data.get("graph")
                start_node_id = data.get("start_node_id")
                if start_node_id is None:
                    await websocket.send_text("Error: No start node selected.")
                    continue
                # Pass the graph to the engine for execution
                await engine.run_workflow(graph_data, str(start_node_id), websocket)

    except WebSocketDisconnect:
        print("Client disconnected")
