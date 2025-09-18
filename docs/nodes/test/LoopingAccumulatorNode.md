---
title: "Looping Accumulator Node"
description: "Advanced test node demonstrating complex state management with NodeStateUpdate and looping patterns"
category: "Test"
tags: ["test", "loop", "accumulator", "state", "memory", "advanced"]
author: "AI Node Builder"
version: "1.0.0"
---

# Looping Accumulator Node

## Overview
The Looping Accumulator Node is an advanced testing utility that demonstrates complex state management, looping patterns, and the use of `NodeStateUpdate` for dynamic input handling. It accumulates values over multiple executions while managing sophisticated state transitions.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `value` | NUMBER | No | No | Value to add to the accumulator |
| `reset` | ANY | No | No | Signal to reset the accumulator |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `total` | NUMBER | Current accumulated total |
| `count` | NUMBER | Number of values accumulated |

## Examples

### Basic Accumulation
1. Connect a Number Node to the `value` input
2. Connect the outputs to Display Nodes
3. Execute multiple times to see accumulation
4. Each execution adds the value to the running total

### Loop Integration
Use in looping workflows to accumulate results:
- Connect loop outputs to the value input
- Monitor total and count to track progress
- Use reset input to restart accumulation cycles

### State Management Testing
Demonstrates advanced state management with dynamic input handling and memory persistence.

## Behavior & Execution

### State Management
- Uses `self.memory` to store accumulated total and count
- Maintains state across multiple executions
- Implements sophisticated state tracking

### Dynamic Input Handling
- Uses `NodeStateUpdate` to control input waiting behavior
- Can dynamically change whether it waits for inputs
- Implements complex execution flow control

### Accumulation Logic
- Adds incoming values to running total
- Tracks count of accumulated values
- Supports reset functionality to clear state

### Memory Structure
The node maintains state in memory:
- `total`: Running sum of all accumulated values
- `count`: Number of values that have been accumulated

## Advanced Features

### NodeStateUpdate Usage
- Demonstrates dynamic control of input waiting behavior
- Shows how to change socket dependency patterns at runtime
- Implements sophisticated execution flow control

### State Persistence
- Maintains accumulation across multiple executions
- Preserves state until workflow completion or reset
- Demonstrates proper memory management patterns

### Reset Functionality
- Supports resetting accumulator state to zero
- Clears both total and count when reset signal received
- Allows for cyclical accumulation patterns

## Loop Patterns

### Accumulation Loops
- Perfect for accumulating values in loop workflows
- Tracks both sum and count for statistical analysis
- Maintains state across loop iterations

### State Reset Cycles
- Supports reset signals to restart accumulation
- Enables multi-cycle accumulation patterns
- Demonstrates state management in complex workflows

### Dynamic Execution Control
- Uses `NodeStateUpdate` for advanced execution patterns
- Controls when the node waits for inputs
- Implements sophisticated looping behaviors

## Testing Applications

### Advanced State Testing
- Validates complex memory management patterns
- Tests state persistence across executions
- Verifies reset functionality works correctly

### Loop Behavior Validation
- Tests accumulation in looping workflows
- Validates state management in complex patterns
- Ensures proper execution flow control

### NodeStateUpdate Testing
- Demonstrates advanced execution control features
- Tests dynamic input handling patterns
- Validates sophisticated state management

## Memory & State Management

### Accumulator State
```python
# Memory structure example:
self.memory = {
    'total': 0.0,      # Running sum
    'count': 0         # Number of accumulated values
}
```

### State Updates
- Tracks total accumulated value
- Counts number of accumulation operations
- Supports state reset functionality

### Persistence Patterns
- State persists across multiple node executions
- Memory survives until workflow completion
- Reset functionality clears state when needed

## Common Use Cases
- **Loop Testing**: Test accumulation in complex loop workflows
- **State Management**: Demonstrate advanced memory patterns
- **Flow Control**: Test NodeStateUpdate functionality
- **Statistics Collection**: Accumulate values and track counts
- **Development Testing**: Validate complex execution patterns
- **Advanced Debugging**: Test sophisticated state management

## Related Nodes
- **Counter Node**: Simpler state management example
- **Add Node Test**: Basic mathematical operations
- **Wait Node**: For controlling execution timing
- **Number Node**: Provides input values for accumulation
- **Assert Node**: For validating accumulated results

## Tips & Best Practices
- This is an advanced testing node for sophisticated patterns
- Study the NodeStateUpdate usage for learning advanced techniques
- Use to understand complex state management patterns
- Monitor both total and count outputs for complete information
- Reset functionality allows for cyclical testing patterns
- Excellent for learning advanced node development techniques

## Advanced Concepts

### NodeStateUpdate
This node demonstrates the use of `NodeStateUpdate` for dynamic execution control, showing how nodes can change their input waiting behavior at runtime.

### Complex State Management
Shows sophisticated memory usage patterns that go beyond simple counters or accumulators, implementing full state management with reset capabilities.

### Loop Integration
Designed specifically for integration with looping workflows, demonstrating how to maintain state across multiple loop iterations while supporting reset cycles.