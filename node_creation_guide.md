# Node Creation Guide

This guide provides a comprehensive walkthrough for creating custom nodes for the AI Node Builder application. By following these steps, you can create any kind of node, from simple inputs to complex processing units.

## 1. Core Concepts

Before creating a node, it's important to understand the fundamental building blocks of the system.

### The `BaseNode` Class

Every node in the application is a Python class that inherits from `core.definitions.BaseNode`. This base class provides the core structure and ensures that the node engine can correctly discover and use your custom node.

### Node Discovery

The engine automatically discovers any class that inherits from `BaseNode` located in any file within the `nodes/` directory. You simply need to create a new Python file (e.g., `my_custom_nodes.py`) inside the `nodes/` directory and define your node classes there. The engine will handle the rest.

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

### Widgets

Widgets are UI elements that appear on the node in the frontend, allowing users to input static values. They are defined as class attributes using the `InputWidget` class from `core.definitions`. The frontend currently supports `TEXT` and `NUMBER` widgets.

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
            duration = 0 # Default to 0 if input is invalid

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

## 8. Best Practices and Considerations

- **Keep Nodes Atomic**: Each node should perform a single, clear task. Instead of one giant node that does three things, create three smaller nodes. This makes your workflows more flexible and easier to debug.
- **Handle Missing Inputs**: In your `execute` method, consider what should happen if an optional input is not connected. The argument will be `None` in that case.
- **Return a Tuple**: The `execute` method **must** return a tuple, even if there is only one output. For a single output, return `(my_value,)`. For no outputs, return `()`. To conditionally prevent an output from firing, return the `SKIP_OUTPUT` object in its place in the tuple.
- **Clear Naming**: Use descriptive names for your node class, sockets, and widgets. This makes the system easier to use for everyone.
- **Check the Frontend**: Remember that the `widget_type` you specify in the backend must have a corresponding implementation in `web/index.html` to render correctly.


By following this guide, you can extend the AI Node Builder with powerful, custom functionality. Happy building!

