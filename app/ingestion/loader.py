"""Source code file loader."""
from typing import List, Dict, Any
from pathlib import Path


class SourceLoader:
    """Loads and preprocesses source code files."""
    
    def __init__(self, base_path: str):
        """Initialize loader with base path.
        
        Args:
            base_path: Root directory of source code
        """
        self.base_path = Path(base_path)
    
    def load_files(self, extensions: List[str]) -> List[Dict[str, Any]]:
        """Load source files with specified extensions.
        
        Args:
            extensions: List of file extensions to load
            
        Returns:
            List of loaded file metadata and content
        """
        pass
