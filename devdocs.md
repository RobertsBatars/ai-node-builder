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
    1.  **Triggering**: When a node is triggered (either by the user or an upstream node), the engine first checks its state in the `run_context`.
    2.  **Setup (`PENDING` -> `WAITING`)**: If it's the first time the node is triggered, it's moved to the `WAITING` state. The engine identifies all its connected inputs and determines which ones are "pull" dependencies (marked with `is_dependency: True` in the node's definition). It then recursively triggers those dependency nodes.
    3.  **Input Processing**: When an upstream node pushes data, the engine finds the waiting downstream node, stores the data in its `input_cache`, and removes that input from the node's "waiting list."
    4.  **Execution (`WAITING` -> `EXECUTING`)**: After processing incoming data, the engine checks if the node's "waiting list" is empty. If it is, the node is moved to the `EXECUTING` state, and its `execute()` method is called with the fully assembled input data.
    5.  **Completion (`EXECUTING` -> `DONE`)**: Once execution is finished, the node is marked as `DONE`, and its results are pushed to all downstream nodes, triggering the process anew.

*   **Key Benefits of the New Model**:
    *   **No Deadlocks**: A node is only executed once all its required inputs are explicitly resolved and cached. The "pull" and "push" actions are now decoupled, preventing circular waits.
    *   **Correct Dependency Handling**: The engine now correctly respects the `is_dependency` flag, only pulling data when necessary and avoiding redundant pulls if the data is already being pushed.
    *   **Clarity and Debuggability**: The state machine and verbose logging make the execution flow far easier to trace and debug.

### **3.4. Dynamic Array Sockets: A Flexible Input Model**

To support nodes that need to process a variable number of inputs (e.g., concatenating multiple text streams), the concept of **dynamic array sockets** was introduced. This feature is a collaboration between the frontend and the backend engine.

*   **Frontend Implementation (`web/index.html`)**:
    *   When a node blueprint contains an input with the property `"array": True`, the frontend doesn't render a static input socket. Instead, it renders a button (e.g., `+ Add Input`).
    *   Clicking this button dynamically adds a new input slot to the node, named with an index suffix (e.g., `my_input_0`, `my_input_1`).
    *   A corresponding "remove" button is also added for each dynamic input, allowing the user to remove them individually.

*   **Backend Engine Implementation (`core/engine.py`)**:
    *   The core of the implementation is in the `execute_node` function within the engine.
    *   Before calling a node's `execute()` method, the engine inspects all the input data that has been cached for that node.
    *   It identifies input names that follow the `basename_index` pattern (e.g., `texts_0`, `texts_1`).
    *   If the `basename` corresponds to an input socket defined with `"array": True`, the engine groups all the values for these inputs into a single list.
    *   This list, sorted by the index, is then passed as a single argument to the node's `execute()` method.

*   **Example**: If a node has an array input named `texts`, and the user connects three inputs in the UI (which become `texts_0`, `texts_1`, `texts_2`), the `execute` method will be called as `execute(texts=['value_from_0', 'value_from_1', 'value_from_2'])`. This abstracts the complexity from the node developer, who simply receives a list.

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