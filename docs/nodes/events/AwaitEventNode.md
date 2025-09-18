---
title: "Await Event Node"
description: "Sends events and awaits responses with timeout handling for request/response patterns"
category: "Events"
tags: ["events", "communication", "await", "response", "timeout", "async"]
author: "AI Node Builder"
version: "1.0.0"
---

# Await Event Node

## Overview
The Await Event Node is part of the **inter-workflow event communication system** that enables request/response patterns between parallel workflows. It extends the functionality of SendEventNode by sending events to parallel workflows and waiting for responses, collecting all responses into an array with configurable timeout handling. This enables sophisticated inter-workflow communication patterns.

This node works together with ReceiveEventNode, SendEventNode, and ReturnEventDataNode to form a complete inter-workflow communication framework managed by the EventManager.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `event_ids` | ANY | No | Yes | Event ID(s) to send to (string or array) |
| `data` | ANY | No | No | Data payload to send with the events |
| `timeout` | NUMBER | No | No | Custom timeout in seconds (overrides widget) |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `results` | ANY | Collected responses from parallel workflows (array or single item) |
| `sent_count` | NUMBER | Number of events successfully sent |

## Widgets
- **event_id_widget**: Text input (default: "event_1") - Fallback event ID when no input connected
- **timeout_seconds**: Number input (default: 30) - Response timeout in seconds
  - Range: 1 to 300 seconds
  - Balances responsiveness with patience for slow workflows

## Examples

### Basic Request/Response
1. Set up a parallel workflow with Receive Event Node → processing → Return Event Data Node
2. Use Await Event Node to send data and wait for the processed result
3. The parallel workflow processes the data and returns the result

### Multi-Workflow Coordination
Send the same request to multiple parallel workflows and collect all their responses into a single array for comparison or aggregation.

### Data Processing Pipeline
Use await patterns to send data through multiple processing stages in parallel, each returning modified or analyzed versions of the data.

### Service Orchestration
Coordinate multiple service-like workflows by sending requests and collecting responses, similar to microservice communication patterns.

## Behavior & Execution

### Event Sending
- Generates unique await_id for correlation tracking
- Sends events with special await payload structure
- Supports both single event ID and arrays of event IDs
- Tracks number of successfully sent events

### Data Handling Patterns
- **Single data to multiple events**: Same data sent to all target event IDs
- **Array data to array events**: Each event ID gets corresponding data item
- **Mixed scenarios**: Handles mismatched array lengths gracefully

### Response Collection
- Waits for responses from all sent events
- Uses asyncio.wait_for() for timeout management
- Collects partial responses if timeout occurs
- Returns single item if only one response, array for multiple

### Timeout Management
- Configurable timeout prevents indefinite waiting
- Partial response collection on timeout
- Debug messages sent to client on timeout
- Graceful degradation with available data

## Await/Response Cycle

### Step 1: Event Preparation
- Creates unique await_id for response correlation
- Packages data with await metadata
- Determines target event IDs from input or widget

### Step 2: Event Distribution
- Sends enhanced payloads to target Receive Event Nodes
- Each payload includes original data plus await_id
- Tracks successful sends for response counting

### Step 3: Response Waiting
- Registers with EventManager for response collection
- Waits for specified number of responses
- Applies timeout to prevent indefinite blocking

### Step 4: Result Processing
- Collects all received responses into array
- Optimizes output format (single item vs array)
- Handles partial results on timeout gracefully

## Integration Patterns

### With Receive Event Node
Target workflows must use Receive Event Node to receive the await-enabled events and access the await_id for response correlation.

### With Return Event Data Node
Target workflows must use Return Event Data Node to send responses back, using the await_id for proper correlation.

### Error Handling
- Missing EventManager results in warning and empty results
- Timeout scenarios collect partial responses
- Failed event sends are tracked and reported

## Advanced Features

### Correlation Tracking
- Unique await_id generation prevents response collision
- Safe for multiple concurrent await operations
- Enables complex workflow orchestration patterns

### Partial Response Handling
- Timeout doesn't discard collected responses
- Enables best-effort processing patterns
- Useful for fault-tolerant distributed processing

### Dynamic Timeout
- Runtime timeout override via input socket
- Widget provides default timeout value
- Balances user control with sensible defaults

## Performance Considerations
- Async implementation prevents blocking other workflows
- Memory usage scales with number of parallel requests
- EventManager handles response routing efficiently
- Consider timeout values based on expected processing time

## Common Use Cases
- **Distributed Processing**: Send work to multiple parallel processors
- **Service Orchestration**: Coordinate multiple service-like workflows
- **Data Aggregation**: Collect processed results from multiple sources
- **Load Distribution**: Distribute work and collect results
- **Validation Workflows**: Send data for multiple validation checks
- **Parallel Analysis**: Run multiple analysis algorithms simultaneously

## Error Scenarios
- **Timeout**: Returns partial results with debug message
- **No EventManager**: Returns empty results with warning
- **No Responses**: Returns empty array if no workflows respond
- **Partial Responses**: Returns available responses on timeout

## Related Nodes

### Inter-Workflow Event Communication System
These nodes work together as part of the inter-workflow communication framework:
- **Receive Event Node**: Receives the events sent by this node and triggers processing workflows
- **Return Event Data Node**: Sends responses back to this node to complete the await cycle
- **Send Event Node**: Simpler one-way event sending (this node extends Send Event functionality)

### Other Event System Nodes
- **Display Input Event Node**: UI interaction events (not inter-workflow communication)
- **Webhook Node**: External HTTP events (not inter-workflow communication)

## Tips & Best Practices
- Set reasonable timeout values based on expected processing time
- Use descriptive event IDs for easier debugging and monitoring
- Consider partial response handling in your workflow logic
- Test timeout scenarios to ensure graceful degradation
- Monitor sent_count to verify successful event distribution
- Design target workflows to always send responses to prevent hanging
- Use unique event IDs to avoid cross-workflow interference