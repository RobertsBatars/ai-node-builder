# **Project Architecture & Journey: Modular AI Node Application**

## **1. Introduction**

This document outlines the core architecture and design evolution for a modular, node-based graphical application. It is intended as a living reference, capturing not just the "what" but also the "why" behind the key design decisions, including a summary of implementation challenges and outcomes. The primary goals are extensibility, user-friendliness, and robust control over the execution flow.

## **2. Core Architecture: Decoupled Client-Server**

The application is built on a decoupled client-server model. This was a foundational decision to ensure a responsive user interface that would not freeze while the backend performs heavy computations.

* **Backend (The Engine)**: A Python application responsible for all logic.  
  * **Why?** This separation allows the backend to be optimized for pure computation (e.g., PyTorch, LiteLLM) without being burdened by UI rendering. It also opens the possibility for the backend to run on a separate, more powerful machine in the future.  
* **Frontend (The GUI)**: A web-based application for user interaction.  
  * **Why?** Web technologies provide the most flexible and powerful tools for creating a modern and responsive UI. Using a library like LiteGraph.js provides a feature-rich node canvas out of the box.  
* **API Layer**: A communication bridge using WebSockets for real-time updates and a REST API for initial data loading (like the list of available nodes).

## **3. Execution Model: The Journey from Theory to Practice**

The design of the execution engine evolved significantly through our discussions, moving from a simple concept to a more complex, parallel model. This journey revealed significant challenges in implementation.

### **3.1. Initial Concept: A Hybrid Push/Pull Model**

The chosen architecture was a hybrid model designed to be both intuitive and powerful:

* **Primary Flow (Push)**: The default data flow is a "push" model, where a node, upon finishing execution, pushes its results to downstream nodes. This is visually intuitive for the user, as the execution follows the arrows on the graph.  
* **Dependency Sockets (Pull)**: To handle cases where a node needs data *before* it can run (like an LLM needing tool definitions), we designed a special "dependency" input. A node would explicitly "pull" data from these sockets on-demand during its execution.

### **3.2. Start Node and Parallelism**

To make the system flexible, we decided against a rigid, sequential execution order (like a simple topological sort).

* **Start Node Driven**: Execution begins from a single, user-designated "Start Node" in the UI. This provides clear control over where a workflow begins.  
* **Parallel by Default**: The engine was designed to be parallel using asyncio. When a node produces data on multiple output sockets, the engine should create concurrent, independent tasks for each downstream path.

### **3.3. The Stateful Execution Engine: A Robust Solution**

The initial, purely recursive `asyncio` engine faced significant deadlocking issues when handling the hybrid push/pull model. The root cause was a lack of state management; the engine couldn't differentiate between a node that was waiting for a dependency and one that was actively being executed. This led to circular waits.

To solve this, the engine was fundamentally rewritten to use a **state-machine model**.

*   **Why a State Machine?** A state machine provides a clear and robust framework for managing the lifecycle of each node during a workflow run. It eliminates ambiguity and race conditions by ensuring that nodes transition through well-defined states (`PENDING`, `WAITING`, `EXECUTING`, `DONE`). This was a more resilient alternative to complex locking mechanisms or trying to manage a tangle of interdependent `asyncio` tasks without a central state tracker.

*   **The `run_context` Object**: A central `run_context` dictionary is now created for each workflow. It acts as the "single source of truth," tracking:
    *   The state of every node.
    *   A cache for input data as it arrives.
    *   A list of inputs that each node is still waiting for.
    *   A cache for node output results.
    *   A set of all active `asyncio` tasks.

