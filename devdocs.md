# **Project Architecture & Journey: Modular AI Node Application**

## **1\. Introduction**

This document outlines the core architecture and design evolution for a modular, node-based graphical application. It is intended as a living reference, capturing not just the "what" but also the "why" behind the key design decisions, including a summary of implementation challenges and outcomes. The primary goals are extensibility, user-friendliness, and robust control over the execution flow.

## **2\. Core Architecture: Decoupled Client-Server**

The application is built on a decoupled client-server model. This was a foundational decision to ensure a responsive user interface that would not freeze while the backend performs heavy computations.

* **Backend (The Engine)**: A Python application responsible for all logic.  
  * **Why?** This separation allows the backend to be optimized for pure computation (e.g., PyTorch, LiteLLM) without being burdened by UI rendering. It also opens the possibility for the backend to run on a separate, more powerful machine in the future.  
* **Frontend (The GUI)**: A web-based application for user interaction.  
  * **Why?** Web technologies provide the most flexible and powerful tools for creating a modern and responsive UI. Using a library like LiteGraph.js provides a feature-rich node canvas out of the box.  
* **API Layer**: A communication bridge using WebSockets for real-time updates and a REST API for initial data loading (like the list of available nodes).

## **3\. Execution Model: The Journey from Theory to Practice**

The design of the execution engine evolved significantly through our discussions, moving from a simple concept to a more complex, parallel model. This journey revealed significant challenges in implementation.

### **3.1. Initial Concept: A Hybrid Push/Pull Model**

The chosen architecture was a hybrid model designed to be both intuitive and powerful:

* **Primary Flow (Push)**: The default data flow is a "push" model, where a node, upon finishing execution, pushes its results to downstream nodes. This is visually intuitive for the user, as the execution follows the arrows on the graph.  
* **Dependency Sockets (Pull)**: To handle cases where a node needs data *before* it can run (like an LLM needing tool definitions), we designed a special "dependency" input. A node would explicitly "pull" data from these sockets on-demand during its execution.

### **3.2. Start Node and Parallelism**

To make the system flexible, we decided against a rigid, sequential execution order (like a simple topological sort).

* **Start Node Driven**: Execution begins from a single, user-designated "Start Node" in the UI. This provides clear control over where a workflow begins.  
* **Parallel by Default**: The engine was designed to be parallel using asyncio. When a node produces data on multiple output sockets, the engine should create concurrent, independent tasks for each downstream path.

### **3.3. Implementation Challenges & Failures**

While the design was sound in theory, the implementation of the asynchronous, parallel engine proved to be the primary point of failure.

* **What Worked**:  
  * The simple "push" model (e.g., NumberNode \-\> DisplayNode) was successfully implemented.  
  * The "pull" model for dependencies (e.g., starting from AddNode to pull from two NumberNodes) was also successfully implemented in isolation.  
* **What Failed (The Deadlock Issue)**:  
  * The combination of push and pull in a single run (Test 3\) consistently failed.  
  * **The Cause**: The engine's asynchronous logic created a deadlock. When a start node (e.g., NumberNode A) pushed its data to a middle node (AddNode), it would wait for the entire downstream graph to finish. However, the AddNode could not execute because it was waiting to pull data from its *other* dependency (NumberNode B), which was never triggered. The tasks for AddNode and NumberNode A ended up in a circular wait, causing the workflow to get stuck.  
  * **Conclusion**: The attempts to fix this by simply re-arranging asyncio.gather or asyncio.create\_task were unsuccessful. This indicates that a more robust state management system is required within the engine, likely involving a task queue and a more sophisticated method of tracking when a node's inputs are fully satisfied before scheduling its execution. The simple recursive model was not sufficient for this hybrid design.

## **4\. Node Implementation and Framework (Successful Components)**

### **4.1. The BaseNode Abstract Class**

The foundation of the framework is the BaseNode class, which is an **Abstract Base Class (ABC)**.

* **Why an ABC?** This Python feature acts as a strict contract. It enforces that every new node *must* implement the required load() and execute() methods, preventing incomplete nodes from being loaded and ensuring a consistent structure across the application.

### **4.2. Dynamic UI Definition from Code**

The system for defining a node's UI was successful. It avoids the need for separate configuration files and keeps all related logic in one place.

* **InputWidget Class**: A programmer defines a UI element (like a slider or dropdown) by declaring a class attribute using this helper class.  
* **Automatic Generation**: On startup, the backend engine inspects each node class, finds these InputWidget declarations, and automatically builds a JSON "UI Blueprint" to send to the frontend.  
* **Interactive Widgets**: The design supports widgets that can trigger backend functions via a callback property, enabling dynamic UI elements.

## **5\. Tool and LLM Integration (Future Implementation)**

*This section outlines planned features that will build upon the core engine once it is stable.*

* **"Tool Provider" Interface**: A standard interface based on the **Model Context Protocol (MCP)** will allow for two types of tool nodes: an MCP Client Node for external servers and a Python Script Node for simple, internal tools.  
* **Universal LLM Support**: Using a library like **LiteLLM** will allow a single LLMNode to act as a universal interface to over 100 different AI models by translating requests into the standardized OpenAI API format.