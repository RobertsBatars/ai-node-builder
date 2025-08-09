# nodes/utility_nodes.py
import asyncio
import re
from core.definitions import BaseNode, SocketType, InputWidget, SKIP_OUTPUT

class WaitNode(BaseNode):
    """
    A node that waits for a specified duration before passing through the input.
    This is useful for testing workflow cancellation and for creating delays.
    """
    CATEGORY = "Utility"

    INPUT_SOCKETS = {
        "trigger": {"type": SocketType.ANY, "is_dependency": True}
    }

    OUTPUT_SOCKETS = {
        "output": {"type": SocketType.ANY}
    }

    # A widget to get the wait time from the user in the UI
    wait_time_seconds = InputWidget(
        widget_type="NUMBER",
        default=5,
        properties={"min": 0, "step": 0.1}
    )

    def load(self):
        """Called once when the workflow is initialized."""
        pass

    async def execute(self, trigger):
        """
        Waits for the specified duration, then returns the input value.
        The 'async' keyword is crucial here to allow non-blocking waits.
        """
        # Get the wait duration from the widget's value
        duration = self.widget_values.get('wait_time_seconds', self.wait_time_seconds.default)
        
        # Ensure duration is a non-negative number
        try:
            duration = float(duration)
            if duration < 0:
                duration = 0
        except (ValueError, TypeError):
            duration = self.wait_time_seconds.default

        print(f"WaitNode: Waiting for {duration} seconds...")
        await asyncio.sleep(duration)
        print("WaitNode: Finished waiting.")

        # Pass the original trigger value to the output
        return (trigger,)


class ImageLinkExtractNode(BaseNode):
    """
    Extracts image links from text and returns both cleaned text and the extracted link.
    Supports markdown images, HTML images, direct URLs, and servable links.
    """
    CATEGORY = "Image"

    INPUT_SOCKETS = {
        "text": {"type": SocketType.TEXT}
    }

    OUTPUT_SOCKETS = {
        "text": {"type": SocketType.TEXT},
        "image_link": {"type": SocketType.TEXT}
    }

    # Widget to choose extraction behavior
    extract_first_only = InputWidget(
        widget_type="BOOLEAN",
        default=True,
        description="Extract only the first image link found"
    )

    def load(self):
        """Initialize regex patterns for image link detection."""
        self.patterns = [
            # Markdown images: ![alt text](url)
            r'!\[([^\]]*)\]\(([^)]+)\)',
            # HTML images: <img src="url" ...>
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
            # Direct image URLs
            r'(https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|bmp|svg)(?:\?[^\s]*)?)',
            # Servable links
            r'(/servable/[^\s]+)',
            # Data URLs for images
            r'(data:image/[^;]+;base64,[A-Za-z0-9+/=]+)'
        ]

    def execute(self, text):
        """Extract image links from text."""
        if not text:
            return (SKIP_OUTPUT, SKIP_OUTPUT)

        original_text = text
        extracted_links = []
        
        # Try each pattern
        for pattern in self.patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    # Markdown format: (alt_text, url)
                    link = match.group(2)
                else:
                    # Direct URL match
                    link = match.group(1)
                
                extracted_links.append({
                    'link': link,
                    'full_match': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })

        # No image links found - output only text
        if not extracted_links:
            return (original_text, SKIP_OUTPUT)

        # Sort by position in text
        extracted_links.sort(key=lambda x: x['start'])
        
        # Get extraction preference
        first_only = self.widget_values.get('extract_first_only', self.extract_first_only.default)
        
        if first_only:
            # Extract only the first link
            first_link = extracted_links[0]
            # Remove the image syntax from text
            cleaned_text = text[:first_link['start']] + text[first_link['end']:]
            cleaned_text = cleaned_text.strip()
            
            # Decide what to output based on remaining content
            text_output = cleaned_text if cleaned_text else SKIP_OUTPUT
            image_output = first_link['link']
            
            return (text_output, image_output)
        else:
            # Extract all links (return first link, but remove all from text)
            cleaned_text = original_text
            # Remove matches in reverse order to maintain positions
            for link_info in reversed(extracted_links):
                cleaned_text = cleaned_text[:link_info['start']] + cleaned_text[link_info['end']:]
            
            cleaned_text = cleaned_text.strip()
            
            # Decide what to output based on remaining content
            text_output = cleaned_text if cleaned_text else SKIP_OUTPUT
            image_output = extracted_links[0]['link']
            
            return (text_output, image_output)


class StringArrayCreatorNode(BaseNode):
    """
    Converts dynamic inputs into a single flattened string array.
    Handles both single values and arrays, flattening arrays properly.
    
    Widget Controls:
    - wait_toggle: If false, inputs use do_not_wait behavior
    - dependency_toggle: If false, inputs don't use dependency behavior  
    - single_item_passthrough: If true and only one item, output single item instead of array
    """
    CATEGORY = "Utility"
    
    INPUT_SOCKETS = {
        "inputs": {"type": SocketType.ANY, "array": True, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "string_array": {"type": SocketType.ANY}
    }
    
    # Widget controls for socket behavior
    wait_toggle = InputWidget(widget_type="BOOLEAN", default=True)
    dependency_toggle = InputWidget(widget_type="BOOLEAN", default=True) 
    single_item_passthrough = InputWidget(widget_type="BOOLEAN", default=True)

    def load(self):
        # Get widget values for socket configuration
        should_wait = self.widget_values.get('wait_toggle', self.wait_toggle.default)
        use_dependency = self.widget_values.get('dependency_toggle', self.dependency_toggle.default)
        
        # Start with base socket configuration - completely rebuild it
        socket_config = {"type": SocketType.ANY, "array": True}
        
        # Apply do_not_wait if wait_toggle is False
        if not should_wait:
            socket_config["do_not_wait"] = True
        
        # Apply dependency if dependency_toggle is True AND we're waiting
        # (do_not_wait takes priority over is_dependency per engine logic)
        if use_dependency and should_wait:
            socket_config["is_dependency"] = True
        
        # Completely replace the socket configuration to clear any previous flags
        self.INPUT_SOCKETS["inputs"] = socket_config
        
        print(f"StringArrayCreatorNode: Configured socket with wait={should_wait}, dependency={use_dependency and should_wait}")

    def execute(self, inputs):
        """
        Flattens all inputs into a single array.
        If input[i] is already an array: extend result with input[i] contents
        If input[i] is single value: append input[i] to result
        
        With single_item_passthrough=True: if only one item in result, output single item instead of array
        """
        if not inputs:
            return ([],)
        
        result = []
        for item in inputs:
            if isinstance(item, (list, tuple)):
                # If item is already an array, extend the result
                result.extend(item)
            else:
                # Single value, append to result
                result.append(item)
        
        # Check single item passthrough setting
        single_passthrough = self.widget_values.get('single_item_passthrough', self.single_item_passthrough.default)
        
        # If single_item_passthrough is enabled and we have exactly one item, output it directly
        if single_passthrough and len(result) == 1:
            print(f"StringArrayCreatorNode: Single item passthrough - outputting {result[0]} directly")
            return (result[0],)
        else:
            print(f"StringArrayCreatorNode: Outputting array with {len(result)} items")
            return (result,)
