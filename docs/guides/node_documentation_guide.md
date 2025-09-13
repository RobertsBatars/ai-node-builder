# Node Documentation Guide

This guide explains how to create comprehensive documentation for AI Node Builder nodes using the automated documentation system.

## Documentation Structure

### File Organization
Documentation files are organized by category in the `docs/nodes/` directory:
```
docs/nodes/
├── input/          # Input nodes (TextNode, NumberNode, etc.)
├── ai/             # AI nodes (LLMNode, etc.)
├── math/           # Mathematical nodes (AddNode, etc.)
├── tools/          # Tool nodes (CalculatorToolNode, etc.)
└── [category]/     # Other categories as needed
```

### File Naming
- Documentation files should be named exactly as the node class name with `.md` extension
- Example: `TextNode.md` for the `TextNode` class
- Case-sensitive matching is required

## Documentation Format

### Frontmatter (Required)
Every documentation file must start with YAML frontmatter:

```yaml
---
title: "Human-Readable Node Name"
description: "Brief description of what the node does"
category: "Category Name"
tags: ["tag1", "tag2", "tag3"]
author: "Author Name"
version: "1.0.0"
---
```

#### Frontmatter Fields
- **title**: Human-readable name displayed in the documentation
- **description**: Brief description shown in search results and category listings
- **category**: Must match the directory name and node's CATEGORY attribute
- **tags**: Array of searchable keywords
- **author**: Documentation author (optional)
- **version**: Documentation version (optional)

### Content Structure

#### Required Sections
1. **Overview**: Brief introduction and purpose
2. **Input Sockets**: Table of all input sockets
3. **Output Sockets**: Table of all output sockets
4. **Examples**: At least one working example

#### Recommended Sections
- **Widgets**: Description of configuration options
- **Common Use Cases**: Practical applications
- **Tips & Best Practices**: Usage recommendations
- **Related Nodes**: Links to commonly used together nodes
- **Memory & State**: How the node uses memory and global state
- **Troubleshooting**: Common issues and solutions

### Socket Documentation Format
Use tables to document sockets:

````markdown
## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `prompt` | TEXT | Yes | Yes | Main input prompt |
| `context` | TEXT | No | No | Optional context information |
| `temperature` | NUMBER | No | No | Controls randomness (0.0-1.0) |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `response` | TEXT | Generated response |
| `metadata` | ANY | Response metadata |
````

#### Socket Properties
- **Socket**: Use code formatting for socket names
- **Type**: TEXT, NUMBER, IMAGE, ANY, etc.
- **Required**: Boolean - whether this socket must be connected for execution
- **Is Dependency**: Boolean - whether this socket triggers dependency fetching (pull model)
- **Description**: Clear explanation of the socket's purpose
- **Default Do Wait Configuration**: Optional - specify if the socket has custom wait behavior

### Widget Documentation
Document all configurable widgets:

````markdown
## Widgets
- **widget_name**: Widget type (default: value)
  - Description of what the widget controls
  - Valid values or ranges
  - Usage notes
````

### Examples Section
Provide practical examples using either textual descriptions or images:

**Option 1: Textual Description**
````markdown
## Examples

### Basic Usage
Connect a Text Node to your node's input, then connect the output to a Display Node to see the processed result.

### Advanced Pattern
Use multiple inputs by connecting different source nodes (Input A and Input B) to your node, which will process both inputs and produce a combined output.

### Common Workflow
1. Create a Text Node with your input text
2. Connect it to your node's `input` socket
3. Configure any widgets as needed
4. Connect the `output` socket to a Display Node
5. Run the workflow to see results
````

**Option 2: Images**
````markdown
## Examples

### Basic Usage
![Basic workflow example](/docs/images/basic_workflow.png)

### Advanced Pattern  
![Advanced workflow with multiple inputs](/docs/images/advanced_workflow.png)
````

**Image Guidelines:**
- Store documentation images in `docs/images/` (version-controlled)
- Use descriptive filenames: `basic_workflow.png`, `textnode_usage.png`
- Keep images under 500KB for fast loading
- Use PNG format for screenshots, JPG for photos, SVG for diagrams
- Reference documentation images: `/docs/images/image_name.png`

## Auto-Discovery System

### How It Works
1. The system scans `docs/nodes/` for `.md` files
2. Parses YAML frontmatter for metadata
3. Generates a registry mapping node names to documentation
4. Makes documentation available via API and web interface

### No Manual Registry
- No need to edit registry files
- Documentation is automatically discovered
- Just add `.md` files in the correct category folder

## Image Support

### Adding Images to Documentation
The documentation system supports images through standard markdown syntax. Images are served from the `servable/` directory.

