---
title: "Add Node"
description: "Performs addition of two numeric values"
category: "Math"
tags: ["math", "addition", "arithmetic", "basic"]
author: "AI Node Builder"
version: "1.0.0"
---

# Add Node

## Overview
The Add Node performs basic addition of two numeric inputs. It's a fundamental mathematical operation node that demonstrates the dependency socket pattern in the AI Node Builder system.

## Input Sockets
| Socket | Type | Required | Description |
|--------|------|----------|-------------|
| `a` | NUMBER | Yes (dependency) | First operand for addition |
| `b` | NUMBER | Yes (dependency) | Second operand for addition |

Both inputs are marked as dependencies, meaning the node will actively pull values from connected nodes before execution.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `result` | NUMBER | The sum of inputs a and b |

## Examples

### Basic Addition
Create two Number Nodes with values 5 and 3. Connect the first to the Add Node's `a` input and the second to the `b` input. Connect the Add Node's `result` output to a Display Node to see the sum (8).

### Chaining Operations
Use multiple Add Nodes in sequence: first add 10 + 5 = 15, then add that result + 3 = 18. This demonstrates how you can chain mathematical operations together.

### With Variable Sources
Connect a Counter Node to the `a` input and a Number Node (value: 1) to the `b` input to create an incrementing system. Each time the workflow runs, the counter increases by 1.

## Behavior & Execution

### Dependency Pattern
- Both inputs use `"is_dependency": True`
- The node waits for both inputs to be available before executing
- Values are pulled from connected nodes automatically
- If no connection is made, the input defaults to 0

### Type Conversion
- All inputs are converted to float before addition
- Integer and decimal numbers are supported
- Scientific notation is handled correctly

## Common Use Cases
- **Basic Arithmetic**: Simple addition operations
- **Accumulation**: Building running totals
- **Offset Calculations**: Adding fixed offsets to values
- **Combining Values**: Merging multiple numeric streams
- **Counter Increment**: Adding 1 to counter values

## Advanced Patterns

### Multiple Additions
For adding more than two numbers, chain multiple Add nodes:
### Multi-Input Addition
For adding multiple numbers (A + B + C + D), create several Add Nodes in sequence: first add A + B, then add that result + C, then add that result + D to get the final sum.

### Conditional Addition
Use an If Node to conditionally add a value. Connect your base value to one input of an Add Node, and use the If Node's output (either the condition value or 0) as the second input.

## Error Handling
- **Missing Inputs**: Defaults to 0 if no connection
- **Invalid Types**: Attempts automatic conversion to number
- **Overflow**: JavaScript number limits apply

## Performance Notes
- Lightweight operation with minimal computational overhead
- Dependency pulling adds slight latency compared to push-based nodes
- Suitable for real-time workflows

## Related Nodes
- **Number Node**: Provides static operands
- **Subtract Node**: Performs subtraction
- **Multiply Node**: Performs multiplication  
- **Divide Node**: Performs division
- **Counter Node**: Often used with Add for increments

## Memory & State
This node is stateless and doesn't use `self.memory` or `self.global_state`. Each execution is independent and based solely on the current input values.

## Tips & Best Practices
- Connect both inputs for predictable results
- Use Number nodes for constant values
- Chain multiple Add nodes for summing more than two values
- Consider order of operations when building complex mathematical expressions