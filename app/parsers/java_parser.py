"""Java language parser."""
from typing import Dict, Any
from .base import BaseParser


class JavaParser(BaseParser):
    """Parser for Java source code."""
    
    def parse(self, source_code: str) -> Dict[str, Any]:
        """Parse Java source code into AST.
        
        Args:
            source_code: Java source code string
            
        Returns:
            Java AST representation
        """
        pass
    
    def extract_metadata(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Java-specific metadata.
        
        Args:
            ast: Java abstract syntax tree
            
        Returns:
            Java metadata (classes, methods, imports, etc.)
        """
        pass
