---
title: "Log Node"
description: "Logs values and passes them through, with configurable message types"
category: "Output"
tags: ["output", "log", "debug", "messages", "display", "passthrough"]
author: "AI Node Builder"
version: "1.0.0"
---

# Log Node

## Overview
The Log Node is a versatile output node that logs values to the client with configurable message types while passing the input through unchanged. It supports multiple message types including standard logging, debugging, error reporting, and display panel output.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `value_in` | ANY | Yes | Yes | The value to log and pass through |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `value_out` | ANY | The input value passed through unchanged |

## Widgets
- **message_type**: Combo (default: "LOG") - Selects the type of message to send
  - Options: LOG, DEBUG, TEST_EVENT, ERROR, DISPLAY
  - Each type affects how the message is processed and displayed

## Message Types

### LOG
Standard informational messages for general logging purposes. Includes timestamp and node information.

### DEBUG
Detailed debugging information for development and troubleshooting. More verbose than LOG messages.

### TEST_EVENT
Special message type for testing-related logs. Shows differently in the log panel and can be filtered separately from other message types.

### ERROR
Error messages for reporting non-fatal issues. Highlighted in the interface.

### DISPLAY
Sends content directly to the Display Panel with special formatting. Uses the node title and formats content as text.

## Examples

### Basic Logging
Connect any node's output to the Log Node's input, set message type to "LOG", then connect the Log Node's output to continue the workflow. The Log Node will print the value while passing it through.

### Debug Workflow
Use message type "DEBUG" to see detailed information about data flowing through your workflow without interrupting the data flow.

### Display Panel Output
Set message type to "DISPLAY" to send content directly to the Display Panel. This is useful for showing intermediate results or status updates.

### Error Monitoring
Use message type "ERROR" to highlight potential issues in your workflow while still allowing data to flow through.

### Test-Related Logging
Set message type to "TEST_EVENT" for test-related messages that can be filtered separately in the log panel. Note: For actual test assertions and validation, use the Assert Node instead.

## Behavior & Execution

### Passthrough Design
- The node is designed as a passthrough: input value flows unchanged to output
- Logging happens as a side effect without modifying the data
- Enables non-intrusive debugging and monitoring

### Message Structure
- **Standard Messages**: Include message content, node ID, and timestamp
- **Display Messages**: Use special structure with node title, content type, and data
- **Error Handling**: Invalid message types default to LOG level

### Async Operation
The node is async-enabled to handle message sending without blocking the workflow execution.

## Common Use Cases
- **Workflow Debugging**: Monitor data flow at key points
- **Error Reporting**: Log errors while allowing recovery downstream
- **Display Integration**: Send updates to the Display Panel
- **Test-Related Logging**: Mark test-related messages for filtering
- **Data Inspection**: Examine intermediate values without stopping execution

## Integration Features

### Display Panel
When using DISPLAY message type, content appears in the persistent Display Panel with proper formatting and node identification.

### Client Communication
All message types use the structured client messaging system, ensuring consistent handling across different frontend implementations.

### Message Filtering
TEST_EVENT and other message types can be filtered in the log panel for better organization. Note that TEST_EVENT uses the same message structure as the test runner and Assert Node but is not intended for actual test integration - it's simply a different message type for categorization.

## Related Nodes
- **Display Output Node**: Dedicated Display Panel output
- **Text Node**: Provides input values for logging
- **Assert Node**: For testing, assertions, and validation
- **Get Display Context Node**: Retrieves Display Panel history

## Tips & Best Practices
- Use LOG for general information, DEBUG for detailed analysis
- DISPLAY type is perfect for showing results to users
- ERROR type helps identify issues without stopping workflows
- The passthrough design allows placing Log Nodes anywhere in data flow
- Combine multiple Log Nodes with different message types for comprehensive monitoring