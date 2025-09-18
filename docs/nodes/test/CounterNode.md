---
title: "Counter Node"
description: "Demonstrates stateful behavior and memory usage with execution counting"
category: "Test"
tags: ["test", "counter", "memory", "state", "execution"]
author: "AI Node Builder"
version: "1.0.0"
---

# Counter Node

## Overview
The Counter Node is a testing utility that demonstrates stateful behavior using the node memory system. It maintains a count of how many times it has been executed, showcasing how nodes can preserve data between executions within a single workflow run.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `trigger` | ANY | Yes | Yes | Input that triggers counting - value is ignored |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `count` | NUMBER | Current execution count |
| `message` | TEXT | Formatted message with execution details |

## Examples

### Basic Counting
1. Connect any node output to the Counter Node's trigger input
2. Connect the Counter Node's outputs to Display Nodes
3. Each time the upstream node executes, the counter increments
4. The count persists throughout the workflow run

### Loop Testing
Use the Counter Node in loop workflows to track iterations:
- Connect loop trigger to Counter Node
- Monitor count output to see iteration progress
- Use message output for formatted feedback

### Execution Flow Analysis
Chain multiple Counter Nodes to track execution flow through different branches of a complex workflow.

## Behavior & Execution

### Memory Management
- Uses `self.memory['count']` to store the current count
- Count starts at 0 for the first execution
- Count persists for the entire workflow run
- Memory is reset when a new workflow starts

### Execution Logic
- Retrieves current count from memory (defaults to 0)
- Increments count by 1
- Stores updated count back to memory
- Returns both numeric count and formatted message

### Output Format
- **count**: Returns the current execution number (1, 2, 3, etc.)
- **message**: Returns formatted string like "Execution count: 3"

## Memory & State Features

### Run-Specific Memory
- Each workflow run gets its own counter instance
- Memory is isolated between different workflow executions
- Perfect for testing stateful behavior patterns

### Memory Persistence
- Count persists across multiple node executions
- Memory survives until workflow completion
- Demonstrates proper memory usage patterns

### State Validation
- Use to verify nodes execute the expected number of times
- Track execution sequences in complex workflows
- Validate loop behavior and iteration counts

## Testing Applications

### Development Testing
- Verify node execution patterns
- Test memory persistence functionality
- Validate stateful node behavior

### Loop Validation
- Count loop iterations in complex workflows
- Track execution frequency of conditional branches
- Monitor repeated node executions

### Flow Analysis
- Analyze workflow execution patterns
- Track data flow through different paths
- Validate execution order and frequency

## Common Use Cases
- **Loop Testing**: Count iterations in looping workflows
- **Execution Tracking**: Monitor how many times nodes execute
- **Memory Demonstration**: Show how to use node memory correctly
- **State Testing**: Validate stateful behavior patterns
- **Development Debugging**: Track execution flow during development

## Related Nodes
- **Test Display Feature Node**: Another testing node for display functionality
- **Looping Accumulator Node**: Advanced stateful testing with complex memory patterns
- **Wait Node**: For controlling execution timing in tests
- **Assert Node**: For validating count values in tests

## Tips & Best Practices
- This is primarily a testing/development node, not for production workflows
- Monitor the count output to understand execution patterns
- Use in test workflows to validate loop behavior
- Remember that memory resets between workflow runs
- Combine with Assert Nodes to validate expected execution counts
- Useful for learning how node memory systems work

## Memory Pattern Example
```python
# How the Counter Node uses memory:
current_count = self.memory.get('count', 0)  # Get existing count or 0
self.memory['count'] = current_count + 1     # Increment and store
return (self.memory['count'], f"Execution count: {self.memory['count']}")
```

This demonstrates the standard pattern for using node memory to maintain state across executions.