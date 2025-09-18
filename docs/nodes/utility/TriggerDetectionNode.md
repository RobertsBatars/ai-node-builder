---
title: "Trigger Detection Node"
description: "Utility node that identifies which input socket triggered its execution"
category: "Utility"
tags: ["utility", "trigger", "detection", "flow-control", "debugging"]
author: "AI Node Builder"
version: "1.0.0"
---

# Trigger Detection Node

## Overview
The Trigger Detection Node is a utility that helps identify which input socket triggered its execution. It demonstrates the difference between dependency and do_not_wait socket behaviors by having one of each type and outputting the value from whichever socket caused the execution.

## Input Sockets
| Socket | Type | Required | Socket Behavior | Description |
|--------|------|----------|-----------------|-------------|
| `dependency_input` | ANY | No | Is Dependency | Input that triggers execution via dependency pulling |
| `trigger_input` | ANY | No | Do Not Wait | Input that triggers execution immediately when data arrives |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `trigger_source` | ANY | The value from whichever input socket triggered the execution |

## Examples

### Testing Dependency vs Do Not Wait Behavior
1. Connect different nodes to both input sockets
2. Connect the output to a Display Node
3. Run the workflow to see which input triggered the execution
4. The output will show the value from the triggering socket

### Flow Control Analysis
Use this node to understand execution flow in complex workflows:
- Connect conditional outputs to both inputs
- Monitor which conditions trigger execution
- Analyze timing and flow patterns

### Debugging Execution Order
Help debug workflow execution by identifying trigger sources:
- Place between complex node connections
- Monitor which paths trigger downstream execution
- Understand data flow patterns

## Behavior & Execution

### Trigger Detection Logic
The node determines the trigger source using this logic:
- If `trigger_input` has data, execution was triggered by the do_not_wait socket
- Otherwise, execution was triggered by the dependency socket
- Returns the value from the triggering socket

### Important Caching Behavior
**Note**: Due to the engine's dependency caching mechanism, the trigger detection behavior has an important nuance:

- **First execution**: If triggered by `trigger_input` first, the dependency will be pulled and cached, so the node detects the dependency as the trigger source
- **Subsequent executions**: If triggered again by `trigger_input` in the same workflow run, the dependency is already cached, so the node correctly detects `trigger_input` as the trigger source

This behavior occurs because dependencies are cached after being pulled once. Depending on your workflow design, this behavior might be desired or you may want to avoid using `is_dependency: True` if you need consistent trigger detection regardless of execution order.

### Socket Behavior Differences
- **dependency_input**: Uses `is_dependency: True` - waits for data to be pulled
- **trigger_input**: Uses `do_not_wait: True` - executes immediately when data arrives

### Execution Patterns
- Dependency input triggers execution through pull mechanisms
- Trigger input causes immediate execution when connected nodes fire
- Only one input will have data during any single execution

## Use Cases

### Workflow Debugging
- Identify which branch of a conditional workflow executes
- Track execution order in complex workflows
- Debug timing issues between different execution paths

### Flow Control Understanding
- Demonstrate the difference between dependency and do_not_wait sockets
- Teach socket behavior patterns to developers
- Visualize data flow in educational contexts

### Execution Monitoring
- Monitor which inputs trigger execution in multi-input scenarios
- Track data flow patterns for optimization
- Identify bottlenecks or unexpected execution paths

## Socket Behavior Education

### Dependency Socket Pattern
The `dependency_input` demonstrates:
- Pull-based data flow where the node actively fetches data
- Execution triggered by dependency resolution
- Useful for ensuring data availability before processing

### Do Not Wait Socket Pattern
The `trigger_input` demonstrates:
- Push-based data flow where incoming data triggers execution
- Immediate execution without waiting for other inputs
- Perfect for event-driven or loop-based patterns

### Comparison Learning
This node provides direct comparison of:
- Pull vs push data flow models
- Dependency coordination vs immediate execution
- Different triggering mechanisms in the same node

## Development Applications

### Testing Socket Configurations
- Validate different socket behavior settings
- Test timing coordination between socket types
- Verify engine handling of mixed socket patterns

### Educational Tool
- Teach developers about socket behavior differences
- Demonstrate execution flow concepts
- Provide hands-on learning for node development

### Workflow Analysis
- Analyze complex workflow execution patterns
- Identify which paths execute under different conditions
- Debug unexpected execution sequences

## Common Use Cases
- **Socket Behavior Learning**: Understand how different socket types work
- **Workflow Debugging**: Identify execution trigger sources
- **Flow Analysis**: Track which branches execute in conditional workflows
- **Development Testing**: Validate socket behavior implementations
- **Educational Demonstrations**: Teach execution flow concepts
- **Pattern Recognition**: Identify common execution patterns

## Related Nodes
- **Decision Node**: For conditional flow control
- **Wait Node**: For execution timing control
- **Counter Node**: For tracking execution patterns
- **Log Node**: For detailed execution logging
- **Test nodes**: For comprehensive behavior testing

## Tips & Best Practices
- Use for learning and understanding socket behavior differences
- Connect different types of nodes to each input to see behavior differences
- Monitor the output to understand which execution paths are taken
- Useful for debugging unexpected workflow behavior
- Great for educational workflows teaching node concepts
- Consider as a diagnostic tool during development

## Execution Flow Examples

### Dependency Triggered Execution
When a node connected to `dependency_input` completes:
1. The dependency socket pulls the data
2. Trigger Detection Node executes
3. Output contains the value from `dependency_input`
4. `trigger_input` remains None

### Trigger Triggered Execution
When a node connected to `trigger_input` fires:
1. Data arrives at the do_not_wait socket
2. Node executes immediately
3. Output contains the value from `trigger_input`
4. `dependency_input` may be None

## Implementation Notes
- Simple logic: returns value from whichever input has data
- Demonstrates socket behavior without complex processing
- Minimal overhead for educational and debugging purposes
- Clear distinction between different execution triggers
- Useful for understanding engine internals and data flow patterns