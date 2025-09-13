---
title: "Calculator Tool Node"
description: "Provides mathematical calculation capabilities to LLM nodes"
category: "Tools"
tags: ["tools", "math", "calculator", "functions"]
author: "AI Node Builder"
version: "1.0.0"
---

# Calculator Tool Node

## Overview
The Calculator Tool Node provides mathematical calculation capabilities that can be used by LLM nodes. It implements a function calling interface that allows language models to perform precise mathematical operations.

## Input Sockets
This node has no input sockets - it generates tool definitions based on its configuration.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `tool_definition` | ANY | Tool definition object for LLM function calling |

## Widgets
This node has no configurable widgets - it provides a fixed calculator tool definition.

## Tool Definition
The node outputs a tool definition that includes:
```json
{
  "type": "function",
  "function": {
    "name": "calculator",
    "description": "Evaluate mathematical expressions and return results",
    "parameters": {
      "type": "object", 
      "properties": {
        "expression": {
          "type": "string",
          "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')"
        }
      },
      "required": ["expression"]
    }
  }
}
```

## Mathematical Capabilities
The calculator supports:
- **Basic Operations**: +, -, *, /
- **Parentheses**: For operation precedence
- **Decimal Numbers**: Floating-point arithmetic
- **Scientific Notation**: 1e6, 2.5e-3, etc.
- **Common Functions**: sin, cos, tan, sqrt, log, exp
- **Constants**: pi, e

## Examples

### Basic LLM Integration
Connect the Calculator Tool Node to an LLM Node's tools input, then send a Text Node with "What is 15 * 7 + 3?" to the LLM's prompt. The LLM will automatically use the calculator to compute the result (108).

### Complex Mathematical Queries
Connect the Calculator Tool to an LLM and ask "Calculate the area of a circle with radius 5". The LLM will use the calculator with the formula `pi * 5 * 5` and return 78.54.

### Multiple Calculations
Ask the LLM to "Compare 2^8 vs 3^5" - it will make multiple calculator calls to compute both values and provide a comparison.
LLM might make multiple tool calls:
- `calculator(expression: "2**8")` → 256
- `calculator(expression: "3**5")` → 243

## Supported Expressions

### Basic Arithmetic
- `2 + 3` → 5
- `10 - 4` → 6
- `6 * 7` → 42
- `15 / 3` → 5

### Advanced Operations
- `2**3` → 8 (exponentiation)
- `sqrt(16)` → 4
- `sin(pi/2)` → 1
- `log(10)` → 2.3026 (natural log)

### Complex Expressions
- `(2 + 3) * (4 - 1)` → 15
- `sqrt(2**2 + 3**2)` → 3.606 (Pythagorean theorem)

## Error Handling
The calculator handles various error conditions:
- **Syntax Errors**: Invalid mathematical expressions
- **Division by Zero**: Returns appropriate error message
- **Undefined Functions**: Unknown function names
- **Domain Errors**: sqrt of negative numbers, etc.

## Usage Patterns

### Single Tool Connection
```
[Calculator Tool] → [LLM Node.tools]
```
Most common pattern for basic math capabilities.

### Multiple Tool Usage
Connect each tool directly to its own LLM tools input socket (dynamic array) AND connect the LLM's tool_calls output to each tool's input:

**Tool to LLM connections:**
1. Calculator Tool → LLM Node tools[0]
2. Weather Tool → LLM Node tools[1]  
3. Web Search Tool → LLM Node tools[2]

**LLM to Tool connections (for execution):**
1. LLM Node tool_calls → Calculator Tool input
2. LLM Node tool_calls → Weather Tool input
3. LLM Node tool_calls → Web Search Tool input

The LLM Node automatically creates additional tool input sockets as needed. Each tool requires BOTH connections: one to provide its definition to the LLM, and one to receive tool calls from the LLM for execution.

### Conditional Tool Availability
Use a Conditional Node to determine whether to provide the Calculator Tool to the LLM based on user permissions or context. Connect the Calculator Tool through the conditional logic to the LLM's tools input.

## Implementation Details

### Security Features
- Expression evaluation is sandboxed
- Only mathematical operations are allowed
- No file system or network access
- Limited to safe mathematical functions

### Performance
- Lightweight expression evaluation
- Minimal memory usage
- Fast response times for most calculations
- Handles complex expressions efficiently

## Related Nodes
- **LLM Node**: Primary consumer of tool definitions
- **Text Analysis Tool**: For text processing capabilities
- **Weather Tool**: Another example tool node
- **Array Nodes**: For combining multiple tools

## Common Use Cases
- **Educational Content**: Math tutoring and problem solving
- **Data Analysis**: Quick calculations on data sets
- **Engineering**: Formula calculations and conversions
- **Financial**: Interest, loan, and investment calculations
- **Scientific**: Physics and chemistry calculations

## Troubleshooting

### Common Issues
- **Expression Errors**: Check mathematical syntax
- **Function Not Found**: Verify function names (sin, cos, sqrt, etc.)
- **Precision Issues**: Floating-point limitations may affect very large numbers
- **Tool Not Called**: Ensure LLM understands when to use calculations

### Debug Tips
- Test expressions manually to verify syntax
- Check LLM tool calling is enabled
- Verify tool definition is properly connected
- Monitor LLM responses for tool usage patterns

## Advanced Configuration
While this node has no widgets, you can extend its functionality by:
- Creating custom tool nodes with additional mathematical functions
- Combining with other tool nodes for comprehensive capabilities
- Using conditional logic to provide tools based on context

## Memory & State
This node is stateless and doesn't use `self.memory` or `self.global_state`. Each tool call is independent and doesn't retain calculation history.