*   **How it Works (The New Flow)**:
    1.  **Triggering**: When a node is triggered (either by the user or an upstream node), the engine first checks its state in the `run_context`. A single trigger event can now carry data for multiple input sockets simultaneously.
    2.  **Resetting Completed Nodes**: If a node is in the `DONE` state and is re-triggered, the engine will reset it. Crucially, it only clears the cached values for its *standard* inputs, preserving any dependency or pull-style inputs. This allows a completed part of a graph to be re-run with new data without forcing a full recalculation of its static dependencies.
    3.  **Setup (`PENDING` -> `WAITING`)**: If it's the first time the node is triggered, it's moved to the `WAITING` state. The engine identifies all its connected inputs and determines which ones are "pull" dependencies (marked with `is_dependency: True` in the node's definition). It then recursively triggers those dependency nodes.
    4.  **Input Processing**: When an upstream node pushes data, the engine finds the waiting downstream node, stores the data in its `input_cache`, and removes that input from the node's "waiting list." The engine efficiently processes a batch of incoming data points in a single operation.
    5.  **Execution (`WAITING` -> `EXECUTING`)**: After processing incoming data, the engine checks if the node's "waiting list" is empty. If it is, the node is moved to the `EXECUTING` state, and its `execute()` method is called with the fully assembled input data.
    6.  **Completion (`EXECUTING` -> `DONE`)**: Once execution is finished, the node is marked as `DONE`, and its results are pushed to all downstream nodes, triggering the process anew.

*   **Key Benefits of the New Model**:
    *   **No Deadlocks**: A node is only executed once all its required inputs are explicitly resolved and cached. The "pull" and "push" actions are now decoupled, preventing circular waits.
    *   **Correct Dependency Handling**: The engine now correctly respects the `is_dependency` flag, only pulling data when necessary and avoiding redundant pulls if the data is already being pushed.
    *   **Clarity and Debuggability**: The state machine and verbose logging make the execution flow far easier to trace and debug.
    *   **Reliable Re-execution**: The intelligent reset logic ensures that re-running parts of the graph is efficient and predictable.

### **3.4. Grouped Downstream Pushes for Reliability**

A key improvement to the engine is how it handles the "push" part of the cycle. When a node finishes execution and produces multiple outputs, instead of creating separate, independent trigger tasks for each downstream node, the engine now groups these actions.

*   **The Problem (Race Conditions)**: In a scenario where a single upstream node connects to the *same* downstream node on multiple inputs, firing independent triggers could create a race condition. The downstream node might be triggered, execute, and reset multiple times in an unpredictable order.
*   **The Solution (Grouped Pushes)**: The `push_to_downstream` function now gathers all the data packets and groups them by their `target_node_id`. It then creates a single `trigger_node` task for each unique downstream node, passing all the relevant data in a single batch.
*   **Benefit**: This ensures that a downstream node receives all of its inputs from a single upstream execution cycle at once. This makes the execution more reliable, predictable, and efficient, completely avoiding the race condition scenario.

### **3.5. Dynamic Array Sockets: A Flexible I/O Model**

To support nodes that need to process a variable number of inputs or produce a variable number of outputs, the concept of **dynamic array sockets** was introduced. This feature is a collaboration between the frontend and the backend engine.

*   **Frontend Implementation (`web/index.html`)**:
    *   When a node blueprint contains an input or output with the property `"array": True`, the frontend renders a per-array button (e.g., `+ Add Input`).
    *   Clicking this button dynamically adds a new input/output slot to the node, named with an index suffix (e.g., `my_array_0`, `my_array_1`).
    *   A corresponding per-array "remove" button allows the user to remove the last added socket from that specific array.

*   **Backend Engine Implementation (`core/engine.py`)**:
    *   **For Inputs**: Before calling a node's `execute()` method, the engine identifies input names that follow the `basename_index` pattern. It groups the values for these inputs into a single list, which is then passed as a single argument to the `execute()` method.
    *   **For Outputs**: After a node executes, if an output is an array, the engine expects the corresponding return value to be a list. It then iterates through this list, mapping each item to the corresponding physical output slot (`basename_0`, `basename_1`, etc.) and pushing the data downstream.

*   **Example**: A node with an array input `texts` will receive `['val_0', 'val_1']`. A node with an array output `results` can return `(['res_A', 'res_B'])`, and the engine will route `res_A` from the `results_0` slot and `res_B` from the `results_1` slot. This abstracts the complexity from the node developer.

### **3.5. Conditional Execution: Skipping Outputs**

To enable more complex, logic-based workflows (like routing data down different paths), the engine supports the ability for a node to conditionally skip one or more of its outputs.

*   **The `SKIP_OUTPUT` Sentinel**: A special object, `SKIP_OUTPUT`, is defined in `core.definitions`. When a node's `execute` method returns this object in its output tuple for a specific socket, the engine recognizes it as a signal to halt execution for that path.
*   **Engine Behavior**: When the `push_to_downstream` function in the engine encounters the `SKIP_OUTPUT` object, it simply ignores that output and does not trigger any downstream nodes connected to it.
*   **Use Case**: This is essential for creating conditional nodes, such as a "Decision" node that compares two values and routes its input to either a "true" output or a "false" output, but never both at the same time. This prevents unnecessary parts of the graph from being executed.

### **3.6. Asynchronous Execution and Cancellation**

To support long-running tasks (like API calls or timed waits) without freezing the entire engine, and to provide user control over runaway workflows, the engine has two key features: support for asynchronous nodes and a robust cancellation mechanism.

*   **Asynchronous Nodes**: The engine can now execute nodes that have an `async def execute(...)` method. It inspects the node's `execute` method and will `await` it if it's a coroutine. This allows node developers to use `await asyncio.sleep()` for delays, or `await` calls to external APIs, enabling non-blocking I/O operations. The `WaitNode` is a canonical example of this feature.

*   **Workflow Cancellation**: The execution of a workflow is not a blocking call in the main server.
    1.  **Task Management**: When the user clicks "RUN", the `run_workflow` coroutine is wrapped in an `asyncio.Task` and managed by the server. This frees the WebSocket connection to immediately listen for other messages.
    2.  **Stop Command**: A "STOP" button in the UI sends a `stop` command to the server.
    3.  **Cancellation**: The server retrieves the running task associated with the user's session and calls `task.cancel()`.
    4.  **Graceful Shutdown**: This raises an `asyncio.CancelledError` inside the `run_workflow` function. The engine catches this specific error, cancels all of its own child tasks (the individual `active_tasks` for each node), and sends a final "Workflow stopped" message to the UI. This ensures the workflow is terminated cleanly without leaving orphaned processes.

## **4. Node Implementation and Framework (Successful Components)**

### **4.1. The BaseNode Abstract Class**

The foundation of the framework is the BaseNode class, which is an **Abstract Base Class (ABC)**.

* **Why an ABC?** This Python feature acts as a strict contract. It enforces that every new node *must* implement the required load() and execute() methods, preventing incomplete nodes from being loaded and ensuring a consistent structure across the application.

### **4.2. Dynamic UI Definition from Code**

The system for defining a node's UI was successful. It avoids the need for separate configuration files and keeps all related logic in one place.

* **InputWidget Class**: A programmer defines a UI element (like a slider or dropdown) by declaring a class attribute using this helper class.  
* **Automatic Generation**: On startup, the backend engine inspects each node class, finds these InputWidget declarations, and automatically builds a JSON "UI Blueprint" to send to the frontend.  
* **Interactive Widgets**: The design supports widgets that can trigger backend functions via a callback property, enabling dynamic UI elements.

## **5. Tool and LLM Integration (Future Implementation)**

*This section outlines planned features that will build upon the core engine once it is stable.*

* **"Tool Provider" Interface**: A standard interface based on the **Model Context Protocol (MCP)** will allow for two types of tool nodes: an MCP Client Node for external servers and a Python Script Node for simple, internal tools.  
* **Universal LLM Support**: Using a library like **LiteLLM** will allow a single LLMNode to act as a universal interface to over 100 different AI models by translating requests into the standardized OpenAI API format.