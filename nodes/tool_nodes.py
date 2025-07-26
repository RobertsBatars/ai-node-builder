# nodes/tool_nodes.py
import json
import random
from typing import Dict, Any
from core.definitions import BaseNode, SocketType, InputWidget

class CalculatorToolNode(BaseNode):
    """
    A simple calculator tool node that mimics an MCP server.
    Provides basic arithmetic operations for LLM tool calling.
    """
    CATEGORY = "Tools"
    
    INPUT_SOCKETS = {
        "tool_call": {"type": SocketType.ANY, "do_not_wait": True}
    }
    
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }

    def load(self):
        """Initialize the tool node."""
        pass

    def execute(self, tool_call=None):
        """
        Execute the calculator tool.
        If tool_call is None, return the tool definition.
        If tool_call is provided, execute the operation and return result.
        """
        # Define the tool schema (MCP-compatible)
        tool_definition = {
            "name": "calculator",
            "description": "Perform basic arithmetic operations (add, subtract, multiply, divide)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The arithmetic operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        }
        
        # If no tool call provided, return the tool definition
        if tool_call is None:
            return (tool_definition,)
        
        # Process the tool call
        try:
            if isinstance(tool_call, dict) and 'arguments' in tool_call:
                args = tool_call['arguments']
                operation = args.get('operation')
                a = float(args.get('a', 0))
                b = float(args.get('b', 0))
                
                if operation == "add":
                    result = a + b
                elif operation == "subtract":
                    result = a - b
                elif operation == "multiply":
                    result = a * b
                elif operation == "divide":
                    if b == 0:
                        result = {"error": "Division by zero is not allowed"}
                    else:
                        result = a / b
                else:
                    result = {"error": f"Unknown operation: {operation}"}
                
                tool_result = {
                    "id": tool_call.get('id', 'calc_result'),
                    "result": result
                }
                
                return (tool_result,)
            else:
                error_result = {
                    "id": "calc_error",
                    "error": "Invalid tool call format"
                }
                return (error_result,)
                
        except Exception as e:
            error_result = {
                "id": "calc_exception",
                "error": f"Calculator error: {str(e)}"
            }
            return (error_result,)


class WeatherToolNode(BaseNode):
    """
    A mock weather lookup tool node that mimics an MCP server.
    Returns simulated weather data for testing LLM tool calling.
    """
    CATEGORY = "Tools"
    
    INPUT_SOCKETS = {
        "tool_call": {"type": SocketType.ANY, "do_not_wait": True}
    }
    
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }

    def load(self):
        """Initialize the tool node."""
        # Mock weather data for different cities
        self.weather_data = {
            "london": {"temp": 15, "condition": "Cloudy", "humidity": 78},
            "paris": {"temp": 18, "condition": "Partly cloudy", "humidity": 65},
            "tokyo": {"temp": 22, "condition": "Sunny", "humidity": 60},
            "new york": {"temp": 12, "condition": "Rainy", "humidity": 85},
            "sydney": {"temp": 25, "condition": "Sunny", "humidity": 55},
            "berlin": {"temp": 10, "condition": "Overcast", "humidity": 80}
        }

    def execute(self, tool_call=None):
        """
        Execute the weather tool.
        If tool_call is None, return the tool definition.
        If tool_call is provided, return weather data for the requested city.
        """
        # Define the tool schema (MCP-compatible)
        tool_definition = {
            "name": "get_weather",
            "description": "Get current weather information for a city",
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
        
        # If no tool call provided, return the tool definition
        if tool_call is None:
            return (tool_definition,)
        
        # Process the tool call
        try:
            if isinstance(tool_call, dict) and 'arguments' in tool_call:
                args = tool_call['arguments']
                city = args.get('city', '').lower().strip()
                
                if city in self.weather_data:
                    weather = self.weather_data[city]
                    # Add some randomness to make it more realistic
                    temp_variation = random.randint(-3, 3)
                    result = {
                        "city": city.title(),
                        "temperature": weather["temp"] + temp_variation,
                        "condition": weather["condition"],
                        "humidity": weather["humidity"] + random.randint(-5, 5),
                        "unit": "Celsius"
                    }
                else:
                    result = {
                        "error": f"Weather data not available for {city}. Available cities: London, Paris, Tokyo, New York, Sydney, Berlin"
                    }
                
                tool_result = {
                    "id": tool_call.get('id', 'weather_result'),
                    "result": result
                }
                
                return (tool_result,)
            else:
                error_result = {
                    "id": "weather_error",
                    "error": "Invalid tool call format"
                }
                return (error_result,)
                
        except Exception as e:
            error_result = {
                "id": "weather_exception",
                "error": f"Weather lookup error: {str(e)}"
            }
            return (error_result,)


class TextAnalysisToolNode(BaseNode):
    """
    A simple text analysis tool node that mimics an MCP server.
    Provides word count, character count, and sentiment analysis.
    """
    CATEGORY = "Tools"
    
    INPUT_SOCKETS = {
        "tool_call": {"type": SocketType.ANY, "do_not_wait": True}
    }
    
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }

    def load(self):
        """Initialize the tool node."""
        # Simple sentiment keywords
        self.positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "happy", "joy"]
        self.negative_words = ["bad", "terrible", "awful", "hate", "sad", "angry", "disappointed", "frustrated"]

    def execute(self, tool_call=None):
        """
        Execute the text analysis tool.
        If tool_call is None, return the tool definition.
        If tool_call is provided, analyze the provided text.
        """
        # Define the tool schema (MCP-compatible)
        tool_definition = {
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
        
        # If no tool call provided, return the tool definition
        if tool_call is None:
            return (tool_definition,)
        
        # Process the tool call
        try:
            if isinstance(tool_call, dict) and 'arguments' in tool_call:
                args = tool_call['arguments']
                text = args.get('text', '')
                
                # Basic text analysis
                word_count = len(text.split())
                char_count = len(text)
                char_count_no_spaces = len(text.replace(' ', ''))
                
                # Simple sentiment analysis
                text_lower = text.lower()
                positive_count = sum(1 for word in self.positive_words if word in text_lower)
                negative_count = sum(1 for word in self.negative_words if word in text_lower)
                
                if positive_count > negative_count:
                    sentiment = "positive"
                elif negative_count > positive_count:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                
                result = {
                    "word_count": word_count,
                    "character_count": char_count,
                    "character_count_no_spaces": char_count_no_spaces,
                    "sentiment": sentiment,
                    "positive_indicators": positive_count,
                    "negative_indicators": negative_count
                }
                
                tool_result = {
                    "id": tool_call.get('id', 'analysis_result'),
                    "result": result
                }
                
                return (tool_result,)
            else:
                error_result = {
                    "id": "analysis_error",
                    "error": "Invalid tool call format"
                }
                return (error_result,)
                
        except Exception as e:
            error_result = {
                "id": "analysis_exception",
                "error": f"Text analysis error: {str(e)}"
            }
            return (error_result,)