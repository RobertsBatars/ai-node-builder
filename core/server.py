# core/server.py
# This file sets up the FastAPI web server and its endpoints.

import json
import asyncio
import uuid
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

try:
    import yaml
except ImportError:
    yaml = None

from core.engine import NodeEngine
from core.event_manager import EventManager
from core.definitions import EventNode
from core.file_utils import ServableFileManager

# Initialize the main FastAPI application and the Node Engine
app = FastAPI()
engine = NodeEngine()

# Load default settings from file
def load_default_settings():
    """Load default settings from default_settings.json"""
    import os
    default_file = "default_settings.json"
    
    if not os.path.exists(default_file):
        raise FileNotFoundError(f"Required file '{default_file}' not found. Please create this file with default settings.")
    
    try:
        with open(default_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in '{default_file}': {e}")
    except Exception as e:
        raise RuntimeError(f"Could not load '{default_file}': {e}")

DEFAULT_SETTINGS = load_default_settings()

# Initialize file manager and create servable directory
file_manager = ServableFileManager()

# Mount static files for servable directory
app.mount("/servable", StaticFiles(directory="servable"), name="servable")

# --- Global State Management ---
GLOBAL_DISPLAY_STATE = {
    "display_context": [],
    "graph_hash": None,
    "initial_graph_hash": None,
    "previous_graph_hash": None,
    "filter_warnings": False  # Frontend filter preference
}
ACTIVE_WEBSOCKET = None

def get_filtered_display_context():
    """Returns display context filtered based on current frontend filter preferences."""
    context = GLOBAL_DISPLAY_STATE.get('display_context', [])
    if GLOBAL_DISPLAY_STATE.get('filter_warnings', False):
        # Filter out warnings if frontend filter is enabled
        context = [msg for msg in context if msg.get('content_type') != 'warning']
    return context

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

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...), node_id: str = Form(default="")):
    """Handle image uploads from file upload widgets."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            return JSONResponse({"success": False, "error": "Invalid file type. Please upload an image."})
        
        # Validate file size (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            return JSONResponse({"success": False, "error": "File size must be less than 10MB."})
        
        # Save to servable folder
        filename = file.filename or "unnamed_file"
        servable_url = file_manager.save_file(content, filename=filename, node_id=node_id)
        
        return JSONResponse({
            "success": True,
            "servable_url": servable_url,
            "filename": file.filename,
            "size": len(content),
            "size_human": file_manager._format_file_size(len(content))
        })
        
    except Exception as e:
        return JSONResponse({"success": False, "error": f"Upload failed: {str(e)}"})

@app.get("/servable_files")
async def get_servable_files():
    """Get list of all servable files with metadata."""
    try:
        files = file_manager.list_files()
        return JSONResponse({
            "success": True,
            "files": files,
            "count": len(files),
            "total_size": sum(f['size'] for f in files)
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": f"Failed to list files: {str(e)}"})

@app.delete("/servable_files/{filename}")
async def delete_servable_file(filename: str):
    """Delete a specific servable file."""
    try:
        success = file_manager.delete_file(filename)
        if success:
            return JSONResponse({"success": True, "message": f"File {filename} deleted successfully."})
        else:
            return JSONResponse({"success": False, "error": f"File {filename} not found."})
    except Exception as e:
        return JSONResponse({"success": False, "error": f"Failed to delete file: {str(e)}"})

@app.get("/servable_files/{filename}/info")
async def get_servable_file_info(filename: str):
    """Get detailed info for a specific servable file."""
    try:
        file_info = file_manager.get_file_info(filename)
        if file_info:
            return JSONResponse({"success": True, "file": file_info})
        else:
            return JSONResponse({"success": False, "error": f"File {filename} not found."})
    except Exception as e:
        return JSONResponse({"success": False, "error": f"Failed to get file info: {str(e)}"})

@app.get("/settings")
async def get_settings():
    """Get application settings."""
    try:
        import os
        settings_file = "settings.json"
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            # Use default settings
            settings = DEFAULT_SETTINGS.copy()
        return JSONResponse({"success": True, "settings": settings})
    except Exception as e:
        return JSONResponse({"success": False, "error": f"Failed to load settings: {str(e)}"})

@app.post("/settings")
async def update_settings(settings_data: dict):
    """Update application settings."""
    try:
        import os
        settings_file = "settings.json"
        
        # Load existing settings or create default
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                current_settings = json.load(f)
        else:
            current_settings = DEFAULT_SETTINGS.copy()
        
        # Deep merge the new settings
        def deep_merge(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        
        deep_merge(current_settings, settings_data)
        
        # Save updated settings
        with open(settings_file, 'w') as f:
            json.dump(current_settings, f, indent=2)
        
        return JSONResponse({"success": True, "settings": current_settings})
    except Exception as e:
        return JSONResponse({"success": False, "error": f"Failed to save settings: {str(e)}"})

@app.get("/settings/defaults")
async def get_default_settings():
    """Get default application settings."""
    return JSONResponse({"success": True, "defaults": DEFAULT_SETTINGS})

# --- Documentation System Endpoints ---

@app.get("/docs/images/{path:path}")
async def serve_docs_images(path: str):
    """Serve documentation images."""
    image_file = Path("docs/images") / path
    if image_file.exists() and image_file.is_file():
        return FileResponse(image_file)
    else:
        raise HTTPException(404, "Image not found")

@app.get("/docs/{path:path}")
async def serve_docs(path: str = ""):
    """Serve the documentation web app."""
    if not path or path.endswith('/'):
        path += "index.html"
    
    docs_file = Path("docs/app") / path
    if docs_file.exists():
        return FileResponse(docs_file)
    else:
        return FileResponse("docs/app/index.html")  # SPA routing

@app.get("/api/docs/registry")
async def get_documentation_registry():
    """Auto-generate registry by scanning docs/nodes/ directory."""
    docs_path = Path("docs/nodes")
    registry = {
        "categories": {},
        "nodes": {},
        "last_updated": datetime.now().isoformat()
    }
    
    if not docs_path.exists():
        return registry
    
    # Scan each category folder
    for category_dir in docs_path.iterdir():
        if category_dir.is_dir():
            category_name = category_dir.name
            registry["categories"][category_name] = []
            
            # Scan for .md files in category
            for doc_file in category_dir.glob("*.md"):
                node_name = doc_file.stem
                
                # Parse frontmatter for metadata
                metadata = parse_markdown_frontmatter(doc_file)
                
                node_info = {
                    "name": node_name,
                    "title": metadata.get("title", node_name),
                    "category": category_name,
                    "file_path": str(doc_file.relative_to("docs")),
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", []),
                    "complexity": metadata.get("complexity", "beginner")
                }
                
                registry["categories"][category_name].append(node_info)
                registry["nodes"][node_name] = node_info
    
    return registry

@app.get("/api/docs/content/{node_name}")
async def get_node_documentation(node_name: str):
    """Get specific node documentation content."""
    registry_data = await get_documentation_registry()
    if node_name not in registry_data["nodes"]:
        raise HTTPException(404, "Documentation not found")
    
    node_info = registry_data["nodes"][node_name]
    doc_path = Path("docs") / node_info["file_path"]
    
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Strip frontmatter from content before returning
        content = strip_frontmatter_from_content(raw_content)
        return {"content": content, "metadata": node_info}
    except FileNotFoundError:
        raise HTTPException(404, f"Documentation file not found: {doc_path}")
    except Exception as e:
        raise HTTPException(500, f"Error reading documentation: {str(e)}")

@app.get("/api/docs/guide/{guide_name}")
async def get_guide_documentation(guide_name: str):
    """Get specific guide documentation content."""
    # Map guide names to files
    guide_mapping = {
        "node-creation": "node_creation_guide.md",
        "node-documentation": "node_documentation_guide.md",
        "devdocs": "devdocs.md"
    }
    
    if guide_name not in guide_mapping:
        raise HTTPException(404, "Guide not found")
    
    guide_file = guide_mapping[guide_name]
    guide_path = Path("docs") / "guides" / guide_file
    
    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Extract metadata if present, otherwise create basic metadata
        metadata = parse_markdown_frontmatter(guide_path)
        if not metadata:
            metadata = {
                "title": guide_name.replace("-", " ").title(),
                "type": "guide",
                "category": "guides"
            }
        else:
            # Ensure guides always have the "guides" category
            metadata["category"] = "guides"
            metadata["type"] = "guide"
        
        # Strip frontmatter from content before returning
        content = strip_frontmatter_from_content(raw_content)
        return {"content": content, "metadata": metadata}
    except FileNotFoundError:
        raise HTTPException(404, f"Guide file not found: {guide_path}")
    except Exception as e:
        raise HTTPException(500, f"Error reading guide: {str(e)}")

def parse_markdown_frontmatter(file_path):
    """Extract YAML frontmatter from markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('---\n'):
            try:
                parts = content.split('---\n', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    if yaml:
                        return yaml.safe_load(frontmatter)
                    else:
                        # Fallback if pyyaml is not available
                        print("Warning: pyyaml not installed. Frontmatter parsing disabled.")
                        return {}
                return {}
            except ValueError:
                return {}
        return {}
    except Exception as e:
        print(f"Error parsing frontmatter for {file_path}: {e}")
        return {}

def strip_frontmatter_from_content(content):
    """Remove YAML frontmatter from markdown content."""
    if content.startswith('---\n'):
        try:
            parts = content.split('---\n', 2)
            if len(parts) >= 3:
                return parts[2]  # Return content after second ---
        except ValueError:
            pass
    return content

# --- End Documentation System Endpoints ---

async def broadcast_to_frontend(message: dict):
    if ACTIVE_WEBSOCKET:
        try:
            await ACTIVE_WEBSOCKET.send_json(message)
        except Exception as e:
            print(f"Failed to broadcast message: {e}")

# Set the callback on the engine instance
engine.set_broadcast_callback(broadcast_to_frontend)

async def check_and_warn_workflow_change(global_state, current_hash):
    """Check if workflow has changed since context was started and add warning if needed."""
    is_context_populated = bool(global_state.get("display_context"))
    initial_hash = global_state.get("initial_graph_hash")
    
    # Set the initial hash when the context first becomes populated
    # We store the hash from the PREVIOUS run, not the current one
    if is_context_populated and not initial_hash:
        # Check if we have a previous hash stored
        previous_hash = global_state.get("previous_graph_hash")
        if previous_hash:
            global_state['initial_graph_hash'] = previous_hash
            initial_hash = previous_hash
    
    # If the context is populated and we have an initial hash, compare it with current hash
    if is_context_populated and initial_hash and current_hash != initial_hash:
        warning_msg = {
            "node_id": None,
            "node_title": "Engine Warning",
            "content_type": "warning",
            "data": "Workflow has changed since the context was started. Node filtering may be unreliable."
        }
        global_state['display_context'].append(warning_msg)
        await broadcast_to_frontend({
            "source": "node",
            "type": "display",
            "payload": {"data": warning_msg}
        })
        return True
    return False


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

                # Check for workflow changes and warn user if needed
                current_hash = engine._generate_graph_hash(graph_data)
                await check_and_warn_workflow_change(GLOBAL_DISPLAY_STATE, current_hash)

                event_manager = event_managers[websocket]
                task = asyncio.create_task(engine.run_workflow(graph_data, str(start_node_id), websocket, run_id, GLOBAL_DISPLAY_STATE, event_manager=event_manager))
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
                
                # Check for workflow changes and warn user if needed
                current_hash = engine._generate_graph_hash(graph_data)
                await check_and_warn_workflow_change(GLOBAL_DISPLAY_STATE, current_hash)
                
                # Instantiate all nodes to find the event nodes
                manager = event_managers[websocket]
                all_nodes = [
                    engine.node_classes[n['type'].split('/')[-1]](engine, n, {}, None, GLOBAL_DISPLAY_STATE, manager)
                    for n in graph_data['nodes'] if n['type'].split('/')[-1] in engine.node_classes
                ]
                event_nodes = [node for node in all_nodes if isinstance(node, EventNode)]

                if not event_nodes:
                    await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "events", "message": "No event nodes found in the graph."}))
                    continue

                # The manager's start_listeners now needs to handle the task creation and tracking
                await manager.start_listeners(event_nodes, graph_data, active_workflows, client_tasks[websocket])
                await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "events", "message": "Now listening for events."}))


            elif action == "stop_listening":
                manager = event_managers.get(websocket)
                if manager:
                    await manager.stop_listeners()
                await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "events", "message": "Stopped listening for events."}))

            elif action == "display_input":
                user_input = data.get("input", "")
                filter_warnings = data.get("filter_warnings", False)
                if not user_input.strip():
                    continue
                
                # Update global filter preference
                GLOBAL_DISPLAY_STATE['filter_warnings'] = filter_warnings
                
                # Add user message to global display context
                user_message_entry = {
                    "node_id": None,  # No specific node ID for user messages
                    "node_title": "User",
                    "content_type": "text",
                    "data": user_input,
                    "timestamp": datetime.now().isoformat()
                }
                GLOBAL_DISPLAY_STATE['display_context'].append(user_message_entry)
                
                # Sync updated context back to frontend
                await broadcast_to_frontend({
                    "type": "display_context_state",
                    "payload": GLOBAL_DISPLAY_STATE
                })
                
                # Find DisplayInputEventNode in the current event listeners
                manager = event_managers.get(websocket)
                if manager:
                    display_input_node = None
                    for node_id, node in manager.listening_nodes.items():
                        if node.__class__.__name__ == "DisplayInputEventNode":
                            display_input_node = node
                            break
                    
                    if display_input_node and display_input_node.trigger_callback:
                        # Pass user input to the triggered workflow (simplified payload)
                        payload_data = {
                            "user_input": user_input
                        }
                        await display_input_node.trigger_callback(payload_data)
                    else:
                        await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "display_input", "message": "No active DisplayInputEventNode found or event listening is not enabled."}))
                else:
                    await websocket.send_text(json.dumps({"type": "engine_log", "run_id": "display_input", "message": "Event manager not found. Please start event listening first."}))


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
