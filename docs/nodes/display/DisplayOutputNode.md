---
title: "Display Output Node"
description: "Sends data to the Display Panel and passes it through the workflow"
category: "Output"
tags: ["output", "display", "panel", "ui", "visualization", "passthrough"]
author: "AI Node Builder"
version: "1.0.0"
---

# Display Output Node

## Overview
The Display Output Node sends data to the persistent Display Panel in the UI while passing the data through unchanged. It supports multiple content types and automatically handles complex data serialization. This node is essential for creating interactive workflows that provide visual feedback to users.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `data` | ANY | Yes | Yes | The data to display and pass through |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `data_out` | ANY | The input data passed through unchanged |

## Widgets
- **content_type**: Combo (default: "text") - Determines how the data is rendered in the Display Panel
  - Options: "text", "image", "video"
  - Controls the frontend rendering behavior

## Content Types

### Text
- Default content type for most data
- Complex objects (lists, dictionaries) are automatically serialized to JSON with indentation
- Simple values are displayed as strings
- Best for text output, JSON data, and general information

### Image
- For displaying images in the Display Panel
- Input data should be:
  - Image URLs (e.g., "https://example.com/image.jpg")
  - Local servable paths (e.g., "/servable/my_image.png")
  - Base64-encoded image data (e.g., "data:image/png;base64,...")
- The Display Panel will render the image visually

### Video
- For displaying videos in the Display Panel
- Input data should be video URLs or local servable video files
- The Display Panel will embed a video player

## Examples

### Basic Text Display
Connect any node output to the Display Output Node with content type "text". Complex data structures are automatically formatted as readable JSON.

### Image Workflow
Connect an Image Node or image-generating node to the Display Output Node with content type "image". The image will be displayed in the Display Panel while the image data flows to downstream nodes.

### LLM Response Display
Connect an LLM Node's response output to a Display Output Node to show AI responses in the Display Panel while passing the text to other processing nodes.

### Data Structure Visualization
Connect nodes that output complex data (arrays, objects) to visualize the data structure in a readable JSON format.

### Multi-Output Workflow
Use multiple Display Output Nodes with different content types to show various types of data simultaneously in the Display Panel.

## Behavior & Execution

### Passthrough Design
- Input data flows unchanged to the output socket
- Display is a side effect that doesn't modify the data
- Enables non-intrusive visualization in data pipelines

### Data Serialization
- Complex objects (lists, dictionaries) are serialized to JSON with 2-space indentation
- Serialization errors are handled gracefully with error messages
- Simple types (strings, numbers) are converted to strings

### Global State Integration
- Messages are stored in the persistent global Display Panel context
- Each message includes node ID and title for identification
- Messages persist across workflow runs

### Dual Output Strategy
- Immediate client messaging for real-time display updates
- Global state storage for persistent Display Panel history
- Node title is automatically included in display messages

## Display Panel Integration

### Message Structure
Each display message includes:
- **node_title**: Human-readable node identifier
- **content_type**: Rendering type (text/image/video)
- **data**: The actual content to display
- **node_id**: Internal node identifier

### Persistent Context
- All display messages are stored in `global_state['display_context']`
- Context persists across workflow runs
- Other nodes can access the context via `get_display_context()`

## Common Use Cases
- **AI Response Display**: Show LLM outputs to users
- **Image Gallery**: Display generated or processed images
- **Data Inspection**: Visualize complex data structures
- **Progress Updates**: Show intermediate results during processing
- **Multi-Media Workflows**: Display various content types in sequence
- **Debugging**: Examine data at different workflow stages

## Error Handling
- Serialization errors are caught and display error messages
- Missing or invalid data is handled gracefully
- Content type mismatches are processed as text fallback

## Related Nodes
- **Get Display Context Node**: Retrieves Display Panel history
- **Log Node**: Alternative output for development/debugging
- **LLM Node**: Common source of displayable content
- **Image Nodes**: Source of image content for display

## Tips & Best Practices
- Use "text" type for most data - JSON formatting handles complex structures
- "image" type works with URLs, local files, and base64 data
- The passthrough design allows placing Display Nodes anywhere in workflows
- Multiple Display Nodes can show different aspects of the same data
- Check the Display Panel to see accumulated workflow output
- Use meaningful node titles for better Display Panel organization