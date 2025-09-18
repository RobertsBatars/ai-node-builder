---
title: "Decision Node"
description: "Routes input to one of two outputs based on a comparison condition"
category: "Conditional"
tags: ["conditional", "decision", "routing", "comparison", "logic", "flow-control"]
author: "AI Node Builder"
version: "1.0.0"
---

# Decision Node

## Overview
The Decision Node implements conditional routing by comparing two values and directing the input to one of two output paths based on the comparison result. It supports multiple comparison operators and handles both numeric and string comparisons automatically.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `input_value` | NUMBER | Yes | Yes | The primary value to route based on comparison |
| `comparison_value` | NUMBER | Yes | Yes | The value to compare against |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `true_output` | ANY | Receives the input value when comparison is true |
| `false_output` | ANY | Receives the input value when comparison is false |

## Widgets
- **operator**: Combo (default: "==") - The comparison operator to use
  - Options: "==", "!=", ">", "<", ">=", "<="
  - Determines the type of comparison performed

## Comparison Operators

### Equality Operators
- **==** (Equal): True when both values are equal
- **!=** (Not Equal): True when values are different

### Relational Operators
- **>** (Greater Than): True when input_value > comparison_value
- **<** (Less Than): True when input_value < comparison_value
- **>=** (Greater Than or Equal): True when input_value >= comparison_value
- **<=** (Less Than or Equal): True when input_value <= comparison_value

## Examples

### Basic Numeric Comparison
1. Connect a Number Node (value: 10) to `input_value`
2. Connect another Number Node (value: 5) to `comparison_value`
3. Set operator to ">"
4. Connect Display Nodes to both outputs
5. The input value (10) will route to `true_output` since 10 > 5

### Threshold Testing
Use a Counter Node connected to `input_value`, a Number Node with threshold value connected to `comparison_value`, and set operator to ">=" to detect when a counter reaches a threshold.

### String Comparison
Connect Text Nodes to both inputs for alphabetical comparison:
- Text Node "apple" → `input_value`
- Text Node "banana" → `comparison_value`
- Operator "<" will route "apple" to `true_output` (alphabetically less)

### Workflow Branching
Create a data source node and connect it to the Decision Node's input_value. Connect different processing nodes to the true_output and false_output paths. Based on the comparison result, the data will flow to either Process A (via true_output) or Process B (via false_output), but never both.

## Behavior & Execution

### Type Handling
- **Numeric Comparison**: Attempts to convert inputs to float for mathematical comparison
- **String Fallback**: If numeric conversion fails, compares as strings
- **Mixed Types**: Converts both to strings for consistent comparison

### Output Routing
- Uses `SKIP_OUTPUT` to prevent execution of the inactive path
- Only one output fires per execution, never both
- The routing decision is made immediately based on comparison

### Dependency Pattern
- Both inputs use dependency pulling to ensure values are available
- Comparison happens when both values are ready
- Node waits for both inputs before executing

## Comparison Logic Details

### Numeric Comparisons
When both values can be converted to numbers:
- Performs mathematical comparison (10.5 > 10)
- Handles integers and floats correctly
- More precise than string comparison for numbers

### String Comparisons
When numeric conversion fails or for mixed types:
- Uses lexicographic (alphabetical) ordering
- Case-sensitive comparison
- Useful for text sorting and categorization

### Error Handling
- Invalid conversions gracefully fall back to string comparison
- No exceptions thrown for type mismatches
- Consistent behavior regardless of input types

## Common Use Cases
- **Threshold Detection**: Route data when values exceed limits
- **Data Filtering**: Send data down different paths based on criteria
- **Workflow Branching**: Create conditional execution paths
- **Quality Control**: Route data based on quality metrics
- **State Machines**: Implement conditional state transitions
- **Data Validation**: Separate valid from invalid data

## Advanced Patterns

### Multi-Stage Decisions
Chain multiple Decision Nodes for complex logic by connecting the output of one Decision Node to the input of subsequent Decision Nodes. For example, connect the true_output of Decision 1 to Decision 2's input, and the false_output of Decision 1 to Decision 3's input. This creates a tree-like decision structure with multiple final outcomes.

### Threshold Cascading
Use multiple Decision Nodes with different thresholds:
- First checks if value > 100 (high priority)
- Second checks if value > 50 (medium priority)
- Remaining goes to low priority path

### Loop Control
Combine with Counter and loop-back connections for iteration control based on conditions.

## Related Nodes
- **Number Node**: Provides comparison values and thresholds
- **Counter Node**: Common source for threshold testing
- **Text Node**: For string-based comparisons
- **Add/Math Nodes**: Generate calculated values for comparison
- **Loop Nodes**: For conditional iteration patterns

## Tips & Best Practices
- Use numeric comparison when possible for mathematical accuracy
- String comparison is useful for text categorization and sorting
- Consider the data types when choosing comparison operators
- Test edge cases like equal values and type mismatches
- Use meaningful threshold values that make sense for your data
- Remember that only one output path executes per run
- Chain multiple Decision Nodes for complex conditional logic