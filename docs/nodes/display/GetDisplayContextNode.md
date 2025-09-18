---
title: "Get Display Context Node"
description: "Retrieves the Display Panel message history with optional filtering"
category: "Input"
tags: ["input", "display", "context", "history", "state", "filter"]
author: "AI Node Builder"
version: "1.0.0"
---

# Get Display Context Node

## Overview
The Get Display Context Node retrieves the persistent Display Panel message history from the global state. It provides access to all messages that have been sent to the Display Panel during the current session, with optional filtering to show only messages from the current node.

## Input Sockets
This node has no input sockets - it retrieves data from the global state.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `context` | ANY | Array of display context messages |

## Widgets
- **filter_by_node_id**: Boolean toggle (default: false)
  - **Off ("all")**: Returns entire Display Panel history
  - **On ("self")**: Returns only messages from this specific node
  - Enables selective context retrieval

## Context Message Structure
Each message in the context array contains:
- **node_id**: Unique identifier of the node that created the message
- **node_title**: Human-readable name of the source node
- **content_type**: Type of content ("text", "image", "video")
- **data**: The actual message content

## Examples

### Full Context Retrieval
1. Set filter toggle to "all" (default)
2. Connect the output to a Display Output Node or Log Node
3. Run to see the complete Display Panel history
4. Useful for conversation analysis or workflow review

### Self-Filtering
1. Set filter toggle to "self"
2. This retrieves only messages that were created by this specific node instance
3. Useful for tracking a node's own output history
4. **Note**: If the workflow is modified after messages are added to the display context, the self filter may not work correctly and you will receive a warning about the modified workflow

### Conversation Context for LLM
Connect the context output to an LLM Node to provide conversation history:
1. Get Display Context Node → LLM Node (as context input)
2. This gives the LLM access to previous conversation messages
3. Enables context-aware AI responses

### Message Analysis
Use the context for analyzing workflow output:
1. Get Display Context → processing nodes
2. Count messages, analyze content types, or extract specific data
3. Build analytics on workflow behavior

## Behavior & Execution

### Global State Access
- Accesses `global_state['display_context']` array
- Returns a deep copy to prevent circular references
- Does not modify the original context

### Filtering Logic
- **All mode**: Returns complete context array
- **Self mode**: Filters by `node_id` matching this node's ID
- Empty results are possible if no matching messages exist

### Data Safety
- Always returns deep copies of context data
- Prevents accidental modification of global state
- Safe for use in parallel workflows

## Context Integration

### Display Panel Relationship
- Context reflects all Display Output Node messages
- Real-time updates as new messages are added
- Persistent across workflow runs within the same session

### Message Lifecycle
1. Display Output Nodes add messages to global context
2. Get Display Context Node retrieves stored messages
3. Context persists until server restart

### Session Scope
- Context is session-wide, not workflow-specific
- Messages from different workflows are included
- Useful for cross-workflow communication

## Common Use Cases
- **LLM Context**: Provide conversation history to AI models
- **Workflow Analysis**: Examine output patterns and sequences
- **Message Counting**: Track how many outputs have been generated
- **Content Filtering**: Extract specific types of messages
- **State Management**: Build stateful applications using display history
- **Debugging**: Inspect all messages for troubleshooting

## Performance Considerations
- Deep copying protects against circular references but uses memory
- Large contexts may impact performance with frequent access
- Consider filtering when working with extensive message histories

## Integration Patterns

### With LLM Nodes
```
Get Display Context → LLM Node (context input)
```
Provides conversation continuity for AI interactions.

### With Analysis Nodes
```
Get Display Context → Processing Nodes → Display Output
```
Analyze and report on workflow communication patterns.

### With Conditional Logic
```
Get Display Context → Decision Node → Different paths
```
Route workflow based on context content or length.

## Related Nodes
- **Display Output Node**: Creates the messages that this node retrieves
- **LLM Node**: Common consumer of context data
- **Log Node**: For debugging context contents
- **Array processing nodes**: For analyzing context arrays

## Tips & Best Practices
- Use filtering when you only need specific node messages
- Deep copies ensure safe data handling but consider memory usage
- Context is session-persistent - clear server state if needed
- Combine with array processing nodes for sophisticated context analysis
- Useful for building conversational AI workflows
- Check context structure before processing - it may be empty initially