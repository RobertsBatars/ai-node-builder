---
title: "Logging Test Node"
description: "Test node for verifying messaging and logging functionality across different message types"
category: "Test"
tags: ["test", "logging", "messages", "debug", "communication", "frontend"]
author: "AI Node Builder"
version: "1.0.0"
---

# Logging Test Node

## Overview
The Logging Test Node is a testing utility that validates the messaging and logging functionality between nodes and the frontend. It sends various types of messages to demonstrate different communication channels and verify that the messaging system works correctly across all message types.

## Input Sockets
| Socket | Type | Required | Description |
|--------|------|----------|-------------|
| `trigger` | ANY | Yes | Input that triggers the logging test sequence |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `output` | TEXT | Completion message indicating the test has finished |

## Examples

### Basic Logging Test
1. Connect any node output to the trigger input
2. Connect the output to a Display Node
3. Run the workflow to see various message types in the frontend
4. Check the console/log panel for different message categories

### Message Type Validation
Use this node to verify that all message types are properly:
- Transmitted from backend to frontend
- Displayed in the appropriate UI components
- Handled correctly by the messaging system

### Development Testing
During development, use this node to:
- Test new message types
- Verify messaging system functionality
- Debug communication issues between backend and frontend

## Behavior & Execution

### Message Sequence
The node sends messages in this sequence:
1. **LOG Message**: General informational logging
2. **DEBUG Message**: Detailed debugging information
3. **TEST_EVENT Message**: Specialized test event with status
4. **Simulated Work**: 1-second delay to demonstrate timing
5. **ERROR Message**: Simulated error for error handling testing

### Async Execution
- Uses async execution to demonstrate timing and non-blocking behavior
- Includes artificial delay to show message timing
- Proper async/await patterns for educational purposes

### Message Types Tested
- **MessageType.LOG**: General informational messages
- **MessageType.DEBUG**: Detailed debugging information
- **MessageType.TEST_EVENT**: Specialized testing events
- **MessageType.ERROR**: Error and exception reporting

## Message System Validation

### Communication Testing
Validates that the messaging system properly:
- Sends messages from nodes to the frontend
- Handles different message types correctly
- Maintains message order and timing
- Displays messages in appropriate UI components

### Frontend Integration
Tests integration between:
- Backend node execution and frontend display
- Message routing and categorization
- Real-time communication during node execution
- Error handling and display mechanisms

### Development Verification
Useful for verifying:
- New message types work correctly
- UI components display messages properly
- Message timing and ordering
- Error handling and recovery

## Message Format Examples

### Log Message
```json
{
  "type": "LOG",
  "data": {
    "message": "This is a log message from LoggingTestNode"
  }
}
```

### Debug Message
```json
{
  "type": "DEBUG", 
  "data": {
    "message": "This is a debug message with more details"
  }
}
```

### Test Event Message
```json
{
  "type": "TEST_EVENT",
  "data": {
    "message": "This is a test event",
    "status": "success"
  }
}
```

### Error Message
```json
{
  "type": "ERROR",
  "data": {
    "message": "This is a simulated error message"
  }
}
```

## Testing Applications

### Message System Testing
- Verify all message types transmit correctly
- Test message ordering and timing
- Validate frontend message display
- Ensure proper error handling

### Development Validation
- Test new messaging features
- Verify communication channels work
- Debug frontend integration issues
- Validate message routing logic

### Integration Testing
- Test backend-to-frontend communication
- Verify message categorization works
- Ensure proper UI component integration
- Test real-time message updates

## Async Execution Patterns

### Non-Blocking Messages
Demonstrates how nodes can send messages without blocking execution:
- Messages sent asynchronously to frontend
- Execution continues while messages are transmitted
- Proper async/await usage patterns
- Simulated work with timing delays

### Message Timing
Shows how to:
- Send messages at different points during execution
- Include timing delays for demonstration
- Maintain execution flow while communicating
- Handle async operations properly

## Common Use Cases
- **Framework Testing**: Validate messaging system functionality
- **Development Debugging**: Test communication between backend and frontend
- **Message Validation**: Verify all message types work correctly
- **UI Testing**: Ensure frontend displays messages properly
- **Integration Testing**: Test complete message flow from node to UI
- **Educational**: Demonstrate messaging patterns for developers

## Related Nodes
- **Log Node**: Production logging functionality
- **Display Output Node**: For showing results and messages
- **Counter Node**: Another testing node with different patterns
- **Assert Node**: For validating test results
- **Debug nodes**: For development and testing workflows

## Tips & Best Practices
- This is primarily a testing/development node, not for production workflows
- Use to verify messaging system works correctly after changes
- Monitor the frontend console/log panel for message display
- Useful for debugging communication issues
- Test new message types by modifying this node
- Educational tool for learning messaging patterns
- Validate frontend integration during development

## Message Categories

### Informational Messages
- **LOG**: General information and status updates
- **DEBUG**: Detailed diagnostic and debugging information

### Event Messages  
- **TEST_EVENT**: Specialized events for testing with additional metadata

### Error Messages
- **ERROR**: Error conditions, exceptions, and failure notifications

## Development Applications

### Testing New Features
- Add new message types to validate they work
- Test message routing and categorization
- Verify UI components handle new message types
- Debug integration issues

### Communication Validation
- Ensure messages reach the frontend correctly
- Verify proper message formatting and structure
- Test real-time communication during execution
- Validate error handling and recovery

### Educational Use
- Demonstrate proper messaging patterns
- Show async execution with communication
- Teach frontend-backend integration concepts
- Illustrate message timing and ordering

## Frontend Integration Notes
- Messages should appear in appropriate UI components
- Log and debug messages typically appear in console/log panels
- Error messages may trigger special error handling UI
- Test events might have specialized display handling
- Timing demonstrates real-time communication capabilities