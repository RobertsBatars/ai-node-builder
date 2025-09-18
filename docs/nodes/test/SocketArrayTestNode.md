---
title: "Socket Array Test Node"
description: "Test node demonstrating dynamic array sockets with dependency patterns"
category: "Test"
tags: ["test", "array", "sockets", "dynamic", "dependencies"]
author: "AI Node Builder"
version: "1.0.0"
---

# Socket Array Test Node

## Overview
The Socket Array Test Node is a testing utility that demonstrates the dynamic array socket feature combined with dependency patterns. It showcases how multiple dynamic array inputs can be used together with dependency pulling to ensure all data is available before execution.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `texts_1` | TEXT[] | Yes | Yes | First dynamic array of text inputs |
| `texts_2` | TEXT[] | Yes | Yes | Second dynamic array of text inputs |
| `dependency` | ANY | Yes | Yes | Additional dependency input for testing dependency coordination |

All inputs use dependency patterns to ensure they are pulled and available before execution.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `output_1` | TEXT | Comma-separated concatenation of texts_1 array |
| `output_2` | TEXT | Comma-separated concatenation of texts_2 array |

## Examples

### Array Socket Testing
1. Add multiple connections to both texts_1 and texts_2 arrays using the `+` buttons
2. Connect Text Nodes to each array slot
3. Connect any node to the dependency input
4. The node will wait for all inputs and output concatenated results

### Dependency Coordination Testing
Use this node to test how the engine coordinates multiple dependency inputs, ensuring all data is available before execution begins.

### Array Processing Patterns
Demonstrates how to process multiple dynamic arrays in a single node while maintaining dependency relationships.

## Behavior & Execution

### Array Processing
- Both dynamic arrays are collected into Python lists
- Each array is processed by joining elements with commas
- Handles arrays of different lengths gracefully

### Dependency Coordination
- All three inputs use `is_dependency: True`
- Node waits for all dependencies to be ready
- Demonstrates multi-input dependency patterns

### Execution Logic
- Concatenates texts_1 array elements with ", " separator
- Concatenates texts_2 array elements with ", " separator
- Logs the dependency value for testing purposes
- Returns both concatenated strings

## Array Socket Features

### Dynamic Addition
- Use `+ texts_1` and `+ texts_2` buttons to add array slots
- Each slot can be connected independently
- Arrays can have different numbers of connections

### Dependency Pulling
- Engine automatically pulls data from all connected array inputs
- Ensures complete data availability before execution
- Coordinates timing across multiple dynamic inputs

## Testing Applications

### Development Testing
- Verify array socket functionality works correctly
- Test dependency coordination mechanisms
- Validate multi-array processing patterns

### Array Processing Validation
- Confirm array data collection and processing
- Test edge cases with different array sizes
- Validate dependency timing coordination

### Socket Configuration Testing
- Verify complex socket configurations work properly
- Test combinations of arrays and dependencies
- Validate engine dependency resolution

## Common Use Cases
- **Framework Testing**: Validate array socket functionality
- **Dependency Testing**: Test multi-input dependency coordination
- **Array Processing**: Demonstrate array concatenation patterns
- **Development Validation**: Ensure complex socket configurations work
- **Integration Testing**: Test array and dependency combinations

## Related Nodes
- **Text Node**: Provides inputs for array testing
- **String Array Creator Node**: Alternative array processing approach
- **Concatenate Array Node**: Production array concatenation
- **Other test nodes**: Part of comprehensive testing suite

## Tips & Best Practices
- This is primarily a testing/development node, not for production workflows
- Use to validate array socket behavior during development
- Test with different array sizes to ensure robust handling
- Monitor console output to see dependency coordination in action
- Useful for understanding how dependency patterns work with arrays