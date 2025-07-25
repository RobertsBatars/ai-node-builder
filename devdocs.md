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
    *   A `node_memory` dictionary, allowing nodes to store and retrieve state that persists across multiple executions within the same workflow run.
    *   A `node_wait_configs` dictionary, which stores the list of inputs each node is currently waiting for. This can be changed dynamically by the node itself to create loops.
    *   A list of inputs that each node is still waiting for.
    *   A cache for node output results.
    *   A set of all active `asyncio` tasks.

*   **How it Works (The New Flow)**:
    1.  **Triggering**: When a node is triggered (either by the user or an upstream node), the engine first checks its state in the `run_context`. A single trigger event can now carry data for multiple input sockets simultaneously.
    2.  **Resetting Completed Nodes**: If a node is in the `DONE` state and is re-triggered, the engine will reset it. It repopulates its list of inputs to wait for based on its current (and potentially dynamic) wait configuration. It then clears the cache for only those specific inputs.
    3.  **Setup (`PENDING` -> `WAITING`)**: If it's the first time the node is triggered, it's moved to the `WAITING` state. The engine inspects the node's static definition to determine its initial wait list, respecting flags like `do_not_wait: True`. It also recursively triggers any "pull" dependencies.
    4.  **Input Processing**: When an upstream node pushes data, the engine finds the waiting downstream node, stores the data in its `input_cache`, and removes that input from the node's "waiting list."
    5.  **Execution (`WAITING` -> `EXECUTING`)**: After processing incoming data, the engine checks if the node's "waiting list" is empty. If it is, the node is moved to the `EXECUTING` state, and its `execute()` method is called.
    6.  **State Update & Completion (`EXECUTING` -> `DONE`)**: After execution, the engine checks if the node returned a special `NodeStateUpdate` object. If so, it updates that node's wait configuration for all future executions. Finally, the node is marked as `DONE`, and its results are pushed downstream.

*   **Key Benefits of the New Model**:
    *   **No Deadlocks**: A node is only executed once all its required inputs are explicitly resolved and cached. The "pull" and "push" actions are now decoupled, preventing circular waits.
    *   **Stateful Execution**: The `node_memory` cache allows nodes to be stateful within a single workflow, remembering information from previous executions.
    *   **Dynamic Looping**: By allowing nodes to dynamically change which inputs they wait for, the engine can now support complex, stateful loops.
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

### **3.7. Event-Driven Architecture and Parallel Workflows**

To move beyond a single, user-initiated workflow, an event-driven architecture was introduced. This allows the application to listen for external events (like a webhook) and trigger new workflow runs in parallel, without interfering with the main, user-driven workflow.

*   **The `EventManager`**: A new `core/event_manager.py` module was created to handle all event-related logic. This keeps the main `NodeEngine` focused purely on workflow execution.
    *   For each connected client, the server creates a dedicated `EventManager` instance.
    *   When the user clicks "Listen for Events" in the UI, the server identifies special `EventNode` instances in the graph and instructs the client's `EventManager` to start them.
    *   Each `EventNode` runs its own listener (e.g., an HTTP server in a separate thread). When an event is detected, the node calls a callback function provided by the `EventManager`.
    *   This callback then instructs the main `NodeEngine` to start a *new* workflow run, beginning from the `EventNode` that caught the event.

*   **Parallel Execution with `run_id`**:
    *   The `run_workflow` method in the `NodeEngine` was modified to accept a `run_id`.
    *   The workflow started by the user's "RUN" button is given a predictable ID: `"frontend_run"`.
    *   Workflows started by the `EventManager` are given a unique ID (e.g., `"event_..."`).
    *   This `run_id` is included in all messages sent to the frontend, allowing the UI to distinguish between logs from the main workflow and logs from parallel, event-driven workflows. This is crucial for managing the UI state, as only the completion of the `"frontend_run"` workflow should re-enable the main "RUN" button.

*   **Data Injection for Events**:
    *   To make event nodes useful, a mechanism was created to inject data from the event into the workflow.
    *   The `run_workflow` method now accepts an `initial_payload`.
    *   When the `EventManager` triggers a workflow, it can pass the data received by the event (e.g., the body of a webhook POST request) as this `initial_payload`.
    *   The engine then places this payload into the `self.memory` dictionary of the starting event node under the key `'initial_payload'`, making it immediately available to the node's `execute` method.

*   **Server State Management**:
    *   The server (`core/server.py`) was significantly updated to manage the more complex state. It now tracks multiple workflow tasks and `EventManager` instances per client, ensuring that all processes are correctly started and cleaned up, even on unexpected disconnects.

### **3.8. Persistent Display Context and Workflow Verification**

To provide a more persistent, chat-like interface for workflows, a global "Display Panel" was implemented. This feature required careful state management to ensure that the context was meaningful even when the underlying workflow changed.

*   **Global Display State**: A single, global dictionary (`GLOBAL_DISPLAY_STATE`) was created on the server (`core/server.py`). This state is not tied to a specific workflow run and persists for the lifetime of the server process. It contains the list of display messages and the structural hash of the workflow that started the context.

