---
title: "Dictionary Set Element Node"
description: "Sets or updates dictionary elements with immutable operations"
category: "Dictionary"
tags: ["dictionary", "update", "set", "immutable", "key-value"]
author: "AI Node Builder"
version: "1.0.0"
---

# Dictionary Set Element Node

## Overview
The Dictionary Set Element Node creates new dictionaries with updated or added elements. It performs immutable operations, meaning it creates a new dictionary rather than modifying the original, ensuring data integrity and preventing unintended side effects in your workflows.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `dictionary` | DICTIONARY | Yes | Yes | The source dictionary to update |
| `value` | ANY | Yes | Yes | The value to set for the specified key |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `updated_dictionary` | DICTIONARY | New dictionary with the element set/updated |

## Widgets
- **key_to_set**: Text input widget (default: "new_key")
  - Specifies the key name for the element to set or update
  - Must be a non-empty string
  - Creates new key if it doesn't exist, updates existing key if it does

## Examples

### Adding New Elements
1. Connect a Dictionary Input Node with `{"name": "Alice", "age": 25}` to the dictionary input
2. Set key_to_set widget to "email"
3. Connect a Text Node with "alice@example.com" to the value input
4. Connect the `updated_dictionary` output to a Display Node to see the result: `{"name": "Alice", "age": 25, "email": "alice@example.com"}`

### Updating Existing Elements
1. Use the same source dictionary `{"name": "Alice", "age": 25}`
2. Set key_to_set widget to "age" (existing key)
3. Connect a Number Node with value 26 to the value input
4. The result will be: `{"name": "Alice", "age": 26}` with the age updated

### Building Dictionaries Incrementally
Chain multiple Dictionary Set Element Nodes to build complex dictionaries:
1. Start with an empty dictionary `{}`
2. First node adds "name": "Bob"
3. Second node (using output from first) adds "age": 30
4. Third node adds "active": true
5. Final result: `{"name": "Bob", "age": 30, "active": true}`

### Dynamic Key Setting
Use variable key names by connecting the workflow to update different keys based on conditions:
1. Use conditional logic to determine which key to update
2. Connect different value sources based on the key being set
3. Create flexible data update workflows that adapt to different scenarios

## Value Type Handling

### Supported Value Types
- **Strings**: Text values are stored directly
- **Numbers**: Both integers and floating-point numbers are preserved
- **Other Types**: Automatically converted to strings for compatibility

### Type Conversion
The node automatically handles type conversion to ensure dictionary compatibility:
- Complex objects are converted to string representations
- Boolean values become "True" or "False" strings
- None values become "None" strings
- Arrays and nested objects are converted to string format

## Immutable Operations

### Why Immutable?
- **Data Integrity**: Original dictionaries remain unchanged
- **Workflow Safety**: Prevents accidental data corruption
- **Debugging**: Clear data flow with distinct input and output
- **Concurrency**: Safe for parallel workflow execution

### Memory Considerations
- Creates new dictionary objects for each operation
- Original dictionary memory is preserved
- Efficient copying for small to medium dictionaries
- Consider memory usage for very large dictionaries

## Error Handling

### Input Validation
- **Invalid Dictionary**: If input is not a dictionary, returns the original input unchanged
- **Empty Key**: Displays error message and returns original dictionary unchanged
- **Missing Inputs**: Node waits for both dictionary and value inputs before executing

### Graceful Degradation
The node prioritizes workflow continuity:
- Invalid inputs result in original data passthrough
- Error messages are sent to frontend for user awareness
- Workflow execution continues with fallback behavior

## Tips & Best Practices

### Key Naming
- Use descriptive, consistent key names
- Follow naming conventions (camelCase or snake_case)
- Avoid special characters that might cause issues
- Keep key names concise but meaningful

### Value Management
- Be aware of automatic type conversion for complex values
- Use appropriate input nodes (Text, Number) for specific data types
- Consider string representation for complex data structures
- Validate critical values before setting

### Workflow Design
- Chain multiple set operations for complex dictionary building
- Use conditional logic to set different keys based on conditions
- Combine with Dictionary Get Element for read-modify-write patterns
- Consider using loops for bulk dictionary updates

## Common Use Cases

### Configuration Building
Create configuration dictionaries by setting multiple parameters:
- Build API configurations with endpoints, keys, and timeouts
- Create user preference objects with various settings
- Assemble application configuration from multiple sources

### Data Transformation
Transform data structures by updating specific fields:
- Update user profiles with new information
- Modify data records with calculated values
- Add metadata to existing data structures

### State Management
Maintain application state through dictionary updates:
- Track workflow progress with status indicators
- Update counters and metrics in state objects
- Manage feature flags and configuration switches

### Batch Processing
Process multiple data updates in sequence:
- Update multiple fields in user records
- Apply bulk transformations to data sets
- Build complex objects from individual components

## Related Nodes
- **Dictionary Input Node**: Creates initial dictionaries to update
- **Dictionary Get Element Node**: Retrieves values before updating
- **Text Node**: Provides string values for setting
- **Number Node**: Provides numeric values for setting
- **Display Node**: Shows the resulting updated dictionaries

## Memory & State
This node is stateless and doesn't use `self.memory` or `self.global_state`. Each execution creates a new dictionary independently without maintaining internal state.

## Advanced Usage

### Conditional Updates
Combine with conditional logic to update dictionaries based on conditions:
1. Use Decision Nodes to determine when to update
2. Apply different update strategies based on data content
3. Create complex update workflows with multiple paths

### Loop-Based Updates
Use loops to apply multiple updates to the same dictionary:
1. Set up looping structures for iterative updates
2. Process arrays of updates sequentially
3. Build complex dictionaries through repeated operations

### Data Pipeline Integration
Integrate with larger data processing pipelines:
1. Use as part of ETL (Extract, Transform, Load) workflows
2. Apply updates as part of data validation processes
3. Combine with external data sources for enrichment

## Troubleshooting

### Common Issues
- **No output**: Verify both dictionary and value inputs are connected
- **Original unchanged**: Check that key_to_set widget has a valid value
- **Type issues**: Be aware of automatic string conversion for complex values
- **Memory concerns**: Monitor memory usage with very large dictionaries

### Debug Strategies
- Use Display Nodes to examine input and output dictionaries
- Check the key_to_set widget value for correctness
- Verify input types match expectations
- Test with simple values before using complex inputs

### Error Messages
- "Key cannot be empty" - The key_to_set widget is empty or contains only whitespace
- Type conversion warnings appear in frontend when complex values are converted to strings

### Performance Tips
- For multiple updates, chain nodes efficiently rather than parallel processing
- Consider the order of operations for dependent updates
- Use appropriate input types to minimize unnecessary conversions
- Monitor memory usage for workflows with many dictionary operations