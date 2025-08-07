# core/file_utils.py
import os
import uuid
import base64
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

class ServableFileManager:
    """Manages files in the servable directory for web access."""
    
    def __init__(self, base_dir: str = "servable"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def save_file(self, content: bytes, filename: str = None, node_id: str = None) -> str:
        """
        Save file content to servable directory.
        Returns the servable URL path.
        """
        if filename is None:
            filename = f"file_{uuid.uuid4().hex[:8]}.bin"
        
        # Handle duplicate filenames by adding UUID suffix
        original_filename = filename
        counter = 1
        while (self.base_dir / filename).exists():
            name, ext = os.path.splitext(original_filename)
            filename = f"{name}_{uuid.uuid4().hex[:4]}{ext}"
            counter += 1
            if counter > 100:  # Safety limit
                filename = f"{uuid.uuid4().hex}.bin"
                break
        
        file_path = self.base_dir / filename
        with open(file_path, 'wb') as f:
            f.write(content)
            
        return self.get_file_url(filename)
    
    def save_base64_image(self, base64_data: str, filename: str = None) -> str:
        """
        Save base64 encoded image to servable directory.
        Handles data URL format: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
        Returns the servable URL path.
        """
        try:
            # Handle data URL format
            if base64_data.startswith('data:'):
                header, data = base64_data.split(',', 1)
                # Extract mime type from header
                mime_type = header.split(';')[0].split(':')[1]
                extension = mimetypes.guess_extension(mime_type) or '.png'
            else:
                # Raw base64 data, assume PNG
                data = base64_data
                extension = '.png'
            
            # Decode base64
            content = base64.b64decode(data)
            
            # Generate filename if not provided
            if filename is None:
                filename = f"image_{uuid.uuid4().hex[:8]}{extension}"
            elif not filename.endswith(extension):
                filename = f"{os.path.splitext(filename)[0]}{extension}"
            
            return self.save_file(content, filename)
            
        except Exception as e:
            raise ValueError(f"Failed to decode base64 image: {str(e)}")
    
    def get_file_url(self, filename: str) -> str:
        """Get servable URL for a filename."""
        return f"/servable/{filename}"
    
    def get_file_path(self, filename: str) -> Path:
        """Get full file path for a filename."""
        return self.base_dir / filename
    
    def file_exists(self, filename: str) -> bool:
        """Check if file exists in servable directory."""
        return (self.base_dir / filename).exists()
    
    def list_files(self) -> List[Dict[str, any]]:
        """
        List all files in servable directory with metadata.
        Returns list of dicts with file info.
        """
        files = []
        
        try:
            for file_path in self.base_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    file_info = {
                        'filename': file_path.name,
                        'url': self.get_file_url(file_path.name),
                        'size': stat.st_size,
                        'size_human': self._format_file_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'mime_type': mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream',
                        'is_image': self._is_image_file(file_path.name)
                    }
                    files.append(file_info)
            
            # Sort by modification time, newest first
            files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            print(f"Error listing servable files: {e}")
            
        return files
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file from servable directory."""
        try:
            file_path = self.base_dir / filename
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
            return False
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, any]]:
        """Get detailed info for a specific file."""
        file_path = self.base_dir / filename
        if not file_path.exists():
            return None
            
        try:
            stat = file_path.stat()
            return {
                'filename': filename,
                'url': self.get_file_url(filename),
                'path': str(file_path),
                'size': stat.st_size,
                'size_human': self._format_file_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'mime_type': mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream',
                'is_image': self._is_image_file(filename)
            }
        except Exception as e:
            print(f"Error getting file info for {filename}: {e}")
            return None
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def _is_image_file(self, filename: str) -> bool:
        """Check if file is an image based on extension."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico'}
        return Path(filename).suffix.lower() in image_extensions