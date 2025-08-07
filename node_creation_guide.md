# Node Creation Guide

This guide provides a comprehensive walkthrough for creating custom nodes for the AI Node Builder application. By following these steps, you can create any kind of node, from simple inputs to complex processing units.

## 1. Core Concepts

Before creating a node, it's important to understand the fundamental building blocks of the system.

### The `BaseNode` Class

Every node in the application is a Python class that inherits from `core.definitions.BaseNode`. This base class provides the core structure and ensures that the node engine can correctly discover and use your custom node.

### Node Discovery

The engine automatically discovers any class that inherits from `BaseNode` located in any file within the `nodes/` directory. You simply need to create a new Python file (e.g., `my_custom_nodes.py`) inside the `nodes/` directory and define your node classes there. The engine will handle the rest.

### Node Memory: The `self.memory` Attribute

Each node instance has a `self.memory` attribute, which is a Python dictionary. This memory is unique to that specific node within a single workflow run. It is created when the workflow starts and destroyed when it finishes.

You can use `self.memory` to store any information you want to persist across multiple executions of the same node. This is the key to creating stateful nodes, such as counters or accumulators.

```python
# Inside your execute method:
# Get a value from memory, defaulting to 0 if it's not there.
current_count = self.memory.get('count', 0)
# Store an updated value back into memory.
self.memory['count'] = current_count + 1
```

### Global State: The `self.global_state` Attribute

In addition to the run-specific `self.memory`, every node instance also has access to `self.global_state`. This is a dictionary that is shared across **all workflows and all nodes** and persists for the entire lifetime of the server.

It is primarily used for the **Display Panel** context. You can read from it to get the current display history or write to it to add new messages.

**Use `self.global_state` with caution.** Since it is shared everywhere, changes made by one workflow will be immediately visible to all others.

```python
# Get a (deep) copy of the entire display history
display_history = copy.deepcopy(self.global_state.get('display_context', []))

# Add a new message to the global display context
# Note: This is typically handled by the DisplayOutputNode.
new_message = {"node_id": self.node_info.get('id'), "content_type": "text", "data": "Hello from my node!"}
self.global_state['display_context'].append(new_message)
```

### Sockets: Inputs and Outputs

Sockets are the connection points on a node for data to flow in and out.

-   **`INPUT_SOCKETS`**: A dictionary defining the inputs of the node.
-   **`OUTPUT_SOCKETS`**: A dictionary defining the outputs of the node.

Each socket is defined with a name and a dictionary of properties, the most important being `type`, which uses the `SocketType` enum (`TEXT`, `NUMBER`, `IMAGE`, `ANY`). Sockets can also be configured as dynamic arrays to accept a variable number of inputs.

### Data Flow: Push vs. Pull (Dependency)

The engine supports two models for how a node receives data. Understanding this is key to creating powerful and predictable nodes.

1.  **Push (Default)**: This is the standard data flow. It follows the visual arrows in the graph. When an upstream node (Node A) completes its `execute` method, it "pushes" its result to the input socket of the next node in the chain (Node B). Node B is triggered *by the arrival of data*. Most nodes use this model.

2.  **Pull (Dependency)**: This is a special mechanism for fetching data from nodes that are **not** part of the main execution chain. You should use this when your node needs data from another node that would not otherwise be triggered.

    By adding `"is_dependency": True` to an input socket's definition, you are telling the engine: "Before you run my `execute` method, go and actively run the node connected to this input and *pull* the result."

    **When to use `is_dependency: True`:**
    -   When you need to retrieve a configuration or a static value from an Input Node (like `TextNode` or `NumberNode`) that is not connected to the starting node of the workflow.
    -   When your node requires multiple inputs to be present *at the same time* before it can run, and those inputs come from separate, independent branches of the graph. The `AddNode` is a perfect example: it cannot execute with just one number, so it pulls both inputs to ensure they are ready simultaneously.

    In short: if the data won't be "pushed" to your node as part of the normal flow, you need to "pull" it.

3.  **Do Not Wait (For Loops)**: This is the key to creating loops and dynamic behavior. You mark an input socket with `"do_not_wait": True`. This tells the engine: "Do not wait for this input. Execute me as soon as my other, standard inputs are ready. If data arrives at this input, it can trigger an execution by itself." This is perfect for a "loop in" or "update" signal.

#### Handling Conflicting Flags

What happens if you set both `is_dependency: True` and `do_not_wait: True` on the same input?

**`do_not_wait` always wins.** The engine will ignore the `is_dependency` flag. The input will not be pulled, and the engine will not wait for it. This ensures that the looping behavior is predictable.

### Widgets

Widgets are UI elements that appear on the node in the frontend, allowing users to input static values. They are defined as class attributes using the `InputWidget` class from `core.definitions`. 

