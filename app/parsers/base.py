"""Base parser interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseParser(ABC):
    """Abstract base class for language parsers."""
    
    @abstractmethod
    def parse(self, source_code: str) -> Dict[str, Any]:
        """Parse source code into AST representation.
        
        Args:
            source_code: Raw source code string
            
        Returns:
            Abstract syntax tree representation
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            Extracted metadata
        """
        pass
