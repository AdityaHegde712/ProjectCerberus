import json
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class StorageAdapter:
    """Storage adapter for video and JSON data with local file fallback mode."""
    
    def __init__(self, use_s3: bool = False, bucket: str = None):
        """
        Initialize storage adapter.
        
        Args:
            use_s3: Whether to use S3 storage (requires AWS credentials)
            bucket: S3 bucket name (required if use_s3 is True)
        """
        self.use_s3 = use_s3
        self.bucket = bucket
        
        # Local file storage setup
        self.local_base_path = Path("data")
        self.local_base_path.mkdir(exist_ok=True)
    
    def read_video(self, key: str) -> bytes:
        """
        Read video bytes from storage.
        
        Args:
            key: Storage key (file path)
            
        Returns:
            Video bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if self.use_s3:
            # TODO: Implement S3 read_video
            raise NotImplementedError("S3 mode not yet implemented")
        
        # Local file mode
        file_path = self.local_base_path / key
        if not file_path.exists():
            raise FileNotFoundError(f"Video file not found: {key}")
        
        return file_path.read_bytes()
    
    def write_json(self, key: str, data: Dict[str, Any]) -> None:
        """
        Write JSON data to storage.
        
        Args:
            key: Storage key (file path)
            data: Dictionary to serialize as JSON
            
        Raises:
            TypeError: If data is not a dictionary
        """
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")
        
        if self.use_s3:
            # TODO: Implement S3 write_json
            raise NotImplementedError("S3 mode not yet implemented")
        
        # Local file mode
        file_path = self.local_base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)


# Global storage adapter instance (local file mode by default)
_storage_adapter = StorageAdapter(use_s3=False)


def read_video(key: str) -> bytes:
    """Read video bytes from storage (module-level function)."""
    return _storage_adapter.read_video(key)


def write_json(key: str, data: Dict[str, Any]) -> None:
    """Write JSON data to storage (module-level function)."""
    _storage_adapter.write_json(key, data)