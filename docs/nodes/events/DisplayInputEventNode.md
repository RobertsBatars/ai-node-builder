---
title: "Display Input Event Node"
description: "Enables chat-like interaction through the Display Panel interface"
category: "Events"
tags: ["events", "display", "chat", "input", "interaction", "ui"]
author: "AI Node Builder"
version: "1.0.0"
---

# Display Input Event Node

## Overview
The Display Input Event Node enables chat-like interaction through the Display Panel interface. Users can type messages in the Display Panel, and this node triggers workflows with that input, creating an interactive conversational experience within the AI Node Builder interface.

## Input Sockets
This node has no input sockets - it serves as a workflow starting point triggered by user input in the Display Panel.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `user_input` | TEXT | The text message entered by the user in the Display Panel |
| `display_context` | ANY | Current Display Panel message history with warnings filtered |
| `trigger` | ANY | Empty trigger output for workflow control |

## Examples

### Basic Chat Interaction
1. Add a Display Input Event Node to your workflow
2. Click "Listen for Events" to activate the node
3. Connect `user_input` to an LLM Node for AI responses
4. Connect the LLM output to a Display Output Node
5. Type messages in the Display Panel to start conversations

### Conversational AI Workflow
Create an interactive AI assistant by connecting:
Display Input Event Node → LLM Node (with context) → Display Output Node

The `display_context` output provides conversation history to the LLM for context-aware responses.

### Command Processing
Use the user input to trigger different workflows based on commands:
Display Input Event Node → Decision Node (check for commands) → Various processing paths

### Interactive Data Processing
Allow users to provide input for data processing workflows through natural language in the Display Panel.

## Behavior & Execution

### Event Listening
- Registers with the server to receive display panel input events
- Activates when user types and submits messages in the Display Panel
- Remains active until "Stop Listening" is clicked

### Payload Processing
- Receives user input through the WebSocket message system
- Extracts user input from the payload structure
- Handles both dictionary format and direct string payloads

### Context Integration
- Automatically retrieves current Display Panel context
- Filters warnings based on frontend settings
- Provides conversation history for context-aware processing

### Workflow Triggering
- Each user message triggers a new workflow execution
- Multiple messages result in multiple workflow runs
- Each run is independent with fresh execution state

## Message Flow

### User Input Process
1. User types message in Display Panel and presses Enter
2. Frontend sends `display_input` WebSocket message to server
3. Server identifies listening Display Input Event Nodes
4. Node's trigger callback is invoked with the user input
5. Workflow executes with the user input as starting data

### Payload Structure
The node handles payload in multiple formats:
- **Dictionary format**: `{"user_input": "message text"}`
- **Direct string**: Raw message text
- **Fallback**: Uses payload as-is if format is unexpected

### Context Retrieval
- Uses `get_display_context()` to fetch current message history
- Automatically applies warning filtering based on UI settings
- Provides complete conversation context for downstream nodes

## Integration with Display System

### Chat Interface
- Integrates seamlessly with the Display Panel chat interface
- Users see their messages and workflow responses in the same panel
- Creates natural conversational flow

### Message History
- Access to complete conversation history via `display_context` output
- Enables context-aware AI responses
- Supports conversation continuity across multiple interactions

### Real-time Interaction
- Immediate workflow triggering on user input
- No polling or refresh required
- Responsive conversational experience

## Common Use Cases
- **Conversational AI**: Build chat-based AI assistants
- **Interactive Workflows**: Allow user input to guide workflow execution
- **Command Interfaces**: Process natural language commands
- **Data Input**: Collect user data through conversational interfaces
- **Support Systems**: Create interactive help and support workflows
- **Educational Tools**: Build interactive learning experiences

## Advanced Patterns

### Context-Aware Conversations
Connect the `display_context` output to LLM nodes to maintain conversation history and context across multiple user interactions.

### Multi-Modal Interactions
Combine with other input nodes to create workflows that respond to both user text input and other data sources.

### Conditional Responses
Use Decision Nodes to process user input and route to different response mechanisms based on content or intent.

## Performance Considerations
- Each user message creates a new workflow execution
- Consider workflow complexity for responsive user experience
- Context retrieval includes full message history - may impact performance with very long conversations
- Multiple simultaneous users each trigger independent workflow executions

## UI Integration
- Requires active Display Panel in the frontend
- Works seamlessly with existing Display Panel features
- Chat input appears at the bottom of the Display Panel
- Messages and responses appear in chronological order

## Related Nodes
- **Display Output Node**: For sending responses back to the Display Panel
- **LLM Node**: Common destination for processing user input
- **Get Display Context Node**: Alternative way to access conversation history
- **Webhook Node**: Alternative external triggering mechanism

## Tips & Best Practices
- Always connect user input to some form of processing (LLM, analysis, etc.)
- Use the display context for maintaining conversation continuity
- Consider implementing error handling for unexpected user input
- Test the conversational flow from the user's perspective
- Remember that each message triggers a complete workflow execution
- Design workflows to be responsive for good user experience
- Use the trigger output for workflow control when needed
- Consider implementing command detection for special user inputs