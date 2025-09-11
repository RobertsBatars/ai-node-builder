# nodes/image_nodes.py
import uuid
import aiohttp
import json
import base64
from core.definitions import BaseNode, SocketType, InputWidget, MessageType
from core.file_utils import ServableFileManager

try:
    import litellm
except ImportError:
    litellm = None


class GPTImageNode(BaseNode):
    """
    Generates images using OpenAI's gpt-image-1 model.
    GPT-image-1 is OpenAI's most advanced image generator (2025),
    superior to DALL-E with better prompt understanding and quality.
    """
    CATEGORY = "AI"
    
    INPUT_SOCKETS = {
        "prompt": {"type": SocketType.TEXT}
    }
    
    OUTPUT_SOCKETS = {
        "image_url": {"type": SocketType.TEXT},
        "filename": {"type": SocketType.TEXT},
        "servable_url": {"type": SocketType.TEXT}
    }
    
    # Configuration widgets
    api_key = InputWidget(widget_type="TEXT", default="", description="OpenAI API Key")
    
    size = InputWidget(
        widget_type="COMBO", 
        default="1024x1024",
        properties={"values": ["1024x1024", "1024x1536", "1536x1024"]},
        description="Image dimensions"
    )
    
    quality = InputWidget(
        widget_type="COMBO",
        default="high",
        properties={"values": ["low", "medium", "high", "auto"]},
        description="Image quality level"
    )

    def load(self):
        """Initialize dependencies."""
        if litellm is None:
            raise ImportError("litellm library is required for GPT-image-1. Install with: pip install litellm")
        self.file_manager = ServableFileManager()

    async def execute(self, prompt):
        """Generate image using GPT-image-1."""
        try:
            # Get widget values
            api_key_val = str(self.widget_values.get('api_key', self.api_key.default))
            size_val = str(self.widget_values.get('size', self.size.default))
            quality_val = str(self.widget_values.get('quality', self.quality.default))
            
            # Validate inputs
            if not prompt or not prompt.strip():
                error_msg = "Image generation prompt is required"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return ("", "", "")
            
            if not api_key_val:
                error_msg = "OpenAI API key is required for GPT-image-1"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return ("", "", "")
            
            # Set OpenAI API key
            litellm.openai_key = api_key_val  # type: ignore
            
            await self.send_message_to_client(MessageType.LOG, 
                {"message": f"🎨 Generating image with gpt-image-1 ({size_val}, {quality_val})"})
            await self.send_message_to_client(MessageType.LOG,
                {"message": f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"})
            
            # Call gpt-image-1 via litellm
            response = await litellm.aimage_generation(  # type: ignore
                model="gpt-image-1",
                prompt=prompt,
                size=size_val,
                quality=quality_val,
                n=1,
                api_key=api_key_val
            )
            
            # Extract image data from response (gpt-image-1 returns base64 directly)
            if response.data and len(response.data) > 0:
                first_data_item = response.data[0]
            else:
                raise ValueError("No image data returned from API")
            
            if hasattr(first_data_item, 'b64_json') and first_data_item.b64_json:
                # Decode base64 to bytes
                image_data = base64.b64decode(first_data_item.b64_json)
                
                # Save directly without downloading
                filename = f"gpt_image_{uuid.uuid4().hex[:8]}.png"
                servable_url = self.file_manager.save_file(image_data, filename)
                
                await self.send_message_to_client(MessageType.LOG,
                    {"message": f"✅ Image generated and saved as {filename} ({len(image_data)} bytes)"})
                
                return (servable_url, filename, servable_url)
            else:
                error_msg = "No image data received from gpt-image-1"
                await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
                return ("", "", "")
                        
        except Exception as e:
            error_msg = f"GPT-image-1 generation error: {str(e)}"
            await self.send_message_to_client(MessageType.ERROR, {"message": error_msg})
            return ("", "", "")


class GPTImageToolNode(BaseNode):
    """
    Tool node for generating images using OpenAI's gpt-image-1 model.
    Complies with MCP-inspired tool specifications for LLM integration.
    """
    CATEGORY = "Tools"
    
    # Tool nodes have single input/output for tool calling
    INPUT_SOCKETS = {
        "tool_call": {"type": SocketType.ANY, "do_not_wait": True}
    }
    
    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }
    
    # Configuration widgets
    api_key = InputWidget(widget_type="TEXT", default="", description="OpenAI API Key")
    
    size = InputWidget(
        widget_type="COMBO", 
        default="1024x1024",
        properties={"values": ["1024x1024", "1024x1536", "1536x1024"]},
        description="Image dimensions"
    )
    
    quality = InputWidget(
        widget_type="COMBO",
        default="high",
        properties={"values": ["low", "medium", "high", "auto"]},
        description="Image quality level"
    )

    def load(self):
        """Initialize dependencies."""
        if litellm is None:
            raise ImportError("litellm library is required for GPT-image-1. Install with: pip install litellm")
        self.file_manager = ServableFileManager()

    async def execute(self, tool_call=None):
        """
        Execute the GPT-image-1 tool in dual mode.
        If tool_call is None, return the tool definition.
        If tool_call is provided, generate the image and return result.
        """
        # Define the tool schema (MCP-compatible) - only expose prompt, use widget values for size/quality
        tool_definition = {
            "name": "generate_image",
            "description": "Generate high-quality images using OpenAI's gpt-image-1 model. Creates detailed, photorealistic images from text descriptions.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Detailed description of the image to generate. Be specific about style, composition, colors, and details."
                    }
                },
                "required": ["prompt"]
            }
        }
        
        # If no tool call provided, return the tool definition
        if tool_call is None:
            return (tool_definition,)
        
        # Process the tool call
        try:
            if isinstance(tool_call, dict) and 'arguments' in tool_call:
                args = tool_call['arguments']
                prompt = str(args.get('prompt', '')).strip()
                
                # Use widget values for size and quality (not exposed to AI)
                size = str(self.widget_values.get('size', self.size.default))
                quality = str(self.widget_values.get('quality', self.quality.default))
                
                if not prompt:
                    error_result = {
                        "id": tool_call.get('id', 'image_error'),
                        "error": "Image generation prompt is required"
                    }
                    return (error_result,)
                
                # Get API key from widget
                api_key_val = self.widget_values.get('api_key', self.api_key.default)
                
                if not api_key_val:
                    error_result = {
                        "id": tool_call.get('id', 'image_error'),
                        "error": "OpenAI API key is required for image generation. Please set it in the node's widget."
                    }
                    return (error_result,)
                
                # Set OpenAI API key
                litellm.openai_key = api_key_val  # type: ignore
                
                await self.send_message_to_client(MessageType.LOG, 
                    {"message": f"🎨 Tool generating image with gpt-image-1 ({size}, {quality})"})
                # Call gpt-image-1 via litellm
                response = await litellm.aimage_generation(  # type: ignore
                    model="gpt-image-1",
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    n=1,
                    api_key=api_key_val
                )
                
                # Extract image data from response (gpt-image-1 returns base64 directly)
                if response.data and len(response.data) > 0:
                    first_data_item = response.data[0]
                else:
                    raise ValueError("No image data returned from API")
                
                if hasattr(first_data_item, 'b64_json') and first_data_item.b64_json:
                    # Decode base64 to bytes
                    image_data = base64.b64decode(first_data_item.b64_json)
                    
                    # Save directly without downloading
                    filename = f"gpt_image_{uuid.uuid4().hex[:8]}.png"
                    servable_url = self.file_manager.save_file(image_data, filename)
                    
                    await self.send_message_to_client(MessageType.LOG,
                        {"message": f"✅ Image generated and saved as {filename} ({len(image_data)} bytes)"})
                    
                    # Return structured result with instructions to output the link
                    tool_result = {
                        "id": tool_call.get('id', 'image_success'),
                        "result": {
                            "success": True,
                            "message": f"Image generated successfully: {filename}. Please show the user the image link: {servable_url}",
                            "servable_url": servable_url,
                            "filename": filename,
                            "size": size,
                            "quality": quality,
                            "prompt_used": prompt,
                            "instructions": "Always include and display the servable_url link to the user so they can view the generated image. YOU MUST INCLUDE IT IN YOUR OUTPUT IN PLAIN TEXT FORMAT."
                        }
                    }
                    return (tool_result,)
                else:
                    error_result = {
                        "id": tool_call.get('id', 'image_error'),
                        "error": "No image data received from gpt-image-1"
                    }
                    return (error_result,)
            else:
                error_result = {
                    "id": tool_call.get('id', 'image_error'),
                    "error": "Invalid tool call format"
                }
                return (error_result,)
                
        except Exception as e:
            error_result = {
                "id": tool_call.get('id', 'image_exception'),
                "error": f"Image generation error: {str(e)}"
            }
            return (error_result,)