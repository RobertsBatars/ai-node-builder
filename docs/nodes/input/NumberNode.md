---
title: "Number Input Node"
description: "Provides static numeric input to workflows"
category: "Input"
tags: ["input", "number", "basic", "math"]
author: "AI Node Builder"
version: "1.0.0"
---

# Number Input Node

## Overview
The Number Input Node provides static numeric values to your workflows. It's essential for mathematical operations, configuration parameters, and any workflow that requires numeric input.

## Input Sockets
This node has no input sockets - it generates output based on its widget value.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `number_out` | NUMBER | The numeric value configured in the widget |

## Widgets
- **value**: Number input widget (default: 10)
  - Accepts integer and floating-point numbers
  - Supports negative values
  - Can be used for counts, thresholds, parameters, etc.

## Examples

### Basic Usage
1. Add a Number Node to your workflow
2. Set the desired numeric value in the widget
3. Connect the `number_out` socket to any node that accepts numeric input

### Mathematical Operations
Create two Number Nodes with values 5 and 3, then connect both to an Add Node's inputs. Connect the Add Node's result to a Display Node to see the sum (8).

### Configuration Parameters
Use Number Nodes to set LLM parameters: one Number Node with value 100 connected to max_tokens, another with 0.7 connected to temperature.

## Common Use Cases
- **Math Operations**: Provide operands for Add, Subtract, Multiply, Divide nodes
- **Loop Counters**: Define iteration counts for loop-based workflows
- **Thresholds**: Set comparison values for conditional logic
- **Configuration**: Store numeric settings and parameters

## Data Type Handling
- The node outputs values as numbers (float type)
- Integer inputs are automatically converted to float
- Scientific notation is supported (e.g., 1e6 for 1,000,000)
- Very large or small numbers are handled appropriately

## Tips & Best Practices
- Use meaningful values that make your workflow self-documenting
- For parameters like temperature, use standard ranges (0.0-2.0)
- Consider using separate number nodes for different parameter types
- Remember that changing the value will trigger downstream re-execution

## Related Nodes
- **Text Node**: For string input values
- **Add Node**: Combines two numbers
- **Math Nodes**: Various mathematical operations
- **Comparison Nodes**: Compare numbers for conditional logic
- **LLM Node**: Accepts numeric parameters

## Memory & State
This node is stateless and doesn't use `self.memory` or `self.global_state`. The output is purely determined by the widget value.

## Troubleshooting
- **Invalid Input**: Ensure the widget contains a valid number
- **Type Errors**: Some nodes may expect integers - check node documentation
- **Precision**: Floating-point arithmetic may have precision limitations for very large numbers