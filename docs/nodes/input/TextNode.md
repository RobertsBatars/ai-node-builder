---
title: "Text Input Node"
description: "Provides static text input to workflows"
category: "Input"
tags: ["input", "text", "basic"]
author: "AI Node Builder"
version: "1.0.0"
---

# Text Input Node

## Overview
The Text Input Node is a fundamental building block that provides static text values to your workflows. It's one of the simplest and most commonly used nodes in the AI Node Builder system.

## Input Sockets
This node has no input sockets - it generates output based on its widget value.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `text_out` | TEXT | The text value configured in the widget |

## Widgets
- **value**: Text input widget (default: "Hello from backend!")
  - Accepts any string value
  - Can include newlines and special characters
  - Value is used as the node's output

## Examples

### Basic Usage
1. Add a Text Node to your workflow
2. Set the desired text value in the widget
3. Connect the `text_out` socket to any node that accepts text input

### Common Use Cases
- **Prompts for LLM Node**: Provide system prompts or user messages
- **Static Labels**: Add fixed text labels to your workflow
- **Template Text**: Store reusable text snippets
- **Configuration Values**: Store API keys, URLs, or other configuration text

### Example Workflow
Create a Text Node with "Hello, World!" as the text value, then connect its output to a Log Node to print the message, and finally connect to a Display Node to show the result in the interface.

## Tips & Best Practices
- Use descriptive text values that make your workflow self-documenting
- For long text, consider using the multiline capability
- Text nodes are cached, so changing the value will trigger downstream re-execution
- Use multiple text nodes for different types of content (prompts, labels, etc.)

## Related Nodes
- **Number Node**: For numeric input values
- **LLM Node**: Commonly receives text from Text Nodes
- **Log Node**: Often used to display text node outputs
- **Concatenate Node**: Can combine multiple text inputs

## Memory & State
This node is stateless and doesn't use `self.memory` or `self.global_state`. The output is purely determined by the widget value.