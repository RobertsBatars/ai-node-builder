---
title: "Concatenate Array Node"
description: "Joins multiple text inputs into a single string with customizable separator"
category: "Text"
tags: ["text", "array", "concatenate", "join", "strings"]
author: "AI Node Builder"
version: "1.0.0"
---

# Concatenate Array Node

## Overview
The Concatenate Array Node takes multiple text inputs through a dynamic array socket and joins them into a single string using a customizable separator. This node demonstrates the powerful dynamic array socket feature, allowing users to add multiple text inputs as needed.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `texts` | TEXT[] | Yes | Yes | Dynamic array of text inputs to be concatenated |

The `texts` socket is a dynamic array, meaning you can add multiple inputs by clicking the `+ texts` button on the node. Each input (`texts_0`, `texts_1`, etc.) can be connected independently.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `full_text` | TEXT | The joined result of all input texts |

## Widgets
- **separator**: Text input (default: ", ") - The string used to join the text inputs together

## Examples

### Basic Usage
1. Add a Concatenate Array Node to your workflow
2. Click the `+ texts` button to add multiple text input slots
3. Connect Text Nodes or other text-producing nodes to each slot
4. Configure the separator (e.g., " - ", " | ", or leave as default ", ")
5. Connect the output to a Display Node to see the joined result

### Creating a Sentence
Connect three Text Nodes with values "Hello", "beautiful", and "world" to the array inputs. Set the separator to " " (space). The output will be "Hello beautiful world".

### Making a List
Connect multiple Text Nodes with different items and use the default ", " separator to create a comma-separated list like "apples, oranges, bananas, grapes".

### Creating File Paths
Use "/" as the separator and connect Text Nodes with path components like "home", "user", "documents" to create "home/user/documents".

## Behavior & Execution

### Dynamic Array Processing
- All connected inputs are collected into a Python list
- The node waits for all connected inputs due to the dependency flag
- Empty or missing connections are handled gracefully
- The order of inputs corresponds to the socket numbers (texts_0, texts_1, etc.)

### Error Handling
- If the separator widget returns a non-string value, the node sends an error message and falls back to ", " separator
- The node is async-enabled and uses proper client messaging

### Memory & State
This node is stateless and performs its operation based purely on current inputs and widget values.

## Common Use Cases
- **Text Lists**: Creating comma-separated or custom-separated lists
- **Path Building**: Constructing file paths or URLs
- **Sentence Construction**: Building sentences from multiple parts
- **Data Formatting**: Combining multiple text fields with delimiters
- **Report Generation**: Joining various text components into reports

## Related Nodes
- **Text Node**: Provides individual text inputs
- **Log Node**: For logging the concatenated result
- **Display Output Node**: For displaying the final joined text
- **String Array Creator Node**: For creating arrays of strings programmatically

## Tips & Best Practices
- Use descriptive separators to make the output format clear
- Remember that the order of connections matters (texts_0, texts_1, etc.)
- Test with different numbers of inputs to ensure your workflow handles variable array sizes
- Consider using meaningful separators for different data types (commas for lists, slashes for paths, spaces for sentences)