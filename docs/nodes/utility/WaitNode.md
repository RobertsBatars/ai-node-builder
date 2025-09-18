---
title: "Wait Node"
description: "Introduces a configurable delay before passing input through"
category: "Utility"
tags: ["utility", "delay", "wait", "async", "timing", "control"]
author: "AI Node Builder"
version: "1.0.0"
---

# Wait Node

## Overview
The Wait Node introduces a configurable delay into your workflow by waiting for a specified duration before passing the input through unchanged. This node is implemented asynchronously, allowing other parts of the workflow to continue executing while the wait is in progress.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `trigger` | ANY | Yes | Yes | The value to pass through after the delay |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `output` | ANY | The input value passed through after the wait period |

## Widgets
- **wait_time_seconds**: Number input (default: 5) - The delay duration in seconds
  - Minimum: 0 seconds
  - Step: 0.1 seconds for precise timing
  - Supports decimal values for sub-second delays

## Examples

### Basic Delay
Connect any data source to the Wait Node's trigger input, set the wait time (e.g., 3 seconds), then connect the output to a Display Node. The data will appear in the display after the specified delay.

### Sequential Processing
Use multiple Wait Nodes with different delays to create staggered execution. For example, connect Text Nodes with different messages through Wait Nodes with delays of 1, 2, and 3 seconds to see messages appear sequentially.

### Workflow Pacing
Insert Wait Nodes between intensive processing steps to control the pace of execution and prevent overwhelming downstream services or APIs.

### Testing Async Behavior
Use Wait Nodes to test workflow cancellation and async behavior by introducing known delays that can be interrupted.

### Rate Limiting
Place Wait Nodes before API calls or external service interactions to implement simple rate limiting.

## Behavior & Execution

### Async Implementation
- Uses `asyncio.sleep()` for non-blocking delays
- Other workflows and nodes can execute during the wait period
- Does not block the entire application

### Input Validation
- Negative wait times are automatically converted to 0
- Invalid values fall back to the widget default (5 seconds)
- Type conversion handles both integer and float inputs

### Passthrough Design
- Input data flows unchanged to the output
- The delay is applied as a side effect
- Maintains data integrity throughout the wait period

### Dependency Pattern
- Uses dependency pulling to ensure the trigger value is available
- Waits for the input before starting the delay timer
- Execution order is predictable and controlled

## Timing Precision

### Accuracy
- Delay precision depends on the system's asyncio event loop
- Generally accurate to within milliseconds for most use cases
- Not suitable for real-time applications requiring microsecond precision

### Minimum Delay
- Supports delays as short as 0.1 seconds
- Zero delay (0 seconds) passes through immediately
- Useful for fine-grained timing control

## Common Use Cases
- **API Rate Limiting**: Prevent overwhelming external services
- **User Experience**: Create smooth, paced interactions
- **Testing**: Simulate real-world delays and timing
- **Workflow Orchestration**: Control execution sequence timing
- **Demo Scenarios**: Create dramatic pauses for presentations
- **Error Recovery**: Add delays before retry attempts

## Performance Considerations
- Async implementation prevents blocking other operations
- Memory usage is minimal during wait periods
- Multiple Wait Nodes can run concurrently without interference
- Does not consume CPU resources during the wait

## Integration Patterns

### Sequential Execution
Chain Wait Nodes with different delays to create precisely timed sequences of events.

### Parallel Delays
Use multiple Wait Nodes in parallel branches to synchronize different parts of a workflow.

### Conditional Delays
Combine with Decision Nodes to apply delays only under certain conditions.

## Error Handling
- Invalid wait times are converted to safe defaults
- Negative values are treated as zero delay
- Type conversion errors fall back to default duration
- No exceptions are thrown for invalid inputs

## Related Nodes
- **Decision Node**: For conditional delay application
- **Counter Node**: For implementing retry delays
- **Log Node**: For monitoring delay timing
- **Display Output Node**: For showing delayed results

## Tips & Best Practices
- Use reasonable delay values to avoid blocking workflows unnecessarily
- Consider the impact on user experience when adding delays
- Test with different delay values to find optimal timing
- Remember that delays are cumulative when chaining Wait Nodes
- Use async-compatible nodes downstream for best performance
- Consider system load when using very short delays repeatedly