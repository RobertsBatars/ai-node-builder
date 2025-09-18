---
title: "Image Link Extract Node"
description: "Extracts image links from text and returns cleaned text plus the extracted link"
category: "Image"
tags: ["image", "extraction", "text", "parsing", "links", "markdown", "html"]
author: "AI Node Builder"
version: "1.0.0"
---

# Image Link Extract Node

## Overview
The Image Link Extract Node parses text to extract image links in various formats (Markdown, HTML, direct URLs, servable links, and data URLs) and returns both the cleaned text with image syntax removed and the extracted image link. This is particularly useful for processing AI-generated content that includes image references.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `text` | TEXT | Yes | No | The text content to parse for image links |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `text` | TEXT | The input text with image syntax removed (skipped if no remaining text) |
| `image_link` | TEXT | The extracted image URL or path (skipped if no images found) |

## Widgets
- **extract_first_only**: Boolean toggle (default: true) - Controls extraction behavior
  - **True**: Extract only the first image link found
  - **False**: Extract the first link but remove all image syntax from text

## Supported Image Formats

### Markdown Images
- Format: `![alt text](url)`
- Example: `![Example](https://example.com/image.jpg)`
- Extracts the URL from the parentheses

### HTML Images
- Format: `<img src="url" ...>`
- Example: `<img src="/path/image.png" alt="description">`
- Extracts the src attribute value

### Direct Image URLs
- Format: `https://example.com/image.ext`
- Supported extensions: jpg, jpeg, png, gif, webp, bmp, svg
- Includes query parameters if present

### Servable Links
- Format: `/servable/filename`
- Example: `/servable/generated_image.png`
- For locally served images

### Data URLs
- Format: `data:image/type;base64,data`
- Example: `data:image/png;base64,iVBORw0KGgo...`
- For base64-encoded images

## Examples

### Basic Image Extraction
Input: "Here is an image: ![Sample](https://example.com/pic.jpg) and some more text."
- Text output: "Here is an image:  and some more text."
- Image output: "https://example.com/pic.jpg"

### Multiple Images (First Only)
Input: "First ![Image1](url1.jpg) then ![Image2](url2.jpg)"
With extract_first_only = true:
- Text output: "First  then ![Image2](url2.jpg)"
- Image output: "url1.jpg"

### Multiple Images (Remove All)
Input: "First ![Image1](url1.jpg) then ![Image2](url2.jpg)"
With extract_first_only = false:
- Text output: "First  then "
- Image output: "url1.jpg"

### HTML Image Processing
Input: "Check this: <img src='/servable/demo.png' alt='Demo'>"
- Text output: "Check this: "
- Image output: "/servable/demo.png"

### No Images Found
Input: "Just plain text with no images."
- Text output: "Just plain text with no images."
- Image output: (skipped)

## Behavior & Execution

### Pattern Matching
- Uses regular expressions to identify image patterns
- Case-insensitive matching for URLs and file extensions
- Processes patterns in order of complexity (Markdown, HTML, direct URLs, etc.)

### Text Cleaning
- Removes entire image syntax from text
- Preserves surrounding whitespace structure
- Returns SKIP_OUTPUT for text if no content remains after cleaning

### Link Prioritization
- When multiple images exist, always extracts the first occurrence
- Maintains original text order when processing
- Removes images based on the extract_first_only setting

### Output Logic
- If no images found: returns original text, skips image output
- If images found but no text remains: skips text output, returns image link
- If both text and images: returns cleaned text and first image link

## Extraction Modes

### First Only Mode (default)
- Extracts the first image link
- Removes only the first image syntax from text
- Leaves other image references in the text unchanged
- Best for processing single-image responses

### Remove All Mode
- Extracts the first image link (same as first only)
- Removes ALL image syntax from the text
- Clean text output without any image references
- Best for separating text content from images completely

## Common Use Cases
- **AI Response Processing**: Extract images from LLM outputs that include image references
- **Content Separation**: Split mixed content into text and image components
- **Markdown Processing**: Parse Markdown content for image extraction
- **HTML Parsing**: Extract images from HTML-formatted text
- **Content Migration**: Convert image-embedded text to separate text and image streams

## Error Handling
- Invalid or malformed image syntax is ignored
- Empty text input returns skipped outputs
- Graceful handling of mixed content formats
- No exceptions thrown for parsing failures

## Pattern Processing Order
1. Markdown images `![alt](url)`
2. HTML img tags `<img src="url">`
3. Direct image URLs with extensions
4. Servable links `/servable/file`
5. Base64 data URLs

## Related Nodes
- **Display Output Node**: For displaying extracted images
- **Text Node**: Source of text content to process
- **LLM Node**: Common source of mixed text/image content
- **String Array Creator Node**: For handling multiple extracted elements

## Tips & Best Practices
- Use "first only" mode when processing AI responses that typically contain one image
- Use "remove all" mode when you need completely clean text output
- The node handles mixed content formats gracefully
- Empty text output is skipped automatically - check for this in downstream nodes
- Regular expressions are case-insensitive for better matching
- Consider the order of pattern matching when dealing with complex mixed content