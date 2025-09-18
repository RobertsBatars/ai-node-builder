---
title: "LLM Node"
description: "Universal AI integration supporting 100+ models via litellm"
category: "AI"
tags: ["ai", "llm", "language-model", "openai", "anthropic", "tools", "multimodal"]
author: "AI Node Builder"
version: "1.0.0"
---

# LLM Node

## Overview
The LLM Node provides universal access to Large Language Models through the litellm library. It supports over 100 different models and providers, tool calling, multimodal inputs, and context integration.

## Input Sockets
| Socket | Type | Required | Description |
|--------|------|----------|-------------|
| `prompt` | TEXT | Yes (dependency) | Main prompt for the LLM |
| `system_prompt` | TEXT | No (dependency) | System instructions for the model |
| `image` | TEXT | No (dependency) | Image URL or base64-encoded image data for vision models |
| `tools` | ANY[] | No (dependency) | Tool definitions for function calling (dynamic array - additional sockets auto-created) |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `response` | TEXT | LLM text response |
| `tool_calls` | ANY[] | Array of tool calls made by the model |

## Widgets

### Model Configuration
- **provider**: Text input (default: "openai") - LLM provider name
- **model**: Text input (default: "gpt-4o") - Specific model identifier
- **api_key**: Text input (default: "") - API key for the provider

### Generation Parameters
- **temperature**: Slider 0.0-2.0 (default: 0.7) - Controls randomness
- **max_tokens**: Number 1-8000 (default: 1000) - Maximum response length
- **top_p**: Slider 0.0-1.0 (default: 1.0) - Nucleus sampling parameter

### Context Control
- **use_display_context**: Boolean (default: false) - Include display panel history
- **display_context_filter**: Combo (default: "user_and_self") - Filter context messages
- **use_runtime_memory**: Boolean (default: true) - Use conversation memory
- **enable_tools**: Boolean (default: true) - Enable function calling
- **output_intermediate_messages**: Boolean (default: false) - Show tool call details

## Examples

### Complete Workflow Example
![LLM Node comprehensive example showing tools, image input, system prompt and output](/docs/images/llm-example.png)

This example demonstrates a complete LLM workflow with:
- **System Prompt**: Providing context and instructions to the model
- **Image Input**: Vision capabilities for image analysis
- **Tool Integration**: Function calling with calculator tools
- **Structured Output**: Clear response with tool results

### Basic Text Generation
Create a Text Node with "Explain quantum computing" and connect it to the LLM Node's prompt input. Connect the LLM's response output to a Display Node to see the generated explanation.

### With System Prompt
Use two Text Nodes: one with "You are a helpful assistant" connected to the system_prompt input, and another with "What is AI?" connected to the prompt input. This provides context and a specific question to the model.

### Tool Calling
Connect a Calculator Tool Node to the LLM's `tools` input and connect the LLM's `tool_calls` output back to the Calculator Tool Node's input. Then connect a Text Node with "What is 15 * 7?" to the LLM's prompt. The LLM will automatically call the calculator tool and return both the calculation and explanation.

**Required Connections:**
1. Calculator Tool Node output → LLM Node `tools` input
2. LLM Node `tool_calls` output → Calculator Tool Node input  
3. Text Node ("What is 15 * 7?") → LLM Node `prompt` input

### Vision Model
Connect an Image Node to the image input and a Text Node with "Describe this image" to the prompt. The model will analyze the image and provide a detailed description.

**Image Input Options**:
- **URL**: Direct link to an image (e.g., "https://example.com/image.jpg")
- **Local path**: Path to servable images (e.g., "/servable/my_image.png")  
- **Base64**: Base64-encoded image data (e.g., "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...")

The Image Node can provide any of these formats to the LLM's image input.

## Supported Providers
- **OpenAI**: GPT-4, GPT-3.5, GPT-4 Vision
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro, Gemini Vision
- **Cohere**: Command models
- **Ollama**: Local models
- **Azure OpenAI**: Enterprise deployments
- **And 90+ more via litellm**

## Tool Calling

### Tool Definition Format
Tools should be provided as an array of objects:
```json
{
  "type": "function",
  "function": {
    "name": "calculator",
    "description": "Perform mathematical calculations",
    "parameters": {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "Mathematical expression to evaluate"
        }
      },
      "required": ["expression"]
    }
  }
}
```

### Tool Execution Flow
1. LLM decides to call a tool
2. Tool call information is output via `tool_calls` socket
3. External nodes execute the tools
4. Results are fed back to the LLM via the `tools` input
5. LLM incorporates results into final response

### Required Tool Connections
For tool calling to work properly, you must establish these connections:
- **Tool Output → LLM Input**: Connect the tool node's output to the LLM's `tools` input
- **LLM Tool Calls → Tool Input**: Connect the LLM's `tool_calls` output to the tool node's input

**Example Connection Pattern:**
1. Calculator Tool Node → LLM Node (`tools` input)
2. LLM Node (`tool_calls` output) → Calculator Tool Node (input)
3. This creates a feedback loop allowing the LLM to call tools and receive results

## Context Integration

### Display Panel Context
When `use_display_context` is enabled:
- Previous conversation history is included
- Filter options control which messages are included
- Helps maintain conversation continuity

### Runtime Memory
The node maintains conversation history in `self.memory` when enabled through widget or when processing tool calls:
- `conversation_history`: Array of message objects
- `tool_definitions`: Cached tool definitions
- `processed_tool_results`: Tool execution results

## Configuration Examples

### High Creativity
```
temperature: 1.2
top_p: 0.9
max_tokens: 2000
```

### Factual/Deterministic
```
temperature: 0.1
top_p: 0.95
max_tokens: 500
```

### Code Generation
```
model: "gpt-4"
temperature: 0.2
system_prompt: "You are an expert programmer"
```

## Dependencies
- **Required**: `litellm` package
- **API Keys**: Required for most providers (stored in widgets)
- **Network**: Internet connection for cloud models

## Error Handling
- Invalid API keys result in authentication errors
- Rate limits are handled by litellm
- Model-specific limitations are reported
- Network timeouts are managed gracefully

## Performance Optimization
- Conversation history is cached between executions (if memory enabled)
- Tool definitions are reused when possible
- Context is filtered to reduce token usage
- Streaming is not currently supported but planned

## Security Considerations
- API keys are stored in widget properties
- Use environment variables for production deployments
- Tool calling should be restricted to safe operations
- Input sanitization is recommended for user-provided prompts

## Related Nodes
- **Text Node**: Provides prompts and system messages
- **Tool Nodes**: Define available functions
- **Display Nodes**: Show LLM responses
- **Image Nodes**: Provide vision inputs
- **Conditional Nodes**: Route responses based on content

## Troubleshooting

### Common Issues
- **No API Key**: Set the `api_key` widget or use environment variables
- **Model Not Found**: Check model name spelling and provider support
- **Rate Limits**: Reduce request frequency or upgrade API plan
- **Tool Errors**: Verify tool definition format and availability

### Debug Tips
- Enable `output_intermediate_messages` to see tool calling details
- Check the console for litellm error messages
- Verify model supports requested features (tools, vision, etc.)
- Test with simple prompts first

## Advanced Usage

### Custom Providers
```javascript
// Set provider-specific parameters
provider: "ollama"
model: "llama2:7b"
// Local model via Ollama
```

### Multi-turn Conversations
The node automatically maintains conversation context when `use_runtime_memory` is enabled. Each execution (within single workflow execution) adds to the conversation history.

### Dynamic Tool Loading
Tools can be provided dynamically by connecting different tool nodes to the `tools` array input, allowing for context-dependent tool availability.