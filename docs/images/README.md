# Documentation Images

This directory contains images used in the AI Node Builder documentation system.

## Image Guidelines

- **Format**: Use PNG for screenshots, JPG for photos, SVG for vector graphics
- **Size**: Keep images under 500KB for fast loading
- **Naming**: Use descriptive names: `textnode_basic_workflow.png`
- **Resolution**: Optimize for web viewing (max width ~800px)
- **Alt Text**: Always provide meaningful alt text in documentation

## Referencing Images

From node documentation (`docs/nodes/category/NodeName.md`):
```markdown
![Description](/docs/images/example.png)
```

From guides (`docs/guides/guide_name.md`):
```markdown
![Description](/docs/images/example.png)
```

## Version Control

This directory is version-controlled (unlike `servable/` which is git-ignored).
All images here should be documentation assets that are part of the project.

For user-generated content, use the `servable/` directory instead.