*   **The `DisplayOutputNode`**: A new node was created (`nodes/display_nodes.py`) that, when executed, appends its input data to this global context. It also sends a message to the client to update the UI in real-time.

*   **Workflow Change Detection**: A key challenge is ensuring the user is aware that a saved context might not be relevant to a modified workflow.
    1.  **Structural Hashing**: The engine (`core/engine.py`) generates a SHA256 hash of the workflow's structure (node types and their connections, ignoring cosmetic details like node positions).
    2.  **Initial Hash Storage**: When the *first* message is added to a currently empty display context, the engine stores the current workflow's hash in the `GLOBAL_DISPLAY_STATE` as the `initial_graph_hash`.
    3.  **Verification on Run**: On every subsequent workflow run, the engine generates a new hash of the current graph. It compares this new hash to the `initial_graph_hash`.
    4.  **Warning Injection**: If the hashes do not match, the engine injects a special "warning" message into the display context. This message is rendered differently in the UI, immediately alerting the user that the context may be from a different version of the workflow and that node-based filtering might be unreliable. This warning is re-injected on every run of the modified workflow until the context is cleared.

*   **State Management**: The server provides WebSocket actions to `get_initial_context`, `load_display_context` from a file, and `clear_display_context`. Clearing the context also resets the `initial_graph_hash` and the warning flags, allowing a new session to begin.

## **4. Node Implementation and Framework (Successful Components)**

### **4.1. The BaseNode and EventNode Abstract Classes**

The foundation of the framework is the `BaseNode` class, which is an **Abstract Base Class (ABC)**.

* **Why an ABC?** This Python feature acts as a strict contract. It enforces that every new node *must* implement the required `load()` and `execute()` methods, preventing incomplete nodes from being loaded and ensuring a consistent structure across the application.
* **Global State Access**: The `BaseNode` constructor was updated to accept the `global_state` dictionary, giving every node instance read/write access to the persistent display context.

To support the event-driven model, a new `EventNode` ABC was introduced, inheriting from `BaseNode`. It adds a new contract for nodes that are intended to start workflows:
*   `async def start_listening(self, trigger_workflow_callback)`
*   `async def stop_listening(self)`

This ensures that the `EventManager` can reliably manage the lifecycle of any event-based node.

### **4.2. Dynamic UI Definition from Code**

The system for defining a node's UI was successful. It avoids the need for separate configuration files and keeps all related logic in one place.

* **InputWidget Class**: A programmer defines a UI element (like a slider or dropdown) by declaring a class attribute using this helper class.  
* **Automatic Generation**: On startup, the backend engine inspects each node class, finds these InputWidget declarations, and automatically builds a JSON "UI Blueprint" to send to the frontend.  
* **Interactive Widgets**: The design supports widgets that can trigger backend functions via a callback property, enabling dynamic UI elements.

## **5. Tool and LLM Integration (Future Implementation)**

*This section outlines planned features that will build upon the core engine once it is stable.*

* **"Tool Provider" Interface**: A standard interface based on the **Model Context Protocol (MCP)** will allow for two types of tool nodes: an MCP Client Node for external servers and a Python Script Node for simple, internal tools.  
* **Universal LLM Support**: Using a library like **LiteLLM** will allow a single LLMNode to act as a universal interface to over 100 different AI models by translating requests into the standardized OpenAI API format.

## **6. Testing Framework**

To ensure the stability and correctness of the node engine and the individual nodes, a dedicated, CLI-based testing framework was implemented. The framework is designed to be separate from the main application server but interacts with it in the same way a real user would.

*   **Test Runner (`test_runner.py`)**: This is a standalone Python script that serves as the entry point for all tests. It is executed from the command line (`python test_runner.py`).

*   **Test Discovery**: The runner automatically discovers test cases by scanning the `/tests` directory for workflow files matching the pattern `test_*.json`.

*   **Workflow-based Tests**: Each test case is a complete workflow saved as a JSON file from the UI. This approach has the benefit of testing the actual graph execution logic, including node interactions, state, and data flow, in a realistic environment.

*   **The `AssertNode`**: The core of the testing logic is the `AssertNode`, a special node available in the "Testing" category.
    -   It takes an `actual` value from the workflow and an `expected` value (usually from a static `InputNode`).
    -   If the values match, the test continues.
    -   If they do not match, the node raises an `AssertionError`, which is caught by the engine and reported to the test runner as a test failure.

*   **Communication**: The test runner communicates with the running application server via WebSockets, exactly like the frontend client. It sends the "run" command with the test workflow's graph data and listens for messages.

*   **Success and Failure Conditions**:
    1.  A test **fails** if the `AssertNode` raises an exception (`AssertionError`).
    2.  A test **fails** if the workflow completes but no `AssertNode` was ever executed. This prevents "false positives" where a broken workflow finishes without actually verifying the result.
    3.  A test **passes** only if the workflow completes *and* at least one `AssertNode` has successfully executed. This is verified by having the `AssertNode` send a special `TEST_EVENT` message to the client, which the test runner listens for.
