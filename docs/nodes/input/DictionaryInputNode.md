---
title: "Dictionary Input Node"
description: "Creates dictionary data structures from JSON text input"
category: "Input"
tags: ["input", "dictionary", "json", "data-structure"]
author: "AI Node Builder"
version: "1.0.0"
---

# Dictionary Input Node

## Overview
The Dictionary Input Node creates dictionary data structures from JSON text input. It provides a convenient way to input structured key-value data into your workflows, with automatic validation to ensure data integrity.

## Input Sockets
This node has no input sockets - it generates output based on its widget value.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `dictionary_out` | DICTIONARY | The parsed and validated dictionary from JSON input |

## Widgets
- **json_input**: Text input widget (default: `{"name": "John", "age": 30, "score": 95.5}`)
  - Accepts valid JSON strings that represent objects
  - Keys must be strings
  - Values must be strings, integers, or floating-point numbers
  - Provides immediate error feedback for invalid JSON or unsupported data types

## Examples

### Basic Dictionary Creation
1. Add a Dictionary Input Node to your workflow
2. Enter a JSON object in the json_input widget: `{"name": "Alice", "age": 25, "score": 87.5}`
3. Connect the `dictionary_out` socket to any node that accepts dictionary input

### Configuration Data
Create a configuration dictionary for your workflow by entering structured settings:
```json
{"api_url": "https://api.example.com", "timeout": 30, "retry_count": 3}
```

### User Profile Data
Store user information in a structured format:
```json
{"username": "john_doe", "email": "john@example.com", "age": 28, "premium": 1}
```

### Common Workflow Pattern
Create a Dictionary Input Node with user data, connect it to a Dictionary Get Element Node to extract specific values like "name" or "age", then use those values in other parts of your workflow such as text processing or API calls.

## Validation Rules

### Supported Data Types
- **Keys**: Must be strings only
- **Values**: Strings, integers, or floating-point numbers
- **Nested Objects**: Not supported (values must be primitive types)
- **Arrays**: Not supported as values

### Error Handling
The node provides comprehensive error handling with immediate feedback:
- **Empty Input**: Returns empty dictionary with error message
- **Invalid JSON**: Returns empty dictionary with syntax error details
- **Invalid Keys**: Error if any key is not a string
- **Invalid Values**: Error if any value is not a string, integer, or float
- **Unexpected Errors**: Graceful handling with descriptive error messages

All errors are displayed in the frontend interface for immediate user feedback.

## Tips & Best Practices
- Use double quotes for JSON strings (single quotes are not valid JSON)
- Ensure all keys are strings - use `"123"` instead of `123` for numeric keys
- Keep values simple - avoid nested objects or arrays
- Test your JSON syntax using the immediate error feedback
- Use meaningful key names that describe your data structure
- Consider using consistent naming conventions (camelCase or snake_case)

## Common Use Cases
- **API Configuration**: Store endpoints, keys, and settings
- **User Profiles**: Structured user data with name, age, preferences
- **Application Settings**: Configuration parameters for workflow behavior
- **Data Templates**: Reusable data structures for consistent formatting
- **Test Data**: Sample data for testing other dictionary operations

## Related Nodes
- **Dictionary Get Element Node**: Extract values from the created dictionary
- **Dictionary Set Element Node**: Modify or add elements to the dictionary
- **Text Node**: Often used with Dictionary Get Element to create text output
- **Display Node**: View the dictionary structure and contents

## Memory & State
This node is stateless and doesn't use `self.memory` or `self.global_state`. The output is purely determined by the JSON widget value and its validation.

## Troubleshooting

### Common Issues
- **JSON Syntax Errors**: Ensure proper JSON formatting with double quotes and correct brackets
- **Key Type Errors**: All keys must be strings, even if they represent numbers
- **Value Type Errors**: Only strings, integers, and floats are supported as values
- **Empty Input**: The widget cannot be left blank - provide at least an empty object `{}`

### Error Messages
- "JSON input cannot be empty" - Provide a valid JSON object
- "Invalid JSON syntax" - Check brackets, quotes, and commas
- "All keys must be strings" - Convert numeric keys to strings
- "Value must be string or number" - Remove arrays, objects, or other complex types