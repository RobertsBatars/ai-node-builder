---
title: "Input Output Array Test Node"
description: "Test node validating dynamic array sockets for both inputs and outputs with SKIP_OUTPUT functionality"
category: "Test"
tags: ["test", "array", "dynamic", "sockets", "skip-output", "validation"]
author: "AI Node Builder"
version: "1.0.0"
---

# Input Output Array Test Node

## Overview
The Input Output Array Test Node is a comprehensive testing utility that validates the implementation of both input and output dynamic arrays. It demonstrates array processing, prefix addition, and the SKIP_OUTPUT functionality for selectively skipping array elements in the output.

## Input Sockets
| Socket | Type | Required | Is Dependency | Array | Description |
|--------|------|----------|---------------|-------|-------------|
| `in_array` | TEXT[] | Yes | Yes | Yes | Dynamic array of text inputs to process |

The input socket uses dynamic arrays with dependency patterns to ensure all connected array data is available before processing.

## Output Sockets
| Socket | Type | Array | Description |
|--------|------|-------|-------------|
| `out_array` | TEXT[] | Yes | Dynamic array of processed text outputs |

## Widgets
- **prefix**: Text input (default: "pre-") - Prefix to add to each input string

## Examples

### Basic Array Processing
1. Add an Input Output Array Test Node to your workflow
2. Click `+ in_array` to add multiple input slots
3. Connect Text Nodes to each array slot with different values
4. Configure the prefix widget (e.g., "processed-")
5. Connect the output array to Display Nodes to see results

### SKIP_OUTPUT Testing
1. Connect Text Nodes with various values including one with "skip"
2. The node will process most inputs normally but skip the "skip" input
3. Use this to test how the engine handles SKIP_OUTPUT in array contexts

### Array Processing Validation
Connect inputs: ["hello", "world", "skip", "test"]
With prefix "pre-":
- Output slot 0: "pre-hello"
- Output slot 1: "pre-world" 
- Output slot 2: SKIP_OUTPUT (no connection fires)
- Output slot 3: "pre-test"

## Behavior & Execution

### Array Processing Logic
- Iterates through each element in the input array
- Applies prefix to each string element
- Handles special "skip" command for SKIP_OUTPUT testing
- Returns processed array maintaining order

### SKIP_OUTPUT Functionality
- If any input string equals "skip" (case-insensitive), places SKIP_OUTPUT in that position
- SKIP_OUTPUT prevents the corresponding output slot from firing
- Demonstrates selective output control in array contexts
- Useful for testing conditional array processing

### Dependency Coordination
- Uses `is_dependency: True` on input array
- Ensures all array elements are available before processing
- Waits for complete array data before execution
- Demonstrates proper array dependency patterns

## Dynamic Array Features

### Input Array Management
- Dynamic array inputs created with `+ in_array` buttons
- Each slot can be connected independently
- Array size determined by number of connections
- Handles variable-length arrays gracefully

### Output Array Generation
- Returns processed array as dynamic output
- Each array element maps to a numbered output slot
- Output slots created automatically based on array size
- SKIP_OUTPUT elements don't create connections

### Array Synchronization
- Input and output arrays maintain element correspondence
- Processing preserves array order and structure
- Handles mixed content types within arrays
- Validates array processing patterns

## Testing Applications

### Array Socket Validation
- Tests both input and output dynamic array functionality
- Validates array dependency coordination
- Ensures proper array element processing
- Confirms dynamic socket creation and management

### SKIP_OUTPUT Testing
- Demonstrates selective output control in arrays
- Tests engine handling of skipped array elements
- Validates conditional array processing patterns
- Ensures proper downstream execution control

### Development Validation
- Verifies array socket implementation works correctly
- Tests complex array processing workflows
- Validates dependency patterns with dynamic arrays
- Ensures robust array handling in the engine

## Array Processing Patterns

### Element-by-Element Processing
```python
# Processing pattern demonstrated:
output_list = []
for item in in_array:
    if condition:
        output_list.append(SKIP_OUTPUT)
    else:
        output_list.append(process(item))
```

### Conditional Output Control
- Use "skip" input to test SKIP_OUTPUT functionality
- Demonstrates how to selectively control array outputs
- Shows proper SKIP_OUTPUT placement in arrays
- Tests engine response to mixed output types

### Array Coordination
- Input arrays collected into Python lists
- Output arrays returned as lists within tuples
- Maintains array structure and ordering
- Handles variable array sizes effectively

## Common Use Cases
- **Array Testing**: Validate dynamic array socket functionality
- **SKIP_OUTPUT Validation**: Test selective output control
- **Processing Patterns**: Demonstrate array element processing
- **Development Testing**: Verify array implementation correctness
- **Flow Control**: Test conditional array output patterns
- **Integration Testing**: Validate array coordination with engine

## Related Nodes
- **Socket Array Test Node**: Alternative array testing approach
- **Concatenate Array Node**: Production array processing
- **String Array Creator Node**: Array creation utilities
- **Text Node**: Provides input data for array testing
- **Display Output Node**: Shows processed array results

## Tips & Best Practices
- This is primarily a testing/development node, not for production workflows
- Use "skip" inputs to test SKIP_OUTPUT functionality
- Monitor both input and output arrays to understand processing
- Test with different array sizes to ensure robust handling
- Useful for learning array processing patterns
- Demonstrates proper array dependency coordination
- Good for understanding SKIP_OUTPUT behavior in array contexts

## SKIP_OUTPUT Behavior
- Input "skip" (case-insensitive) triggers SKIP_OUTPUT placement
- SKIP_OUTPUT prevents corresponding output slot from firing
- Downstream nodes connected to skipped slots won't execute
- Demonstrates conditional flow control in array processing
- Tests engine's handling of mixed output types in arrays

## Advanced Testing Scenarios
- **Variable Array Sizes**: Test with different numbers of array connections
- **Mixed Content**: Use different types of text inputs
- **Selective Skipping**: Mix normal processing with SKIP_OUTPUT
- **Empty Arrays**: Test behavior with no array connections
- **Large Arrays**: Validate performance with many array elements

## Array Dependency Patterns
The node demonstrates proper array dependency usage:
- All array inputs collected before execution
- Dependency flag ensures complete data availability
- Processing waits for all connected array elements
- Validates timing coordination in array workflows