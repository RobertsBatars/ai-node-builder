---
title: "Dictionary Get Element Node"
description: "Retrieves values from dictionaries by key with comprehensive error handling"
category: "Dictionary"
tags: ["dictionary", "access", "key-value", "lookup", "error-handling"]
author: "AI Node Builder"
version: "1.0.0"
---

# Dictionary Get Element Node

## Overview
The Dictionary Get Element Node retrieves values from dictionary data structures using a specified key. It provides robust error handling with dual output approach - either returning the requested value or providing detailed error information when the operation fails.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `dictionary` | DICTIONARY | Yes | Yes | The dictionary to retrieve the element from |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `value` | ANY | The retrieved value when the key is found (uses SKIP_OUTPUT when key not found) |
| `error` | TEXT | Error message when operation fails (uses SKIP_OUTPUT when successful) |

## Widgets
- **key_to_get**: Text input widget (default: "name")
  - Specifies which key to look up in the dictionary
  - Must be a non-empty string
  - Case-sensitive key matching

## Examples

### Basic Value Retrieval
1. Connect a Dictionary Input Node with `{"name": "Alice", "age": 25}` to the dictionary input
2. Set the key_to_get widget to "name"
3. Connect the `value` output to a Display Node to see "Alice"
4. The `error` output will be skipped since the operation succeeded

### Error Handling Workflow
1. Use the same dictionary but set key_to_get to "email" (a key that doesn't exist)
2. Connect the `error` output to a Display Node to see the error message
3. The `value` output will be skipped since the key wasn't found
4. Connect both outputs to different Display Nodes to handle both success and failure cases

### Conditional Processing
Create a workflow where successful value retrieval continues processing while errors trigger alternative handling:
1. Connect the `value` output to nodes that process the retrieved data
2. Connect the `error` output to nodes that handle missing data scenarios
3. Only one path will execute based on whether the key is found

### Dynamic Key Access
Use the Dictionary Get Element Node in a loop to access different keys:
1. Connect a Text Node with variable key names to update the key_to_get widget
2. Process multiple dictionary elements by changing the key dynamically
3. Handle each success/error case appropriately in your workflow

## Error Conditions

### Input Validation Errors
- **Invalid Dictionary Input**: When the input is not a dictionary type
- **Empty Key**: When the key_to_get widget is empty or contains only whitespace

### Lookup Errors
- **Key Not Found**: When the specified key doesn't exist in the dictionary

### Error Handling Approach
The node uses a dual-output pattern with SKIP_OUTPUT:
- **Success**: Returns value on `value` output, skips `error` output
- **Failure**: Returns error message on `error` output, skips `value` output
- **Frontend Feedback**: All errors are also sent to the user interface for immediate visibility

## Tips & Best Practices

### Key Management
- Use consistent key naming conventions across your dictionaries
- Check key existence before retrieval in critical workflows
- Consider using default values by connecting error output to fallback nodes

### Error Handling Strategies
- Always connect the `error` output to handle missing keys gracefully
- Use the error output to trigger alternative processing paths
- Combine with Display Nodes to show user-friendly error messages

### Performance Considerations
- Dictionary lookups are fast and efficient for small to medium datasets
- Use dependency pulling to ensure dictionary data is available before lookup
- Cache dictionary access results when performing multiple lookups

## Common Use Cases

### Configuration Access
Retrieve configuration values from settings dictionaries:
- API endpoints from configuration objects
- User preferences from profile data
- Feature flags from application settings

### Data Extraction
Extract specific fields from structured data:
- User information from profile dictionaries
- Metrics from analytics data
- Properties from object representations

### Validation Workflows
Check for required fields in data structures:
- Validate required user profile fields
- Ensure configuration completeness
- Verify data integrity before processing

### Dynamic Processing
Access data based on runtime conditions:
- User-selected data fields
- Conditional value retrieval
- Context-dependent data access

## Related Nodes
- **Dictionary Input Node**: Creates the dictionaries to access
- **Dictionary Set Element Node**: Modifies dictionary contents
- **Text Node**: Often used to specify dynamic key names
- **Display Node**: Shows retrieved values or error messages
- **Decision Node**: Can route based on error vs success outputs

## Memory & State
This node is stateless and doesn't use `self.memory` or `self.global_state`. Each execution performs an independent dictionary lookup operation.

## Advanced Usage

### Multiple Key Access
To access multiple keys from the same dictionary:
1. Use multiple Dictionary Get Element Nodes
2. Connect the same dictionary to each node's input
3. Configure different keys for each node
4. Process each retrieved value independently

### Nested Workflows
Combine with other dictionary operations:
1. Get an element that serves as input to Dictionary Set Element
2. Chain multiple get operations for sequential data access
3. Use retrieved values as keys for subsequent dictionary operations

## Troubleshooting

### Common Issues
- **Nothing happens**: Check that the dictionary input is properly connected
- **Always getting errors**: Verify the key name matches exactly (case-sensitive)
- **Wrong data type**: Ensure the input is actually a dictionary, not a string or other type
- **Empty results**: Check if the key_to_get widget has a valid, non-empty value

### Debug Tips
- Use Display Nodes on both outputs to see what's happening
- Connect the dictionary input to a Display Node to verify its contents
- Check the browser console for additional error information
- Verify the exact key names in your source dictionary

### Error Messages
- "Expected dictionary input, got [type]" - Input is not a dictionary
- "Key cannot be empty" - The key_to_get widget is empty or whitespace
- "Key '[key]' not found in dictionary" - The specified key doesn't exist in the dictionary