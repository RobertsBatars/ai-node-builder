# nodes/event_nodes.py
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
from core.definitions import BaseNode, EventNode, SocketType, InputWidget

class WebhookNode(EventNode):
    """
    An event node that starts a simple web server and triggers a workflow
    when it receives a POST request to a specific path.
    """
    CATEGORY = "Events"

    # This node has no inputs, as it's a starting point.
    INPUT_SOCKETS = {}
    OUTPUT_SOCKETS = {
        "received_data": {"type": SocketType.TEXT}
    }

    port = InputWidget(widget_type="NUMBER", default=8181, properties={"min": 1024, "max": 65535})
    path = InputWidget(widget_type="TEXT", default="/webhook")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = None
        self.server_thread = None
        self.loop = None

    def load(self):
        """One-time setup."""
        self.loop = asyncio.get_running_loop()

    async def start_listening(self, trigger_workflow_callback):
        """Start the HTTP server in a separate thread."""
        port_val = int(self.widget_values.get('port', self.port.default))
        path_val = self.widget_values.get('path', self.path.default)

        # Ensure the loop is captured here in the main thread.
        if not self.loop:
            self.loop = asyncio.get_running_loop()

        # The handler needs a way to call the async callback in the main event loop.
        def make_handler(*args, **kwargs):
            # Pass the captured loop to the handler's constructor
            return WebhookRequestHandler(self.loop, trigger_workflow_callback, path_val, *args, **kwargs)

        try:
            self.server = HTTPServer(('', port_val), make_handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            log_msg = f"Webhook server started on http://localhost:{port_val}{path_val}"
            print(log_msg)
            # You might want to send this info to the client UI as well
            # await self.send_message_to_client(MessageType.LOG, {"message": log_msg})

        except Exception as e:
            error_msg = f"Failed to start webhook server: {e}"
            print(error_msg)
            # await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})


    async def stop_listening(self):
        """Stop the HTTP server."""
        if self.server:
            print("Shutting down webhook server...")
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()
            self.server = None
            self.server_thread = None
            print("Webhook server stopped.")

    def execute(self, *args, **kwargs):
        """
        This method is called when the workflow starts. It retrieves the
        payload injected by the engine and returns it on the output socket.
        """
        payload = self.memory.get('initial_payload', "")
        return (payload,)


class DisplayInputEventNode(EventNode):
    """
    An event node that listens for input from the display panel chat interface.
    This node enables chat-like interaction where users can type messages in the
    display panel and trigger workflows.
    """
    CATEGORY = "Events"
    
    INPUT_SOCKETS = {}
    OUTPUT_SOCKETS = {
        "user_input": {"type": SocketType.TEXT},
        "display_context": {"type": SocketType.ANY}
    }

    def load(self):
        """Initialize the event node."""
        self.trigger_callback = None
        
    async def start_listening(self, trigger_workflow_callback):
        """
        Store the callback function. The actual triggering happens when the
        server receives a 'display_input' WebSocket message.
        """
        self.trigger_callback = trigger_workflow_callback
        print(f"DisplayInputEventNode: Ready to receive display panel inputs.")
        
    async def stop_listening(self):
        """Clean up the listener."""
        self.trigger_callback = None
        print("DisplayInputEventNode: Stopped listening for display panel inputs.")
        
    def execute(self, *args, **kwargs):
        """
        Called when the workflow starts from display panel input.
        Returns the user input and current display context.
        """
        payload = self.memory.get('initial_payload', "")
        # Get current display context from global state
        display_context = self.global_state.get('display_context', [])
        return (payload, display_context)


class WebhookRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, loop, trigger_callback, configured_path, *args, **kwargs):
        self.loop = loop
        self.trigger_callback = trigger_callback
        self.configured_path = configured_path
        super().__init__(*args, **kwargs)

    def do_POST(self):
        if self.path == self.configured_path:
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Decode the payload to a string to be passed to the workflow.
                payload_str = post_data.decode('utf-8')
                
                # Schedule the async callback to be run in the main event loop,
                # passing the payload to it.
                future = asyncio.run_coroutine_threadsafe(self.trigger_callback(payload_str), self.loop)
                # Optionally, you can wait for the result, but for a fire-and-forget trigger, it's not necessary.
                # future.result() 

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status": "ok", "message": "Workflow triggered."}')
            except Exception as e:
                print(f"Error in WebhookRequestHandler: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def log_message(self, format, *args):
        # Suppress the default logging to keep the console clean
        return
