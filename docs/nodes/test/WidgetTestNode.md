---
title: "Widget Test Node"
description: "Demonstrates all supported widget types and their values"
category: "Test"
tags: ["test", "widgets", "ui", "demo", "development"]
author: "AI Node Builder"
version: "1.0.0"
---

# Widget Test Node

## Overview
The Widget Test Node is a demonstration node that showcases all supported widget types in the AI Node Builder system. It's primarily used for testing widget functionality, UI development, and understanding widget behavior.

## Input Sockets
This node has no input sockets - it generates output based on its widget values.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `output` | TEXT | A formatted string showing all widget values |

## Widgets

### Text Widget
- **text_widget**: Text input (default: "Test String")
  - Demonstrates basic text input functionality
  - Accepts any string value including special characters

### Number Widget
- **number_widget**: Number input (default: 42)
  - Range: 0 to 100 with step of 1
  - Demonstrates numeric input with constraints
  - Properties: `{"min": 0, "max": 100, "step": 1}`

### Slider Widget
- **slider_widget**: Slider (default: 5)
  - Range: 0 to 10 with step of 0.1
  - Demonstrates precise decimal input via slider
  - Properties: `{"min": 0, "max": 10, "step": 0.1}`

### Boolean Widget
- **boolean_widget**: Boolean toggle (default: true)
  - Demonstrates checkbox/toggle functionality
  - Returns true/false values

### Combo Widget
- **combo_widget**: Dropdown menu (default: "Option 2")
  - Options: "Option 1", "Option 2", "Option 3"
  - Demonstrates selection from predefined choices
  - Properties: `{"values": ["Option 1", "Option 2", "Option 3"]}`

## Examples

### Widget Testing
1. Add the Widget Test Node to your workflow
2. Experiment with different widget values
3. Connect the output to a Display Node to see the formatted result
4. Observe how each widget type behaves in the UI

### UI Development Reference
Use this node as a reference when developing new nodes to understand:
- How each widget type is declared
- What properties are available for each widget
- How to access widget values in the execute method
- Default value behavior

### Widget Properties Testing
Modify the widget properties to test different configurations:
- Change number ranges and steps
- Modify combo box options
- Test different default values

## Output Format
The node outputs a formatted string showing all widget values:
```
Text: [text_value], Number: [number_value], Slider: [slider_value], Boolean: [boolean_value], Combo: [combo_value]
```

## Widget Implementation Details

### Property Structures
- **Number/Slider**: Use `properties={"min": x, "max": y, "step": z}`
- **Combo**: Use `properties={"values": ["option1", "option2", ...]}`
- **Text/Boolean**: No properties needed

### Value Access
All widgets use the `get_widget_value_safe()` method with appropriate type casting:
- Text: `str` type
- Number: `int` or `float` type  
- Boolean: `bool` type
- Combo: `str` type (returns selected option)

## Development Usage

### Widget Development
- Test new widget types before implementing in production nodes
- Verify widget rendering and behavior across different browsers
- Debug widget value storage and retrieval

### Frontend Integration
- Ensure frontend correctly handles all widget property types
- Test widget validation and constraint enforcement
- Verify widget state persistence

### Backend Integration
- Validate widget value serialization/deserialization
- Test type safety with `get_widget_value_safe()`
- Confirm default value fallback behavior

## Related Nodes
- **Text Node**: Uses basic text widget
- **Number Node**: Uses basic number widget  
- **LLM Node**: Uses multiple widget types including sliders and combos
- **Log Node**: Uses combo widget for message type selection

## Tips & Best Practices
- Use this node to test new widget configurations before implementing
- Widget order is determined by the global widget counter system
- Properties must match the exact structure expected by the frontend
- Always provide sensible default values for widgets
- Test widget behavior with edge cases (min/max values, empty strings, etc.)