For a complete list of available widgets and their properties, see [section 5](#5-available-widgets-and-properties).

---

## 2. Step-by-Step Tutorial: Creating a "Concatenate" Node

Let's create a new node called `ConcatenateNode`. This node will take two text inputs and join them together with a separator defined by a widget.

### Step 1: Create a New File

Inside the `nodes/` directory, create a new file named `custom_nodes.py`.

### Step 2: Define the Node Class

In `custom_nodes.py`, start by importing the necessary classes and defining your new node class.

```python
# nodes/custom_nodes.py
from core.definitions import BaseNode, SocketType, InputWidget

class ConcatenateNode(BaseNode):
    # --- Metadata ---
    # This is the category under which the node will appear in the UI's right-click menu.
    CATEGORY = "Text"

    # --- Sockets ---
    # Define the inputs the node will accept.
    # These are standard "push" inputs. The node will wait for data to be sent to them.
    INPUT_SOCKETS = {
        "text_a": {"type": SocketType.TEXT},
        "text_b": {"type": SocketType.TEXT}
    }

    # Define the outputs the node will produce.
    OUTPUT_SOCKETS = {
        "full_text": {"type": SocketType.TEXT}
    }

    # --- Widgets ---
    # Define a widget to get a static value from the user.
    # This will appear on the node in the UI.
    separator = InputWidget(widget_type="TEXT", default=", ")

    # --- Core Logic ---
    def load(self):
        """
        Called once when the workflow is initialized.
        Use this for any one-time setup. For this simple node, we don't need any.
        """
        pass

    def execute(self, text_a, text_b):
        """
        Called when the node is executed.
        The arguments `text_a` and `text_b` directly correspond to the names of the INPUT_SOCKETS.
        """
        # Get the value from the widget.
        separator_value = self.widget_values.get('separator', self.separator.default)

        # The core logic of the node.
        concatenated_string = f"{text_a}{separator_value}{text_b}"

        # The execute method must return a tuple of output values.
        # The order of values in the tuple corresponds to the order of OUTPUT_SOCKETS.
        return (concatenated_string,)

```

### Step 3: Run the Application

That's it! Save the `custom_nodes.py` file. The next time you run the application, the `ConcatenateNode` will automatically appear in the "Text" category when you right-click on the canvas.

---

## 3. Advanced Example: A "MathOperation" Node

This example demonstrates using the **pull/dependency** mechanism and a widget to control the node's behavior. This node will perform an operation (add or subtract) on two numbers.

```python
# nodes/custom_nodes.py (add this to the same file)
import operator

class MathOperationNode(BaseNode):
    CATEGORY = "Math"

    # --- Sockets ---
    # By setting "is_dependency": True, we tell the engine to "pull" these values
    # before executing the node. This ensures both 'a' and 'b' are available.
    INPUT_SOCKETS = {
        "a": {"type": SocketType.NUMBER, "is_dependency": True},
        "b": {"type": SocketType.NUMBER, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {"result": {"type": SocketType.NUMBER}}

    # --- Widgets ---
    # Use a COMBO widget to provide a user-friendly dropdown for selecting the operation.
    operation = InputWidget(widget_type="COMBO", default="ADD", properties={"values": ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"]})

    def load(self):
        pass

    def execute(self, a, b):
        op_str = self.widget_values.get('operation', self.operation.default).upper()

        op_map = {
            "ADD": operator.add,
            "SUBTRACT": operator.sub,
            "MULTIPLY": operator.mul,
            "DIVIDE": operator.truediv
        }
        op_func = op_map.get(op_str)

        # Handle division by zero and unknown operations
        if op_func is None:
            return (float('nan'),)
        if op_str == "DIVIDE" and float(b) == 0:
            return (float('inf'),) # Or float('nan') depending on desired behavior

        result = op_func(float(a), float(b))
        return (result,)
```

---

## 4. Advanced Sockets: Dynamic Arrays

The engine supports a powerful feature called **dynamic array sockets**. This allows you to create inputs and outputs that can accept a variable number of connections. In the UI, this appears as a per-array `+` and `-` button on the node, letting the user add or remove slots of the same type.

### How It Works

When you declare a socket with `"array": True` in `INPUT_SOCKETS` or `OUTPUT_SOCKETS`, the system treats it differently:

1.  **UI**: Instead of a fixed socket, the node will display `+` and `-` buttons for that specific array (e.g., `+ texts`, `- texts`). Clicking `+` adds a new, numbered socket (e.g., `texts_0`, `texts_1`). Each of these can be connected independently.

2.  **Backend (Inputs)**: When the node is executed, the engine gathers all the values from the dynamically added inputs (`texts_0`, `texts_1`, ...), collects them into a single Python `list`, and passes that list as the argument to your `execute` method.

3.  **Backend (Outputs)**: For a dynamic array output, your `execute` method must return a `list` of values. The engine will then map each item in that list to a corresponding output slot (`results_0`, `results_1`, etc.) and push the data downstream.

### Example: A "Split Text" Node

Let's create a node that takes a single string, splits it by a separator, and provides each piece on a dynamic output array.

```python
# in a file like nodes/custom_nodes.py
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT

class SplitTextNode(BaseNode):
    CATEGORY = "Text"
    
    # --- Sockets ---
    INPUT_SOCKETS = {
        "text": {"type": SocketType.TEXT}
    }
    OUTPUT_SOCKETS = {
        # "array": True makes this a dynamic output array.
        "parts": {"type": SocketType.TEXT, "array": True}
    }
    
    # --- Widget ---
    separator = InputWidget(widget_type="TEXT", default=",")

    def load(self):
        pass

    # --- Execution ---
    def execute(self, text):
        separator_val = self.widget_values.get('separator', self.separator.default)
        
        # The core logic: split the string into a list.
        # This list will be mapped to the 'parts_0', 'parts_1', ... outputs.
        result_list = text.split(separator_val)
        
        # The list must be returned inside a tuple because it corresponds to a single
        # output socket definition ('parts').
        return (result_list,)
```

### Key Takeaways for Dynamic Arrays

-   To create a dynamic array, add `"array": True` to its socket definition in `INPUT_SOCKETS` or `OUTPUT_SOCKETS`.
-   **For inputs**, the corresponding argument in your `execute` method will be a Python `list`.
-   **For outputs**, the corresponding return value from your `execute` method must be a Python `list`.
-   The `is_dependency` flag is often useful for array inputs to ensure all connected data is available before execution if the connected data nodes are not expected to push data on their own.

## 5. Available Widgets and Properties

The frontend determines which UI widgets to render based on the `widget_type` string. Here are the currently supported types:

| `widget_type` | Renders as... | Available `properties` in `InputWidget` |
|---------------|--------------------|-------------------------------------------------|
| `"TEXT"` | A text input box. | (None) |
| `"NUMBER"` | A number input box.| `{"min": number, "max": number, "step": number}` |
| `"SLIDER"` | A horizontal slider. | `{"min": number, "max": number, "step": number}` |
| `"BOOLEAN"` | A toggle/checkbox. | (None) |
| `"COMBO"` | A dropdown menu. | `{"values": ["list", "of", "options"]}` |

**Examples of using properties:**

```python
# A number widget that acts like a slider from 0 to 100 with a step of 5.
percentage = InputWidget(widget_type="SLIDER", default=50, properties={"min": 0, "max": 100, "step": 5})

# A dropdown menu for selecting a mode.
mode_selection = InputWidget(widget_type="COMBO", default="Option A", properties={"values": ["Option A", "Option B", "Option C"]})

# A simple on/off switch.
enable_feature = InputWidget(widget_type="BOOLEAN", default=True)
```

## 6. Advanced Feature: Skipping Outputs for Conditional Logic

For creating nodes that control the flow of the graph (e.g., routing data based on a condition), you can instruct the engine to skip an output. This prevents any downstream nodes connected to that output from executing.

To do this, you import the `SKIP_OUTPUT` object from `core.definitions` and return it in the position of the output you wish to skip in your `execute` method's return tuple.

For a dynamic output array, you can place `SKIP_OUTPUT` within the returned list. The engine will not fire the output for the corresponding slot. For example, returning `(['A', SKIP_OUTPUT, 'B'],)` for an array output would fire `parts_0` with value `'A'`, skip `parts_1`, and fire `parts_2` with value `'B'`.

### Example: A Simple "Gate" Node

Let's imagine a node that only passes a value through if a `boolean` widget is checked.

```python
# nodes/conditional_nodes.py
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT

class GateNode(BaseNode):
    CATEGORY = "Conditional"
    INPUT_SOCKETS = {"value": {"type": SocketType.ANY}}
    OUTPUT_SOCKETS = {"output": {"type": SocketType.ANY}}

    is_open = InputWidget(widget_type="BOOLEAN", default=True)

    def load(self):
        pass

    def execute(self, value):
        # Get the state of the gate from the widget
        gate_is_open = self.widget_values.get('is_open', self.is_open.default)

        if gate_is_open:
            # The gate is open, so pass the value through.
            return (value,)
        else:
            # The gate is closed. Return SKIP_OUTPUT to prevent the
            # 'output' socket from firing.
            return (SKIP_OUTPUT,)
```
The `DecisionNode` in `conditional_nodes.py` is another great example of this, where it returns the value on one output and `SKIP_OUTPUT` on the other based on the result of a comparison.

---

## 7. Advanced Feature: Asynchronous Nodes

The engine supports nodes that perform non-blocking operations, such as waiting for a timer or making an external API call. This is achieved by defining the `execute` method as an `async` function.

### How It Works

The engine automatically checks if a node's `execute` method is a coroutine function (defined with `async def`). If it is, the engine will `await` the function, allowing the `asyncio` event loop to manage other tasks while it runs. If it's a regular function (defined with `def`), the engine calls it directly.

This allows you to create nodes that can perform long-running I/O-bound tasks without blocking the entire workflow execution.

### Example: The `WaitNode`

Let's create a node that waits for a specified number of seconds before passing its input through. This is a perfect use case for an `async` node.

```python
# nodes/utility_nodes.py
import asyncio
from core.definitions import BaseNode, SocketType, InputWidget

class WaitNode(BaseNode):
    CATEGORY = "Utility"

    # This node needs to be triggered. We also mark it as a dependency
    # in case it's used to delay a branch that another node depends on.
    INPUT_SOCKETS = {
        "trigger": {"type": SocketType.ANY, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }

    # Widget to set the delay time in the UI
    wait_time_seconds = InputWidget(widget_type="NUMBER", default=5, properties={"min": 0})

    def load(self):
        pass

    # Note the 'async' keyword here. This is the key to the feature.
    async def execute(self, trigger):
        """
        Waits for the specified duration, then returns the input value.
        """
        duration = self.widget_values.get('wait_time_seconds', self.wait_time_seconds.default)
        
        try:
            duration = float(duration)
        except (ValueError, TypeError):
            duration = 0 # Default to 0 if invalid

        # This is a non-blocking sleep. The engine can run other nodes
        # while this one is waiting.
        await asyncio.sleep(duration)

        # Pass the original trigger value to the output
        return (trigger,)
```

### Key Takeaways for Async Nodes

-   Define your `execute` method with `async def` if you need to perform non-blocking I/O operations (like `await asyncio.sleep(n)` or `await client.get(...)`).
-   The rest of the node's structure (`INPUT_SOCKETS`, `OUTPUT_SOCKETS`, `Widgets`, etc.) remains exactly the same.
-   The engine handles the distinction between `sync` and `async` nodes for you.

---

## 8. Advanced Feature: Dynamic Socket Configuration and Loops

Nodes can dynamically modify their socket behavior in two ways: during initialization in the `load()` method, and during execution via the return value. This enables powerful runtime behavior customization and loop creation.

### Method 1: Load-Time Configuration (Static Dynamic Configuration)

Nodes can modify their socket configurations during the `load()` phase based on widget values. This approach sets the behavior once when the workflow initializes.

#### Socket Configuration Access Methods

The `BaseNode` class provides several methods for working with socket configurations:

```python
# Get configuration for a specific input socket
socket_config = self.get_socket_config("my_input")

# Get all input socket configurations
all_configs = self.get_input_socket_configs()

# Dynamically update socket configuration (complete replacement recommended)
self.INPUT_SOCKETS["my_input"] = new_config
```

#### Load-Time Configuration Example

Here's how to create a node that changes its socket behavior based on widget values:

```python
from core.definitions import BaseNode, SocketType, InputWidget

class DynamicBehaviorNode(BaseNode):
    CATEGORY = "Advanced"
    
    INPUT_SOCKETS = {
        "data": {"type": SocketType.ANY, "array": True, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }
    
    # Widget controls for socket behavior
    wait_for_input = InputWidget(widget_type="BOOLEAN", default=True)
    use_dependency = InputWidget(widget_type="BOOLEAN", default=True)
    
    def load(self):
        # Get widget values
        should_wait = self.widget_values.get('wait_for_input', self.wait_for_input.default)
        use_dependency = self.widget_values.get('use_dependency', self.use_dependency.default)
        
        # Build new socket configuration
        socket_config = {"type": SocketType.ANY, "array": True}
        
        # Apply do_not_wait if waiting is disabled
        if not should_wait:
            socket_config["do_not_wait"] = True
        
        # Apply dependency if enabled and we're still waiting
        # (do_not_wait takes priority over is_dependency)
        if use_dependency and should_wait:
            socket_config["is_dependency"] = True
        
        # Complete replacement to clear any existing flags
        self.INPUT_SOCKETS["data"] = socket_config
        
    def execute(self, data):
        # Process data based on current configuration
        return (f"Processed {len(data)} items",)
```

### Method 2: Runtime Configuration (Dynamic State Updates)

For creating loops and truly dynamic behavior, you can use `NodeStateUpdate` to change which inputs the node waits for during the *next* execution.

#### The `execute` Method's Return Value

Your `execute` method can return two different things:
1.  **Just outputs**: `return (output_value,)`
2.  **Outputs and a state update**: `return ((output_value,), NodeStateUpdate(wait_for_inputs=['new_input_to_wait_for']))`

#### Runtime Configuration Example: A Looping Accumulator

Let's create a node that takes an initial number, and then adds to it every time a second input is triggered.

```python
# in a file like nodes/custom_nodes.py
from core.definitions import BaseNode, SocketType, NodeStateUpdate, InputWidget

class LoopingAccumulatorNode(BaseNode):
    CATEGORY = "Test"
    INPUT_SOCKETS = {
        "initial_value": {"type": SocketType.NUMBER},
        # This input will not be waited for initially. It will trigger subsequent executions.
        "add_value": {"type": SocketType.NUMBER, "do_not_wait": True}
    }
    OUTPUT_SOCKETS = {
        "result": {"type": SocketType.NUMBER},
        "threshold_reached": {"type": SocketType.NUMBER}
    }

    threshold = InputWidget(widget_type="NUMBER", default=100)

    def load(self):
        # Best practice to initialize memory in load()
        self.memory['total'] = 0
        self.memory['is_initialized'] = False

    def execute(self, initial_value=None, add_value=None):
        is_initialized = self.memory.get('is_initialized', False)
        threshold_val = float(self.widget_values.get('threshold', self.threshold.default))

        if not is_initialized:
            # FIRST RUN: Triggered by 'initial_value'.
            if initial_value is None: return (0, SKIP_OUTPUT)
            
            total = float(initial_value)
            self.memory['total'] = total
            self.memory['is_initialized'] = True
            
            # Create the state update object to change waiting behavior
            state_update = NodeStateUpdate(wait_for_inputs=['add_value'])
            
            if total > threshold_val:
                return ((SKIP_OUTPUT, total), state_update)
            else:
                return ((total, SKIP_OUTPUT), state_update)
        else:
            # SUBSEQUENT RUNS: Triggered by 'add_value'.
            if add_value is None: return (self.memory['total'], SKIP_OUTPUT)

            total = self.memory['total'] + float(add_value)
            self.memory['total'] = total
            
            if total > threshold_val:
                return (SKIP_OUTPUT, total)
            else:
                return (total, SKIP_OUTPUT)
```

### Enhanced StringArrayCreatorNode Example

The `StringArrayCreatorNode` demonstrates the load-time configuration pattern with three widget controls:

- **wait_toggle**: Controls whether to wait for inputs (`do_not_wait` behavior)
- **dependency_toggle**: Controls dependency pulling behavior
- **single_item_passthrough**: When true, outputs single items directly instead of arrays

### Key Principles for Dynamic Socket Configuration

1. **Socket Priority**: `do_not_wait` always overrides `is_dependency`
2. **Load-Time vs Runtime**: Use load-time configuration for static behavior, runtime updates for loops and state changes
3. **Complete Replacement**: Use `self.INPUT_SOCKETS["name"] = new_config` to fully replace socket configuration and avoid flag pollution
4. **Widget Integration**: Use `self.widget_values.get()` with defaults for consistent behavior

### When to Use Each Method

- **Load-Time Configuration**: When socket behavior should be determined by user settings and remain constant throughout workflow execution
- **Runtime Configuration (NodeStateUpdate)**: When creating loops, state machines, or nodes that need to change their waiting behavior based on execution results

### Creating Loops: Required Components

To create loops, you need to combine three features:
1.  **`self.memory`**: To store the state of the loop between executions
2.  **`"do_not_wait": True`**: On an input to act as the loop trigger
3.  **`NodeStateUpdate`**: To change which inputs the node waits for in subsequent executions

This dynamic socket configuration system enables creating highly flexible nodes that can adapt their behavior at both initialization time and runtime, making workflows more powerful and customizable.
---

## 9. Advanced Feature: Sending Messages to the Client

Nodes have a built-in, structured way to send messages directly to the connected client (e.g., the frontend UI or a test runner). This is useful for logging, debugging, or sending custom events to trigger UI updates, without using an output socket.

### How It Works

The `BaseNode` class provides an `async` helper method called `send_message_to_client`. To use it, your node's `execute` method must also be defined as `async def`.

The method sends a structured JSON message over the WebSocket. This allows the client to distinguish messages sent by nodes from the standard status messages sent by the engine.

### The `MessageType` Enum

To keep messages consistent and easy to filter, you must specify a message type using the `MessageType` enum, which you can import from `core.definitions`. The available types are:
- `MessageType.LOG`: For general, informative messages.
- `MessageType.DEBUG`: For more verbose, developer-focused information.
- `MessageType.TEST_EVENT`: For messages specifically intended for a test runner to capture.
- `MessageType.ERROR`: For reporting non-fatal errors from within a node.
- `MessageType.DISPLAY`: For sending content to the persistent Display Panel in the UI.

### Sending to the Display Panel

Sending content to the Display Panel uses a specific payload structure with `MessageType.DISPLAY`. This allows you to send rich content like text, images, and videos.

The `data_dict` for a `DISPLAY` message must contain the following keys:
-   `"node_title"`: The title to be displayed in the message header. You can get this from `self.node_info.get('title', self.__class__.__name__)`.
-   `"content_type"`: A string specifying how the frontend should render the data. Supported types are:
    -   `"text"`: Renders the `data` as plain text.
    -   `"image"`: Renders the `data` as an image. The `data` should be a URL or a base64-encoded data URI.
    -   `"video"`: Renders the `data` as a video. The `data` should be a URL to the video file.
    -   `"warning"`: Renders the `data` as a distinct warning message.
-   `"data"`: The actual content to be displayed.

The `DisplayOutputNode` is a pre-built example that handles this for you, but you can use this mechanism in any custom node.

### Example: A Node that Logs its Progress

Let's create a node that processes some data and sends log messages to the client at each step.

```python
# in a file like nodes/custom_nodes.py
import asyncio
from core.definitions import BaseNode, SocketType, MessageType

class LoggingProcessorNode(BaseNode):
    CATEGORY = "Utility"
    INPUT_SOCKETS = {"data_in": {"type": SocketType.ANY}}
    OUTPUT_SOCKETS = {"data_out": {"type": SocketType.ANY}}

    async def execute(self, data_in):
        # --- Sending a LOG message ---
        await self.send_message_to_client(
            MessageType.LOG, 
            {"message": f"Started processing data: {data_in}"}
        )

        # --- Sending an IMAGE to the Display Panel ---
        # (Assuming data_in is a URL to an image)
        await self.send_message_to_client(
            MessageType.DISPLAY,
            {
                "node_title": self.node_info.get('title', self.__class__.__name__),
                "content_type": "image",
                "data": data_in 
            }
        )

        # Simulate some work
        await asyncio.sleep(2) 
        processed_data = str(data_in).upper()

        # --- Sending a DEBUG message ---
        await self.send_message_to_client(
            MessageType.DEBUG,
            {"message": "Data transformation complete.", "original": data_in, "transformed": processed_data}
        )

        return (processed_data,)
```

### Key Takeaways for Client Messaging
- Your node's `execute` method must be `async def`.
- Import `MessageType` from `core.definitions`.
- Call `await self.send_message_to_client(message_type, data_dict)`.
- The `data_dict` is a standard Python dictionary containing whatever information you want to send. For `DISPLAY` messages, it must follow the specific structure outlined above.
- The client is responsible for deciding how to display or handle these messages.

---

## 10. Advanced Feature: Creating Event Nodes

Event nodes are a special category of nodes that, instead of being triggered by an input, listen for an external event (like a webhook, message queue, or user input) and start a new workflow run when that event occurs. This enables powerful features like parallel workflow execution and integration with external systems.

### The `EventNode` Class

To create an event node, your class must inherit from `core.definitions.EventNode`. This class is an Abstract Base Class, just like `BaseNode`, but it enforces a different contract.

-   **Inheritance**: `class MyEventNode(EventNode):`
-   **Discovery**: The engine discovers `EventNode`s just like regular nodes. However, they are handled by a special `EventManager` in the backend.

### The `EventNode` Contract

When you inherit from `EventNode`, you **must** implement two new `async` methods:

1.  `async def start_listening(self, trigger_workflow_callback)`:
    *   This method is called by the `EventManager` when the user clicks "Listen for Events" in the UI.
    *   Your job is to start the process that listens for the external event (e.g., start an HTTP server, connect to a message broker).
    *   Crucially, you are given a `trigger_workflow_callback` function. When your event occurs, you **must call this function** to tell the engine to start the workflow.

2.  `async def stop_listening(self)`:
    *   This method is called when the user clicks "Stop Listening" or disconnects.
    *   Your job is to cleanly shut down your listener (e.g., stop the server, close the connection).

### The `trigger_workflow_callback`

This callback function is the key to the whole system. It's an `async` function that you call from your listener. It accepts one argument:

-   `payload`: The data from your event that you want to inject into the workflow. This can be any object, but it's often a string or a dictionary.

### Injecting Event Data into the Workflow

When you call `trigger_workflow_callback(payload)`, the engine does something special:
1.  It starts a new run of the workflow, beginning at your `EventNode`.
2.  It takes the `payload` you provided and injects it into your node's `self.memory` dictionary under the key `'initial_payload'`.

Your `EventNode`'s `execute()` method can then retrieve this data from memory and pass it to its output socket, making it available to the rest of the workflow.

### Example: A Simple `WebhookNode`

Let's look at a practical example: a node that listens for an HTTP POST request and uses the request body as the data for the workflow.

```python
# in a file like nodes/event_nodes.py
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
from core.definitions import EventNode, SocketType, InputWidget

class WebhookNode(EventNode):
    CATEGORY = "Events"
    OUTPUT_SOCKETS = { "received_data": {"type": SocketType.TEXT} }

    port = InputWidget(widget_type="NUMBER", default=8181)
    path = InputWidget(widget_type="TEXT", default="/webhook")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = None
        self.server_thread = None
        self.loop = None

    def load(self):
        """Capture the main asyncio event loop."""
        self.loop = asyncio.get_running_loop()

    async def start_listening(self, trigger_workflow_callback):
        """Start the HTTP server in a separate thread."""
        port_val = int(self.widget_values.get('port', self.port.default))
        path_val = self.widget_values.get('path', self.path.default)

        # Create a handler factory that passes the loop and callback to the handler
        def make_handler(*args, **kwargs):
            return WebhookRequestHandler(self.loop, trigger_workflow_callback, path_val, *args, **kwargs)

        self.server = HTTPServer(('', port_val), make_handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"Webhook server started on http://localhost:{port_val}{path_val}")

    async def stop_listening(self):
        """Shutdown the HTTP server cleanly."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()
            print("Webhook server stopped.")

    def execute(self, *args, **kwargs):
        """
        Called when the workflow starts. It retrieves the payload injected
        by the engine and returns it on the output socket.
        """
        payload = self.memory.get('initial_payload', "")
        return (payload,)

class WebhookRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, loop, trigger_callback, configured_path, *args, **kwargs):
        self.loop = loop
        self.trigger_callback = trigger_callback
        self.configured_path = configured_path
        super().__init__(*args, **kwargs)

    def do_POST(self):
        if self.path == self.configured_path:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload_str = post_data.decode('utf-8')

            # This is the critical part: call the async callback from our server thread,
            # passing the received data as the payload.
            asyncio.run_coroutine_threadsafe(self.trigger_callback(payload_str), self.loop)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return # Suppress console logging
```

### Special case: Display Panel Chat Input Node

The `DisplayInputEventNode` is a special event node that enables chat-like interactions through the Display Panel. Unlike external event nodes, it's triggered by user input from the frontend.


### Key Takeaways for Event Nodes
-   Inherit from `EventNode`.
-   Implement `async def start_listening(self, trigger_workflow_callback)` to start your listener.
-   Implement `async def stop_listening(self)` to clean up.
-   When your event happens, call `trigger_workflow_callback(payload)` to start the workflow.
-   In your `execute()` method, get the data from `self.memory.get('initial_payload')` and return it on an output socket.
-   If your listener runs in a separate thread (like the `HTTPServer`), you must use `asyncio.run_coroutine_threadsafe(coro, loop)` to safely call the async callback on the main event loop.
-   For Display Panel integration, use `self.global_state.get('display_context', [])` to access the conversation history.

---

## 11. Recent Node Examples

### TriggerDetectionNode
A utility node that demonstrates advanced socket configuration:
```python
class TriggerDetectionNode(BaseNode):
    CATEGORY = "Utility"
    INPUT_SOCKETS = {
        "dependency_input": {"type": SocketType.ANY, "is_dependency": True},
        "trigger_input": {"type": SocketType.ANY, "do_not_wait": True}
    }
    OUTPUT_SOCKETS = {"trigger_source": {"type": SocketType.TEXT}}
    
    def execute(self, dependency_input=None, trigger_input=None):
        if trigger_input is not None:
            return (trigger_input,)  # Returns the actual trigger input data
        else:
            return (dependency_input,)  # Returns the actual dependency input data
```

This node shows how to:
- Use both dependency and do_not_wait socket configurations
- Pass through input data based on which socket triggered execution
- Create utility nodes for workflow control

### LLMNode (AI Integration)
The `LLMNode` demonstrates advanced features like:
- Universal AI model access via litellm
- Context integration from display panel and runtime memory
- Multimodal support (text + images) with dedicated image socket
- **Fully implemented and tested** tool calling system with MCP-inspired design
- Base64 image processing and automatic format detection
- Support for servable paths, external URLs, and embedded base64 images

## 12. Creating Tool Nodes for LLM Integration

Tool nodes are special nodes designed to work with the `LLMNode`'s **fully tested and functional** tool calling system. They follow **Model Context Protocol (MCP)**-inspired patterns and operate in dual modes to support AI tool calling workflows.

### Tool Node Architecture

Tool nodes have a unique dual-operation architecture:
1. **Definition Mode**: When called with `tool_call=None`, they return their tool schema/definition
2. **Execution Mode**: When called with actual tool call data, they process the request and return results

This dual mode allows the LLM to first discover available tools, then execute them when needed.

### Basic Tool Node Structure

Here's the essential structure for a tool node:

```python
from core.definitions import BaseNode, SocketType

class MyToolNode(BaseNode):
    CATEGORY = "Tools"
    
    # Tool nodes have a single input that can receive tool calls
    INPUT_SOCKETS = {
        "tool_call": {"type": SocketType.ANY, "do_not_wait": True}
    }
    
    # Tool nodes have a single output for results
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }
    
    def load(self):
        # Initialize any required data structures
        pass
    
    def execute(self, tool_call=None):
        # Define the tool schema (MCP-inspired)
        tool_definition = {
            "name": "my_tool",
            "description": "What this tool does",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of parameter 1"
                    }
                },
                "required": ["param1"]
            }
        }
        
        # If no tool call provided, return the tool definition
        if tool_call is None:
            return (tool_definition,)
        
        # Process the actual tool call
        try:
            if isinstance(tool_call, dict) and 'arguments' in tool_call:
                args = tool_call['arguments']
                # Extract parameters from the arguments
                param1 = args.get('param1', '')
                
                # Perform the tool's logic
                result = f"Processed: {param1}"
                
                # Return structured result
                tool_result = {
                    "id": tool_call.get('id', 'unknown'),
                    "result": result
                }
                return (tool_result,)
            else:
                # Handle invalid tool call format
                error_result = {
                    "id": tool_call.get('id', 'error'),
                    "error": "Invalid tool call format"
                }
                return (error_result,)
        except Exception as e:
            # Handle exceptions gracefully
            error_result = {
                "id": tool_call.get('id', 'exception'),
                "error": f"Tool error: {str(e)}"
            }
            return (error_result,)
```

### Key Requirements for Tool Nodes

1. **Socket Configuration**:
   - Single input socket named `tool_call` with `"do_not_wait": True`
   - Single output socket named `output`

2. **Dual Mode Operation**:
   - Return tool definition when `tool_call=None`
   - Process and return results when `tool_call` contains data

3. **MCP-Inspired Schema**:
   - Use JSON Schema format for `input_schema`
   - Include `name`, `description`, and `input_schema` in definition
   - Follow standard JSON Schema property definitions

4. **Structured Results**:
   - Always return results in `{"id": ..., "result": ...}` format
   - Handle errors with `{"id": ..., "error": ...}` format
   - Use the tool call ID for proper message correlation

### Example: Calculator Tool Node

Here's a complete example of a calculator tool that performs basic arithmetic:

```python
from core.definitions import BaseNode, SocketType

class CalculatorToolNode(BaseNode):
    """
    A calculator tool that performs basic arithmetic operations.
    Demonstrates proper tool node implementation with error handling.
    """
    CATEGORY = "Tools"
    
    INPUT_SOCKETS = {
        "tool_call": {"type": SocketType.ANY, "do_not_wait": True}
    }
    
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }

    def load(self):
        pass

    def execute(self, tool_call=None):
        # Define the tool schema (MCP-inspired)
        tool_definition = {
            "name": "calculator",
            "description": "Perform basic arithmetic operations (add, subtract, multiply, divide)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The arithmetic operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        }
        
        # If no tool call provided, return the tool definition
        if tool_call is None:
            return (tool_definition,)
        
        # Process the tool call
        try:
            if isinstance(tool_call, dict) and 'arguments' in tool_call:
                args = tool_call['arguments']
                operation = args.get('operation')
                a = float(args.get('a', 0))
                b = float(args.get('b', 0))
                
                # Perform the calculation
                if operation == "add":
                    result = a + b
                elif operation == "subtract":
                    result = a - b
                elif operation == "multiply":
                    result = a * b
                elif operation == "divide":
                    if b == 0:
                        return ({
                            "id": tool_call.get('id', 'calc_error'),
                            "error": "Division by zero is not allowed"
                        },)
                    result = a / b
                else:
                    return ({
                        "id": tool_call.get('id', 'calc_error'),
                        "error": f"Unknown operation: {operation}"
                    },)
                
                # Return successful result
                tool_result = {
                    "id": tool_call.get('id', 'calc_result'),
                    "result": result
                }
                return (tool_result,)
            else:
                # Invalid format
                return ({
                    "id": tool_call.get('id', 'calc_error'),
                    "error": "Invalid tool call format"
                },)
                
        except Exception as e:
            # Handle unexpected errors
            return ({
                "id": tool_call.get('id', 'calc_exception'),
                "error": f"Calculator error: {str(e)}"
            },)
```

### Tool Node Best Practices

1. **Always Handle Both Modes**: Check if `tool_call` is None to return definition, otherwise process the call

2. **Robust Error Handling**: Wrap tool execution in try-catch blocks and return structured error responses

3. **Validate Input Parameters**: Check that required parameters are present and have valid types

4. **Use Descriptive Schemas**: Provide clear descriptions for the tool and all its parameters

5. **Preserve Tool Call IDs**: Always include the original tool call ID in results for proper correlation

6. **Handle Edge Cases**: Consider division by zero, missing parameters, invalid types, etc.

7. **Test Thoroughly**: Tool nodes need to work in both definition and execution modes

### Connecting Tools to LLM Node

To use your tool nodes with the LLM node:

1. Connect tool nodes to the LLM node's `tools` array input (they will provide definitions)
2. Connect the LLM node's `tool_calls` array output back to the same tool nodes (for execution)
3. The LLM node will automatically route tool calls to the correct tools by name
4. Tool results will be processed and integrated into the AI conversation

The LLM node handles all the complex routing, message sequencing, and OpenAI API compatibility automatically. This system has been thoroughly tested with multiple tool types and complex tool calling scenarios.

### Image Generation Tool Node Example

Here's a complete example of the `GPTImageToolNode` that demonstrates advanced tool node patterns with image generation:

```python
from core.definitions import BaseNode, SocketType, InputWidget, MessageType
from core.file_utils import ServableFileManager
import uuid
import base64

class GPTImageToolNode(BaseNode):
    """
    Tool node for generating images using OpenAI's gpt-image-1 model.
    Demonstrates advanced patterns: async execution, file management,
    widget-controlled parameters, and comprehensive error handling.
    """
    CATEGORY = "Tools"
    
    INPUT_SOCKETS = {
        "tool_call": {"type": SocketType.ANY, "do_not_wait": True}
    }
    
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }
    
    # Configuration widgets (not exposed to AI, used internally)
    api_key = InputWidget(widget_type="TEXT", default="", description="OpenAI API Key")
    size = InputWidget(
        widget_type="COMBO", 
        default="1024x1024",
        properties={"values": ["1024x1024", "1024x1536", "1536x1024"]}
    )
    quality = InputWidget(
        widget_type="COMBO",
        default="high",
        properties={"values": ["low", "medium", "high", "auto"]}
    )

    def load(self):
        if litellm is None:
            raise ImportError("litellm library is required")
        self.file_manager = ServableFileManager()

    async def execute(self, tool_call=None):
        # Tool definition (MCP-compatible) - only expose prompt to AI
        tool_definition = {
            "name": "generate_image",
            "description": "Generate high-quality images using OpenAI's gpt-image-1 model",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Detailed description of the image to generate"
                    }
                },
                "required": ["prompt"]
            }
        }
        
        # Return definition if no tool call
        if tool_call is None:
            return (tool_definition,)
        
        # Process tool call
        try:
            if isinstance(tool_call, dict) and 'arguments' in tool_call:
                args = tool_call['arguments']
                prompt = str(args.get('prompt', '')).strip()
                
                # Use widget values (not exposed to AI)
                size = str(self.widget_values.get('size', self.size.default))
                quality = str(self.widget_values.get('quality', self.quality.default))
                api_key_val = self.widget_values.get('api_key', self.api_key.default)
                
                if not prompt:
                    return ({"id": tool_call.get('id'), "error": "Prompt required"},)
                
                if not api_key_val:
                    return ({"id": tool_call.get('id'), "error": "API key required"},)
                
                # Set API key and generate image
                litellm.openai_key = api_key_val
                
                response = await litellm.aimage_generation(
                    model="gpt-image-1",
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    n=1
                )
                
                # Process base64 response directly (no URL downloading)
                first_data_item = response.data[0]
                if hasattr(first_data_item, 'b64_json') and first_data_item.b64_json:
                    image_data = base64.b64decode(first_data_item.b64_json)
                    filename = f"gpt_image_{uuid.uuid4().hex[:8]}.png"
                    servable_url = self.file_manager.save_file(image_data, filename)
                    
                    await self.send_message_to_client(MessageType.LOG,
                        {"message": f"✅ Image generated: {filename}"})
                    
                    # Return structured result with instructions
                    return ({
                        "id": tool_call.get('id'),
                        "result": {
                            "success": True,
                            "message": f"Image generated: {servable_url}",
                            "servable_url": servable_url,
                            "filename": filename,
                            "instructions": "Always display the servable_url to the user"
                        }
                    },)
                else:
                    return ({"id": tool_call.get('id'), "error": "No image data received"},)
            else:
                return ({"id": tool_call.get('id'), "error": "Invalid tool call format"},)
                
        except Exception as e:
            return ({"id": tool_call.get('id'), "error": f"Generation error: {str(e)}"},)
```

This example demonstrates:
- **Async Tool Execution**: Using `async def execute()` for API calls
- **File Management**: Using `ServableFileManager` for automatic file serving
- **Base64 Processing**: Direct base64 handling without URL downloads
- **Widget-Controlled Parameters**: Size/quality from widgets, not AI input
- **Client Messaging**: Using `send_message_to_client()` for progress updates
- **Comprehensive Error Handling**: Structured error responses for all failure modes
- **Result Instructions**: Guiding AI to display the generated image link

## 13. Image Processing Nodes

The system includes specialized nodes for handling images in AI workflows. These demonstrate advanced patterns for file management, conditional output, and image link processing.

### ImageLinkExtractNode Pattern

This node shows how to create conditional outputs using `SKIP_OUTPUT`:

```python
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT
import re

class ImageLinkExtractNode(BaseNode):
    """
    Extracts image links from text with conditional output.
    Demonstrates regex pattern matching and SKIP_OUTPUT usage.
    """
    CATEGORY = "Image"

    INPUT_SOCKETS = {
        "text": {"type": SocketType.TEXT}
    }
    
    OUTPUT_SOCKETS = {
        "text": {"type": SocketType.TEXT},      # Cleaned text
        "image_link": {"type": SocketType.TEXT}  # Extracted link
    }
    
    extract_first_only = InputWidget(
        widget_type="BOOLEAN",
        default=True,
        description="Extract only the first image link found"
    )

    def load(self):
        """Initialize regex patterns for comprehensive image detection."""
        self.patterns = [
            r'!\[([^\]]*)\]\(([^)]+)\)',  # Markdown: ![alt](url)
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',  # HTML: <img src="url">
            r'(https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|bmp|svg)(?:\?[^\s]*)?)',  # URLs
            r'(/servable/[^\s]+)',  # Servable links
            r'(data:image/[^;]+;base64,[A-Za-z0-9+/=]+)'  # Base64 data URLs
        ]

    def execute(self, text):
        if not text:
            return (SKIP_OUTPUT, SKIP_OUTPUT)  # Skip both outputs if no text

        extracted_links = []
        
        # Search for image links using all patterns
        for pattern in self.patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Handle both markdown (2 groups) and direct URL (1 group) patterns
                link = match.group(2) if len(match.groups()) == 2 else match.group(1)
                extracted_links.append({
                    'link': link,
                    'full_match': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })

        # No image links found - output only cleaned text
        if not extracted_links:
            return (text, SKIP_OUTPUT)

        # Process first link, remove from text
        first_link = extracted_links[0]
        cleaned_text = text[:first_link['start']] + text[first_link['end']:]
        cleaned_text = cleaned_text.strip()
        
        # Use SKIP_OUTPUT for empty cleaned text
        text_output = cleaned_text if cleaned_text else SKIP_OUTPUT
        image_output = first_link['link']
        
        return (text_output, image_output)
```

### File Management with ServableFileManager

For nodes that need to handle file operations:

```python
from core.file_utils import ServableFileManager
import uuid

class MyImageNode(BaseNode):
    def load(self):
        self.file_manager = ServableFileManager()
    
    async def execute(self, image_data):
        # Save binary data with automatic filename generation
        filename = f"processed_{uuid.uuid4().hex[:8]}.png"
        servable_url = self.file_manager.save_file(image_data, filename)
        
        # URL is automatically accessible at http://localhost:8000/servable/filename
        return (servable_url, filename)
```

### Key Patterns for Image Processing Nodes

1. **Conditional Output with SKIP_OUTPUT**: Skip outputs when no relevant data is found
2. **Comprehensive Pattern Matching**: Support multiple image formats (markdown, HTML, URLs, base64)
3. **File Management Integration**: Use `ServableFileManager` for automatic CORS-friendly file serving
4. **Base64 Direct Processing**: Handle base64 images directly without URL downloading
5. **Widget-Controlled Behavior**: Use widgets for parameters not exposed to AI systems
6. **Progress Messaging**: Use `send_message_to_client()` for user feedback in async operations

## 14. Event Communication Nodes

The system includes specialized nodes for inter-workflow communication, enabling parallel workflow coordination and data exchange:

### Event Communication Pattern

The event system follows a Send/Receive/Await/Return pattern:

```python
# Example: ReceiveEventNode that starts parallel workflows
class ReceiveEventNode(EventNode):
    """Listens for internal events and starts parallel workflows."""
    CATEGORY = "Events"
    
    OUTPUT_SOCKETS = {
        "data": {"type": SocketType.ANY},
        "event_id": {"type": SocketType.TEXT},
        "await_id": {"type": SocketType.TEXT}  # For response correlation
    }
    
    listen_id = InputWidget(widget_type="TEXT", default="event_1")
    
    async def start_listening(self, trigger_workflow_callback):
        # Register with EventManager for internal event listening
        if self.event_manager:
            await self.event_manager.register_internal_listener(self.listening_id, trigger_workflow_callback)
    
    def execute(self, *args, **kwargs):
        payload = self.memory.get('initial_payload', "")
        event_id = self.widget_values.get('listen_id', self.listen_id.default)
        
        # Handle await functionality
        if isinstance(payload, dict) and 'await_id' in payload:
            return (payload['data'], event_id, payload['await_id'])
        else:
            return (payload, event_id, SKIP_OUTPUT)
```

### Key Event Node Features

1. **ReceiveEventNode** (EventNode): Inherits from EventNode, registers with EventManager, outputs event data and correlation IDs

2. **SendEventNode/AwaitEventNode**: Use `self.event_manager` to send events, support both single and array event IDs

3. **Event Manager Integration**: Nodes access EventManager via `self.event_manager` (passed during initialization)

4. **Timeout and Response Handling**: AwaitEventNode includes timeout logic and partial response collection

### Best Practices for Event Nodes

- Use unique event IDs to avoid conflicts between different workflows
- Always handle the case where `self.event_manager` might be None
- Use SKIP_OUTPUT for conditional outputs (e.g., await_id when not present)
- Include proper error handling and timeout logic for await operations
- Follow the established pattern: Send → Receive → Process → Return

## 15. Best Practices and Considerations

- **Keep Nodes Atomic**: Each node should perform a single, clear task. Instead of one giant node that does three things, create three smaller nodes. This makes your workflows more flexible and easier to debug.
- **Initialize Memory**: When using stateful nodes, it is best practice to initialize all expected keys for `self.memory` in the `load()` method. This prevents potential `KeyError` exceptions and makes the node's expected state clear.
- **Handle Missing Inputs**: In your `execute` method, consider what should happen if an optional input is not connected. The argument will be `None` in that case.
- **Return a Tuple**: The `execute` method **must** return a tuple for its outputs, even if there is only one. For a single output, return `(my_value,)`. For no outputs, return `()`. To conditionally prevent an output from firing, return the `SKIP_OUTPUT` object in its place in the tuple.
- **Clear Naming**: Use descriptive names for your node class, sockets, and widgets. This makes the system easier to use for everyone.
- **Check the Frontend**: Remember that the `widget_type` you specify in the backend must have a corresponding implementation in `web/index.html` to render correctly.
- **Follow Tool Node Conventions**: When implementing tool-calling nodes, follow the MCP-inspired dual-mode pattern shown in the examples. The tool calling system is fully functional and tested.


By following this guide, you can extend the AI Node Builder with powerful, custom functionality. Happy building!


