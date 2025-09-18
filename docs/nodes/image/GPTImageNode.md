---
title: "GPT Image Node"
description: "High-quality image generation using OpenAI's advanced gpt-image-1 model"
category: "AI"
tags: ["ai", "image", "generation", "gpt-image-1", "openai", "visual"]
author: "AI Node Builder"
version: "1.0.0"
---

# GPT Image Node

## Overview
The GPT Image Node generates high-quality images using OpenAI's advanced gpt-image-1 model. GPT-image-1 is OpenAI's most advanced image generator (2025), superior to DALL-E with better prompt understanding and quality. The node creates detailed, photorealistic images from text descriptions and automatically saves them to the servable directory.

## Input Sockets
| Socket | Type | Required | Description |
|--------|------|----------|-------------|
| `prompt` | TEXT | Yes | Detailed description of the image to generate |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `image_url` | TEXT | Servable URL for accessing the generated image |
| `filename` | TEXT | Generated filename for the saved image |
| `servable_url` | TEXT | Same as image_url - servable URL for the image |

## Widgets

### API Configuration
- **api_key**: Text input (default: "") - OpenAI API key for gpt-image-1 access

### Image Settings
- **size**: Combo box (default: "1024x1024") - Image dimensions
  - Options: "1024x1024", "1024x1536", "1536x1024"
- **quality**: Combo box (default: "high") - Image quality level
  - Options: "low", "medium", "high", "auto"

## Examples

### Basic Image Generation
1. Connect a Text Node with "A majestic mountain landscape at sunset" to the prompt input
2. Set your OpenAI API key in the widget
3. Configure desired size and quality settings
4. Connect the outputs to Display Nodes to see the results
5. The generated image will be available at the servable URL

### High-Quality Art Creation
Use detailed prompts for better results:
- "A photorealistic portrait of a wise old wizard with a long white beard, wearing ornate robes, magical lighting, 4K detail"
- "Modern minimalist living room with large windows, natural lighting, Scandinavian design, clean lines"
- "Vibrant street art mural featuring geometric patterns and bright colors, urban wall background"

### Different Aspect Ratios
- **Square (1024x1024)**: Perfect for social media, profile pictures, general artwork
- **Portrait (1024x1536)**: Ideal for character portraits, vertical compositions
- **Landscape (1536x1024)**: Great for scenery, wide compositions, banners

## Behavior & Execution

### Image Generation Process
1. Validates prompt and API key requirements
2. Calls OpenAI's gpt-image-1 model with specified parameters
3. Receives base64-encoded image data from the API
4. Decodes and saves the image to the servable directory
5. Returns servable URLs and filename information

### File Management
- Generates unique filenames using UUID prefixes: `gpt_image_12345678.png`
- Saves images in PNG format for quality preservation
- Files are accessible via the servable URL system
- Automatic cleanup handled by the ServableFileManager

### Error Handling
- **Missing prompt**: Returns empty outputs with error message
- **Missing API key**: Prevents execution with clear error message
- **API failures**: Handles network errors and API limit responses
- **Invalid responses**: Manages cases where no image data is returned

## Image Quality & Settings

### Quality Levels
- **low**: Fastest generation, basic quality
- **medium**: Balanced speed and quality
- **high**: Best quality, slower generation (recommended)
- **auto**: Let the model choose optimal quality

### Size Recommendations
- **1024x1024**: Standard square format, most versatile
- **1024x1536**: Portrait orientation, great for people and vertical subjects
- **1536x1024**: Landscape orientation, ideal for scenery and wide shots

### Advanced Prompting
For best results, include:
- **Style descriptors**: "photorealistic", "digital art", "oil painting"
- **Lighting details**: "golden hour", "studio lighting", "dramatic shadows"
- **Composition notes**: "close-up", "wide angle", "bird's eye view"
- **Quality modifiers**: "4K", "high detail", "sharp focus"

## API Integration

### OpenAI Requirements
- Requires valid OpenAI API key with image generation access
- Uses gpt-image-1 model (latest image generation model)
- Charges based on image size and quality settings
- Respects API rate limits and usage quotas

### Cost Considerations
- Different sizes and qualities have different costs
- High quality images cost more than lower quality
- Monitor API usage to manage costs
- Consider caching frequently used images

## File System Integration

### Servable Directory
- Images saved to `/servable/` directory
- Accessible via HTTP at `http://localhost:8000/servable/filename`
- Files persist until manually deleted or server restart
- Unique filenames prevent conflicts

### File Format
- All images saved as PNG format
- Preserves transparency and quality
- Compatible with web browsers and image viewers
- Optimized for display and sharing

## Common Use Cases
- **Creative Artwork**: Generate original art and illustrations
- **Content Creation**: Create images for blogs, websites, presentations
- **Concept Art**: Visualize ideas and concepts quickly
- **Product Mockups**: Generate placeholder or concept product images
- **Character Design**: Create character illustrations and portraits
- **Landscape Art**: Generate scenic and environmental artwork

## Related Nodes
- **GPT Image Tool Node**: Tool calling version for LLM integration
- **Image Link Extract Node**: For processing and organizing generated images
- **Text Node**: For providing prompts to the image generator
- **Display Output Node**: For showing the generated image URLs
- **LLM Node**: Can be combined for AI-assisted prompt generation

## Setup & Configuration

### API Key Setup
1. Create an OpenAI account at [platform.openai.com](https://platform.openai.com)
2. Navigate to API keys section
3. Generate a new API key with image generation permissions
4. Copy the key into the node's api_key widget
5. Ensure you have sufficient credits for image generation

### Dependencies
- Requires `litellm` library for OpenAI integration
- Install with: `pip install litellm`
- Automatic error if library not available

## Tips & Best Practices
- **Be specific**: Detailed prompts produce better results
- **Use quality descriptors**: Include terms like "4K", "detailed", "sharp"
- **Specify style**: Mention artistic style, medium, or technique
- **Include lighting**: Describe lighting conditions for better atmosphere
- **Test different sizes**: Different aspect ratios work better for different subjects
- **Monitor costs**: Image generation has API costs, especially for high quality
- **Save important images**: Generated images are temporarily stored
- **Iterate prompts**: Refine prompts based on results to improve output

## Error Messages
- **"Image generation prompt is required"**: Empty or missing prompt
- **"OpenAI API key is required for GPT-image-1"**: Missing API key configuration
- **"No image data returned from API"**: API response issue
- **"GPT-image-1 generation error"**: General API or processing errors

## Performance Notes
- Generation time varies by quality setting (high quality takes longer)
- Network speed affects download and save times
- Large images consume more bandwidth and storage
- API rate limits may cause delays during heavy usage

## Advanced Features
- Automatic base64 decoding and file conversion
- UUID-based unique filename generation
- Integrated file management and serving
- Comprehensive error handling and user feedback
- Support for all gpt-image-1 quality and size options