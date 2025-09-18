---
title: "Return Event Data Node"
description: "Returns data back to awaiting workflows to complete request/response cycles"
category: "Events"
tags: ["events", "communication", "return", "response", "correlation"]
author: "AI Node Builder"
version: "1.0.0"
---

# Return Event Data Node

## Overview
The Return Event Data Node is part of the **inter-workflow event communication system** and completes the await/response cycle by sending processed data back to workflows that are waiting for responses. It uses correlation IDs to ensure responses reach the correct awaiting workflow, enabling reliable request/response patterns across parallel workflows.

This node works together with ReceiveEventNode, SendEventNode, and AwaitEventNode to form a complete inter-workflow communication framework managed by the EventManager.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `return_data` | ANY | Yes | No | The processed data to return to the awaiting workflow |
| `await_id` | TEXT | Yes | No | Correlation ID received from the Receive Event Node |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `confirmed` | TEXT | Confirmation message indicating success or failure of the return operation |

## Examples

### Basic Response Pattern
1. Receive Event Node outputs await_id
2. Process the received data through your workflow
3. Connect processed result to return_data and await_id to await_id input
4. The Return Event Data Node sends the response back to the waiting workflow

### Data Processing Service
Create a service-like workflow: Receive Event Node → processing nodes → Return Event Data Node. This workflow can process requests and return results to multiple different awaiting workflows.

### Multi-Step Response
Chain multiple processing steps before returning: Receive Event → Process A → Process B → Return Event Data. The await_id flows through the entire chain to maintain correlation.

### Conditional Responses
Use Decision Nodes to determine what data to return based on processing results, while always using the same await_id for correlation.

## Behavior & Execution

### Correlation Handling
- Uses await_id to identify the correct awaiting workflow
- Maintains response correlation across complex parallel execution
- Ensures responses reach their intended recipients

### Response Delivery
- Sends return_data through EventManager to awaiting workflow
- Uses await_id for precise routing
- Provides confirmation of successful delivery

### Error Handling
- Missing await_id results in error message
- Failed delivery attempts are reported
- Missing EventManager results in warning and failure status

### Confirmation Messages
- **Success**: "Data returned successfully" 
- **Failure**: "Failed to return data"
- **Error**: "Error: No await_id provided"

## Integration Requirements

### With Receive Event Node
The await_id must originate from a Receive Event Node that received an await-enabled event. The correlation ID flows through the workflow to maintain the response connection.

### With Await Event Node
The target Await Event Node must be actively waiting for responses. The EventManager routes the response using the await_id correlation.

### Workflow Design
- await_id must flow through the entire processing workflow
- Return Event Data Node should be the final step in response workflows
- Each request should have exactly one corresponding response

## Response Flow

### Step 1: Correlation Preservation
- Receive await_id from upstream Receive Event Node
- Maintain correlation ID through processing workflow
- Ensure await_id reaches Return Event Data Node

### Step 2: Data Preparation
- Process input data through workflow logic
- Prepare final result for return to awaiting workflow
- Connect processed result to return_data input

### Step 3: Response Transmission
- EventManager routes response using await_id
- Response data is delivered to waiting Await Event Node
- Confirmation status is returned to this workflow

### Step 4: Completion
- Await Event Node receives the response
- Request/response cycle is complete
- Both workflows can continue independently

## Advanced Patterns

### Service Workflows
Design workflows that act like services: always start with Receive Event Node and end with Return Event Data Node for consistent request/response behavior.

### Error Response Handling
Return error messages or status codes when processing fails, ensuring the awaiting workflow doesn't timeout waiting for a response.

### Data Transformation Services
Create specialized workflows that receive data, transform it, and return the transformed result, acting as reusable processing services.

## Correlation ID Management

### ID Preservation
- await_id must be preserved throughout the workflow
- Use passthrough patterns or memory to maintain correlation
- Never modify or regenerate the await_id

### Unique Responses
- Each await_id should be used exactly once for response
- Multiple responses to the same await_id may cause undefined behavior
- Design workflows to ensure single response per request

## Common Use Cases
- **Data Processing Services**: Return processed results to requesting workflows
- **Validation Services**: Return validation results and status
- **Computation Services**: Perform calculations and return results
- **External API Wrappers**: Wrap external services in await/response patterns
- **Database Query Services**: Execute queries and return results
- **File Processing Services**: Process files and return status or results

## Error Conditions
- **Missing await_id**: Cannot route response, returns error message
- **Invalid await_id**: Response fails to deliver
- **No EventManager**: Cannot send response, returns failure status
- **No awaiting workflow**: Response may be discarded

## Performance Considerations
- Lightweight operation with minimal overhead
- Response delivery is asynchronous and non-blocking
- EventManager handles routing efficiently
- Memory usage is minimal per response

## Integration Patterns

### Simple Service Pattern
A basic service workflow follows this pattern: start with a Receive Event Node to get requests, perform processing operations in the middle, and end with a Return Event Data Node to send responses back to the awaiting workflow.

### Complex Processing Pattern
For workflows with conditional logic, use a Decision Node after receiving the event. Based on the decision outcome, route the request through different processing paths (Processing A or Processing B), but ensure both paths eventually lead to a Return Event Data Node to provide a response.

### Error Handling Pattern
Implement robust error handling by attempting the main processing first. If processing succeeds, return the successful result. If processing fails, catch the error and return an error response instead of leaving the awaiting workflow hanging without a response.

## Related Nodes

### Inter-Workflow Event Communication System
These nodes work together as part of the inter-workflow communication framework:
- **Receive Event Node**: Provides the initial await_id for correlation and receives events
- **Await Event Node**: Receives the data returned by this node to complete the response cycle  
- **Send Event Node**: Basic one-way event sending (Await Event extends this for responses)

### Other Workflow Nodes
- **Decision Node**: For conditional response logic and routing
- **Display Input Event Node**: UI interaction events (not inter-workflow communication)
- **Webhook Node**: External HTTP events (not inter-workflow communication)

## Tips & Best Practices
- Always preserve the await_id throughout your workflow
- Design workflows to always send a response, even for errors
- Use meaningful response data that helps the awaiting workflow
- Test response delivery by monitoring confirmation messages
- Consider timeout implications when designing processing workflows
- Use consistent response formats for easier consumption
- Handle errors gracefully by returning error status rather than failing silently