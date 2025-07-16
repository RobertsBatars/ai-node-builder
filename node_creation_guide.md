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

The engine supports a powerful feature called **dynamic array sockets**. This allows you to create an input that can accept a variable number of connections. In the UI, this appears as a button on the node that lets the user add more input slots of the same type.

### How It Works

When you declare an input socket with `"array": True`, the backend engine and frontend UI treat it differently:

1.  **UI**: Instead of a fixed input socket, the node will display a button (e.g., `+ texts`). Clicking this button adds a new input socket (e.g., `texts_0`, `texts_1`, etc.). Each of these can be connected to an output from another node.
2.  **Backend**: When the node is executed, the engine gathers all the values from the dynamically added inputs (`texts_0`, `texts_1`, `texts_2`, ...), collects them into a single Python `list`, and passes that list as the argument to your `execute` method.

### Example: A "Concatenate Array" Node

Let's look at the `ConcatenateArrayNode` from `simple_nodes.py`. It takes any number of text inputs and joins them together.

```python
# nodes/simple_nodes.py

class ConcatenateArrayNode(BaseNode):
    CATEGORY = "Text"
    
    # --- Socket Definition ---
    # 1. "array": True - This is the key to making the socket a dynamic array.
    # 2. "is_dependency": True - This ensures that the nodes connected to this 
    #    array will be called before executing the node as they will not initiate
    #    the push themselves.
    INPUT_SOCKETS = {
        "texts": {"type": SocketType.TEXT, "array": True, "is_dependency": True}
    }
    
    OUTPUT_SOCKETS = {
        "full_text": {"type": SocketType.TEXT}
    }
    
    separator = InputWidget(widget_type="TEXT", default=", ")

    def load(self):
        pass

    # --- Execution ---
    # The 'texts' argument will be a list of strings, not a single value.
    # The engine handles the grouping and ordering for you.
    def execute(self, texts):
        separator_value = self.widget_values.get('separator', self.separator.default)
        
        # The core logic is simple: join the list of strings.
        result = separator_value.join(texts)
        return (result,)
```

### Key Takeaways

-   To create a dynamic array input, add `"array": True` to its socket definition in `INPUT_SOCKETS`.
-   The argument passed to your `execute` method will be a Python `list` containing all the values from the connected inputs, ordered by their index (e.g., `texts_0`, `texts_1`, ...).

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

## 5. Best Practices and Considerations

- **Keep Nodes Atomic**: Each node should perform a single, clear task. Instead of one giant node that does three things, create three smaller nodes. This makes your workflows more flexible and easier to debug.
- **Handle Missing Inputs**: In your `execute` method, consider what should happen if an optional input is not connected. The argument will be `None` in that case.
- **Return a Tuple**: The `execute` method **must** return a tuple, even if there is only one output. For a single output, return `(my_value,)`. For no outputs, return `()`.
- **Clear Naming**: Use descriptive names for your node class, sockets, and widgets. This makes the system easier to use for everyone.
- **Check the Frontend**: Remember that the `widget_type` you specify in the backend must have a corresponding implementation in `web/index.html` to render correctly.
