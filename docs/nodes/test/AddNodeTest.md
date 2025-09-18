---
title: "Add Node Test"
description: "Simple test node demonstrating basic mathematical operations and dependency patterns"
category: "Test"
tags: ["test", "math", "addition", "dependencies", "validation"]
author: "AI Node Builder"
version: "1.0.0"
---

# Add Node Test

## Overview
The Add Node Test is a simple testing utility that demonstrates basic mathematical operations using the dependency pattern. It adds two numbers together, showcasing how nodes can pull data from multiple independent sources before execution.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `a` | NUMBER | Yes | Yes | First number to add |
| `b` | NUMBER | Yes | Yes | Second number to add |

Both inputs use dependency patterns to ensure both numbers are available before the addition is performed.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `result` | NUMBER | Sum of the two input numbers |

## Examples

### Basic Addition Testing
1. Connect two Number Nodes to the `a` and `b` inputs
2. Set different values in each Number Node (e.g., 5 and 3)
3. Connect the `result` output to a Display Node
4. Run the workflow to see the sum (8)

### Dependency Validation
Use this node to test dependency coordination:
- Connect Number Nodes that are not part of the main execution flow
- Verify the node waits for both inputs before executing
- Confirm the addition is performed correctly

### Mathematical Workflow Testing
Chain multiple Add Node Test instances to test complex mathematical workflows and validate calculation chains.

## Behavior & Execution

### Dependency Coordination
- Both inputs use `is_dependency: True`
- Node waits for both numbers to be available
- Demonstrates multi-input dependency patterns
- Perfect for testing pull-based data flow

### Mathematical Operation
- Performs simple addition: `a + b`
- Returns the numeric result
- Handles both integer and floating-point numbers
- No error handling for invalid input types

### Execution Logic
- Pulls data from both dependency inputs
- Adds the two numbers together
- Returns the result as a single output
- Simple, predictable behavior for testing

## Testing Applications

### Basic Functionality Testing
- Verify mathematical operations work correctly
- Test dependency coordination mechanisms
- Validate node execution with multiple inputs

### Dependency Pattern Testing
- Demonstrate how dependency inputs work
- Test timing coordination between independent inputs
- Validate pull-based data flow patterns

### Integration Testing
- Test mathematical workflow chains
- Validate numeric data type handling
- Ensure proper execution order

## Mathematical Validation

### Input Handling
- Accepts any numeric values (integer or float)
- Processes both inputs simultaneously
- No validation of input types (assumes NUMBER socket enforcement)

### Calculation Accuracy
- Performs standard Python addition
- Maintains numeric precision
- Returns result in appropriate numeric format

### Edge Cases
- Works with negative numbers
- Handles zero values correctly
- Supports decimal/floating-point arithmetic

## Common Use Cases
- **Framework Testing**: Validate basic mathematical operations
- **Dependency Testing**: Test multi-input coordination patterns
- **Workflow Validation**: Verify mathematical workflow chains
- **Development Testing**: Ensure numeric processing works correctly
- **Integration Testing**: Test mathematical node combinations

## Related Nodes
- **Number Node**: Provides numeric inputs for testing
- **Add Node**: Production mathematical addition node
- **Counter Node**: Another testing node with different patterns
- **Assert Node**: For validating calculation results
- **Display Output Node**: For showing calculation results

## Tips & Best Practices
- This is primarily a testing/development node, not for production workflows
- Use to understand how dependency patterns work with multiple inputs
- Compare with the production Add Node to see differences
- Good for learning basic mathematical node patterns
- Useful for testing numeric data flow in workflows
- Remember both inputs are required before execution begins

## Dependency Pattern Example
This node demonstrates the classic pattern where a mathematical operation requires multiple inputs to be present simultaneously. Both inputs use `is_dependency: True` to ensure the node has all required data before performing the calculation, rather than trying to execute with only one input available.