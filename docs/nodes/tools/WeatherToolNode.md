---
title: "Weather Tool Node"
description: "Real weather data retrieval tool using OpenWeatherMap API for LLM tool calling"
category: "Tools"
tags: ["tool", "weather", "api", "openweathermap", "llm", "function-calling"]
author: "AI Node Builder"
version: "1.0.0"
---

# Weather Tool Node

## Overview
The Weather Tool Node provides real-time weather data retrieval through the OpenWeatherMap API. It's designed for LLM tool calling, allowing AI models to fetch current weather information for any city worldwide. The node operates in dual mode: returning tool definitions when called without parameters, and executing weather lookups when called with city names.

## Input Sockets
| Socket | Type | Required | Do Not Wait | Description |
|--------|------|----------|-------------|-------------|
| `tool_call` | ANY | No | Yes | Tool call data from LLM or direct invocation |

The `do_not_wait` configuration allows the node to execute immediately when called, essential for tool calling patterns.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `output` | ANY | Tool definition (when no input) or weather data result |

## Widgets
- **openweathermap_api_key**: Text input (default: "") - OpenWeatherMap API key for weather data access

## Examples

### LLM Tool Integration
1. Connect the Weather Tool Node output to an LLM Node's `tools` input
2. Connect the LLM Node's `tool_calls` output back to the Weather Tool Node's `tool_call` input
3. Set your OpenWeatherMap API key in the widget
4. Send a prompt like "What's the weather in London?" to the LLM
5. The LLM will automatically call the weather tool and return formatted results

**Required Connections:**
- Weather Tool Node `output` → LLM Node `tools` input
- LLM Node `tool_calls` output → Weather Tool Node `tool_call` input

### Direct Weather Lookup
Create a manual tool call structure and connect it to test weather data retrieval:
```json
{
  "id": "weather_1",
  "arguments": {"city": "Tokyo"}
}
```

### API Key Setup
1. Sign up for a free API key at [OpenWeatherMap](https://openweathermap.org/api)
2. Enter the API key in the node's widget field
3. The node will use this key for all weather API requests

## Behavior & Execution

### Dual Operation Mode
- **Tool Definition Mode**: When called without `tool_call`, returns MCP-compatible tool schema
- **Execution Mode**: When called with `tool_call`, fetches real weather data

### Weather Data Format
Returns comprehensive weather information:
- City name and country
- Temperature and "feels like" temperature (Celsius)
- Weather condition description
- Humidity and atmospheric pressure
- Wind speed and visibility
- All measurements in metric units

### Error Handling
- **Invalid API Key**: Returns error message with setup instructions
- **City Not Found**: Returns specific error for unknown cities
- **Network Issues**: Handles connection errors gracefully
- **API Limits**: Provides meaningful error messages for API failures

## API Integration

### OpenWeatherMap Integration
- Uses OpenWeatherMap Current Weather API
- Requires free or paid API key
- Supports worldwide city lookups
- Returns real-time weather data

### Request Format
The tool expects city names in various formats:
- Simple names: "London", "Tokyo", "New York"
- City with country: "London,UK", "Paris,FR"
- Cities with spaces: "New York", "Los Angeles"

### Response Structure
Successful weather lookups return:
```json
{
  "city": "London",
  "country": "GB",
  "temperature": 15.2,
  "feels_like": 14.1,
  "condition": "Partly Cloudy",
  "humidity": 68,
  "pressure": 1013,
  "wind_speed": 3.2,
  "visibility": 10.0,
  "unit": "Celsius"
}
```

## Tool Definition Schema

### MCP Compatibility
The node provides MCP-compatible tool definitions:
```json
{
  "name": "get_weather",
  "description": "Get current weather information for a city using OpenWeatherMap API",
  "input_schema": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string",
        "description": "The name of the city to get weather for"
      }
    },
    "required": ["city"]
  }
}
```

### Function Calling Integration
- Compatible with OpenAI function calling format
- Works with Claude tool use
- Supports any LLM with structured tool calling

## Common Use Cases
- **AI Weather Assistant**: Enable LLMs to provide real-time weather information
- **Travel Planning**: Get weather data for destination cities
- **Location-Based Services**: Integrate weather into location-aware applications
- **Data Collection**: Gather weather data for analysis or logging
- **Conditional Workflows**: Use weather data to trigger different workflow paths

## Related Nodes
- **LLM Node**: Primary integration partner for AI tool calling
- **Calculator Tool Node**: Another tool node for mathematical operations
- **Text Analysis Tool Node**: Additional tool for text processing
- **Display Output Node**: For showing weather results
- **Conditional Nodes**: For weather-based decision making

## Setup & Configuration

### API Key Requirements
1. Register at [OpenWeatherMap](https://openweathermap.org/api)
2. Generate a free API key (1000 calls/day limit)
3. For higher usage, consider paid plans
4. Enter the API key in the node widget

### Network Requirements
- Requires internet connectivity
- Uses HTTP requests to OpenWeatherMap API
- Handles network timeouts and errors gracefully

## Tips & Best Practices
- Always configure the API key before using the node
- Test with known city names first to verify setup
- Monitor API usage if on free tier (1000 calls/day limit)
- Use specific city names for better accuracy ("London,UK" vs "London")
- Cache weather data if making frequent requests for the same location
- Handle the error responses appropriately in your workflows

## Error Messages
- **"OpenWeatherMap API key not configured"**: API key widget is empty
- **"Invalid API key"**: API key is incorrect or inactive
- **"City 'name' not found"**: City name not recognized by API
- **"Network error"**: Connection issues or API unavailable
- **"Invalid tool call format"**: Malformed tool call structure

## API Limitations
- Free tier: 1000 calls per day
- Rate limiting: 60 calls per minute
- Historical data requires paid subscription
- Weather forecasts available in paid tiers
- City database updated regularly but may have gaps