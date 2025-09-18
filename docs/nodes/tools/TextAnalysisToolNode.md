---
title: "Text Analysis Tool Node"
description: "Simple text analysis tool providing word count, character count, and basic sentiment analysis for LLM tool calling"
category: "Tools"
tags: ["tool", "text", "analysis", "sentiment", "statistics", "llm", "function-calling"]
author: "AI Node Builder"
version: "1.0.0"
---

# Text Analysis Tool Node

## Overview
The Text Analysis Tool Node provides basic text analysis capabilities including word counting, character counting, and simple sentiment analysis. It's designed for LLM tool calling, allowing AI models to analyze text content programmatically. The node operates in dual mode: returning tool definitions when called without parameters, and performing analysis when called with text data.

## Input Sockets
| Socket | Type | Required | Do Not Wait | Description |
|--------|------|----------|-------------|-------------|
| `tool_call` | ANY | No | Yes | Tool call data from LLM or direct invocation |

The `do_not_wait` configuration allows the node to execute immediately when called, essential for tool calling patterns.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `output` | ANY | Tool definition (when no input) or text analysis results |

## Examples

### LLM Tool Integration
1. Connect the Text Analysis Tool Node output to an LLM Node's `tools` input
2. Connect the LLM Node's `tool_calls` output back to the Text Analysis Tool Node's `tool_call` input
3. Send a prompt like "Analyze the sentiment of this text: 'I love this amazing product!'" to the LLM
4. The LLM will automatically call the analysis tool and return formatted results

**Required Connections:**
- Text Analysis Tool Node `output` → LLM Node `tools` input
- LLM Node `tool_calls` output → Text Analysis Tool Node `tool_call` input

### Direct Text Analysis
Create a manual tool call structure to test analysis:
```json
{
  "id": "analysis_1",
  "arguments": {"text": "This is a wonderful day! I feel great."}
}
```

### Batch Analysis
Use in workflows that process multiple text samples, analyzing each for statistical and sentiment information.

## Behavior & Execution

### Dual Operation Mode
- **Tool Definition Mode**: When called without `tool_call`, returns MCP-compatible tool schema
- **Execution Mode**: When called with `tool_call`, performs text analysis

### Analysis Components
The node performs comprehensive text analysis:
- **Word Count**: Total number of words (space-separated tokens)
- **Character Count**: Total characters including spaces and punctuation
- **Character Count (No Spaces)**: Character count excluding spaces
- **Sentiment Analysis**: Basic positive/negative/neutral classification
- **Sentiment Indicators**: Count of positive and negative keywords found

### Sentiment Analysis Method
Uses keyword-based sentiment detection:
- **Positive Words**: "good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "happy", "joy"
- **Negative Words**: "bad", "terrible", "awful", "hate", "sad", "angry", "disappointed", "frustrated"
- **Classification**: Compares positive vs negative word counts to determine overall sentiment

## Analysis Results

### Statistical Metrics
- **word_count**: Number of words in the text
- **character_count**: Total number of characters
- **character_count_no_spaces**: Characters excluding spaces
- **positive_indicators**: Count of positive keywords found
- **negative_indicators**: Count of negative keywords found

### Sentiment Classification
- **"positive"**: More positive keywords than negative
- **"negative"**: More negative keywords than positive  
- **"neutral"**: Equal positive and negative keywords, or no sentiment indicators

### Result Format
```json
{
  "word_count": 8,
  "character_count": 42,
  "character_count_no_spaces": 35,
  "sentiment": "positive",
  "positive_indicators": 2,
  "negative_indicators": 0
}
```

## Tool Definition Schema

### MCP Compatibility
The node provides MCP-compatible tool definitions:
```json
{
  "name": "analyze_text",
  "description": "Analyze text for word count, character count, and basic sentiment",
  "input_schema": {
    "type": "object",
    "properties": {
      "text": {
        "type": "string",
        "description": "The text to analyze"
      }
    },
    "required": ["text"]
  }
}
```

### Function Calling Integration
- Compatible with OpenAI function calling format
- Works with Claude tool use
- Supports any LLM with structured tool calling

## Analysis Capabilities

### Text Statistics
- Word counting using space-based tokenization
- Character counting with and without spaces
- Basic text length metrics
- Simple statistical analysis

### Sentiment Detection
- Keyword-based sentiment analysis
- Positive and negative word detection
- Balanced scoring system
- Simple classification output

### Limitations
- Basic keyword matching (not context-aware)
- Limited sentiment vocabulary
- No advanced NLP features
- Case-insensitive matching only

## Common Use Cases
- **Content Analysis**: Analyze user-generated content for basic metrics
- **Sentiment Monitoring**: Track sentiment in feedback or reviews
- **Text Statistics**: Get word and character counts for content
- **AI Text Processing**: Enable LLMs to analyze text programmatically
- **Content Filtering**: Basic sentiment-based content classification
- **Writing Tools**: Provide statistics for text editing workflows

## Related Nodes
- **LLM Node**: Primary integration partner for AI tool calling
- **Weather Tool Node**: Another tool node for API-based data retrieval
- **Calculator Tool Node**: Mathematical operations tool
- **Text Node**: Source of text for analysis
- **Display Output Node**: For showing analysis results

## Analysis Examples

### Positive Text
Input: "I love this amazing product! It's wonderful and fantastic!"
Output:
```json
{
  "word_count": 9,
  "character_count": 54,
  "character_count_no_spaces": 45,
  "sentiment": "positive",
  "positive_indicators": 4,
  "negative_indicators": 0
}
```

### Negative Text
Input: "This is terrible and awful. I hate it."
Output:
```json
{
  "word_count": 8,
  "character_count": 36,
  "character_count_no_spaces": 29,
  "sentiment": "negative",
  "positive_indicators": 0,
  "negative_indicators": 3
}
```

### Neutral Text
Input: "The weather today is cloudy with some sunshine."
Output:
```json
{
  "word_count": 8,
  "character_count": 45,
  "character_count_no_spaces": 37,
  "sentiment": "neutral",
  "positive_indicators": 0,
  "negative_indicators": 0
}
```

## Tips & Best Practices
- Use for basic text analysis where advanced NLP is not required
- Combine with other tools for comprehensive text processing
- Understand the limitations of keyword-based sentiment analysis
- Consider the node as a starting point for more sophisticated analysis
- Test with various text types to understand sentiment detection accuracy
- Use statistical metrics for content length validation
- Integrate with LLMs for intelligent text processing workflows

## Error Handling
- **"Invalid tool call format"**: Malformed tool call structure
- **"Text analysis error"**: General processing errors
- **Missing text**: Returns analysis of empty string (zero counts)
- **Invalid input types**: Handles non-string inputs gracefully

## Enhancement Possibilities
The basic analysis can be extended with:
- More comprehensive sentiment vocabularies
- Context-aware sentiment analysis
- Additional text statistics (sentences, paragraphs)
- Language detection capabilities
- Advanced NLP features (parts of speech, entities)
- Customizable sentiment keyword lists