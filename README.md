# AI Node Builder

A modular, node-based graphical application for creating and running AI and data processing workflows.

## How to Run

1.  **Install Dependencies:**
    Open your terminal and run the following command to install the necessary Python packages:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start the Application:**
    Run the main script to start the backend server:
    ```bash
    python main.py
    ```

3.  **Access the UI:**
    Open your web browser and navigate to:
    [http://localhost:8000](http://localhost:8000)

## How to Use

*   **Add Nodes:** Right-click on the canvas to open the menu and select a node to add.
*   **Select Starting Node:** Before running a workflow, you must select one node to be the starting point. Click on a node to select it.
*   **Run Workflow:** Click the "RUN" button to execute the workflow.

## Development

### Creating Your Own Nodes

If you want to extend the application with your own custom logic, please refer to the [Node Creation Guide](./node_creation_guide.md) for a detailed walkthrough on how to build new nodes.

### Developer Documentation (`devdocs.md`)

The `devdocs.md` file in this repository serves two purposes:
1.  It documents the development journey, architectural decisions, and technical challenges of the project.
2.  It provides essential context for AI assistants to understand the project's structure and goals, enabling them to provide more effective help.
