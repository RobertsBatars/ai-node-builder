# core/server.py
# This file sets up the FastAPI web server and its endpoints.

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
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
    return engine.generate_ui_blueprints()

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
                # Pass the graph to the engine for execution
                await engine.run_workflow(graph_data, websocket)

    except WebSocketDisconnect:
        print("Client disconnected")