#### Image Organization
```
docs/images/           # Documentation images (version-controlled)
```

#### Image Reference Syntax
```markdown
![Alt text](/docs/images/image_name.png)
![Node workflow example](/docs/images/textnode_basic.png)
```

#### Best Practices
- **File Size**: Keep images under 500KB for fast loading
- **Format**: Use PNG for screenshots, JPG for photos, SVG for diagrams
- **Naming**: Use descriptive names: `textnode_basic_workflow.png`
- **Alt Text**: Always provide meaningful alt text for accessibility
- **Dimensions**: Optimize for documentation viewer (max width ~800px)

#### Image Creation Tips
- Take clear screenshots at standard resolution (1920x1080 or similar)
- Crop to show only relevant portions of the interface
- Use consistent styling and backgrounds
- Highlight important areas with arrows or borders when needed
- Consider creating simple workflow diagrams using tools like draw.io or Lucidchart

## Integration with Main Interface

### Right-Click Access
- Documentation appears in node context menus automatically
- Only shows for nodes that have documentation files
- Opens specific node documentation in new window

### Search Functionality
- All documentation is searchable by title, description, and tags
- Search includes content from frontmatter and body text
- Results are ranked by relevance

## Best Practices

### Writing Guidelines
1. **Be Clear and Concise**: Use simple, direct language
2. **Use Textual Descriptions**: Prefer clear text explanations over ASCII diagrams
3. **Include Practical Examples**: Show real-world usage patterns
4. **Use Consistent Formatting**: Follow the established structure
5. **Add Context**: Explain when and why to use the node
6. **Cover Edge Cases**: Document error conditions and limitations

### Content Tips
- Start with the most common use case
- **Avoid ASCII diagrams**: They're hard to create and maintain; use textual descriptions or images instead
- Use step-by-step instructions for complex workflows
- Include screenshots or workflow images when they add value
- Explain complex concepts with concrete examples
- Link to related nodes and concepts
- Keep examples realistic and testable

### Example Quality Guidelines
- **Good**: "Connect a Text Node to the input, configure the prompt widget, then connect the output to a Display Node"
- **Avoid**: Complex ASCII art diagrams that are hard to read and maintain
- **Better**: Include actual workflow screenshots when possible
- **Best**: Combine clear textual steps with supporting images

### Maintenance
- Update documentation when node functionality changes
- Keep examples current with latest node behavior
- Review and update tags for better searchability
- Validate examples work in actual workflows

## Templates

### Basic Node Template
````markdown
---
title: "Your Node Name"
description: "What your node does"
category: "YourCategory"
tags: ["relevant", "tags"]
---

# Your Node Name

## Overview
Brief description of what the node does and its purpose.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `input1` | TEXT | Yes | Yes | Description |
| `input2` | NUMBER | No | No | Optional parameter |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `output1` | TEXT | Description |

## Examples
### Basic Usage
Connect an Input Node to this node, configure any required settings, then connect the output to a Display Node to see the processed result.

### Advanced Usage
For complex workflows, this node can be combined with other processing nodes to create sophisticated data transformation pipelines.

## Related Nodes
- **Related Node 1**: How it relates
- **Related Node 2**: How it relates
````

### Advanced Node Template
Include all optional sections for complex nodes:
- Widgets section
- Common Use Cases
- Advanced Patterns
- Configuration Examples
- Error Handling
- Performance Notes
- Security Considerations
- Troubleshooting

## Testing Documentation

### Validation Checklist
- [ ] Frontmatter is valid YAML
- [ ] Title and description are clear
- [ ] Category matches directory name
- [ ] Examples are realistic and testable
- [ ] All sockets are documented
- [ ] Links to related nodes work
- [ ] Markdown formatting is correct

### Preview Testing
1. Save documentation file in appropriate category folder
2. Restart the AI Node Builder server (if needed for yaml parsing)
3. Open documentation interface via 📚 Docs button
4. Verify node appears in navigation
5. Test search functionality
6. Check right-click context menu on actual node

## Troubleshooting

### Common Issues
- **Node not appearing**: Check file name matches class name exactly
- **Frontmatter errors**: Validate YAML syntax
- **Category mismatch**: Ensure directory matches node's CATEGORY
- **Search not working**: Verify tags and description are descriptive

### Debug Tips
- Check browser console for JavaScript errors
- Verify API endpoints are responding correctly
- Test documentation URLs directly
- Validate markdown rendering

## Future Enhancements
The documentation system is designed to be extensible:
- Guide integration (migrate existing guides)
- Interactive examples
- Version history tracking
- Community contributions
- Automated validation tools

This guide will be updated as the documentation system evolves.