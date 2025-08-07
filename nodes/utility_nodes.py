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
