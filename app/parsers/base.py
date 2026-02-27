"""Base parser interface for multi-language code analysis."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import os

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ASTNode:
    """Unified AST node schema for language-agnostic representation."""
    id: str
    name: str
    node_type: str
    parameters: List[str]
    return_type: Optional[str]
    called_symbols: List[str]
    imports: List[str]
    file_path: str
    start_line: int
    end_line: int
    raw_source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)


class BaseParser(ABC):
    """Abstract base class for language parsers."""
    
    def __init__(self):
        """Initialize parser with configuration from settings."""
        settings = get_settings()
        self.max_file_size = settings.PARSER_MAX_FILE_SIZE_MB * 1024 * 1024
    
    @abstractmethod
    def parse_file(self, file_path: str) -> List[ASTNode]:
        """Parse a source file into normalized AST nodes.
        
        Args:
            file_path: Path to source file
            
        Returns:
            List of normalized ASTNode objects
        """
        pass
    
    @abstractmethod
    def extract_dependencies(self, nodes: List[ASTNode]) -> List[str]:
        """Extract dependency list from AST nodes.
        
        Args:
            nodes: List of ASTNode objects
            
        Returns:
            List of dependency identifiers
        """
        pass
    
    @abstractmethod
    def supports_language(self) -> str:
        """Return the language this parser supports.
        
        Returns:
            Language name (e.g., 'java', 'cobol', 'python')
        """
        pass
    
    def _read_file_safely(self, file_path: str) -> Optional[str]:
        """Safely read file with size and error handling.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content or None if unreadable/too large
        """
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(
                    f"Skipping {file_path} (size: {file_size} bytes exceeds {self.max_file_size} bytes)",
                    extra={"stage_name": "ast_parsing", "file_path": file_path, "file_size": file_size}
                )
                return None
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.warning(
                f"Could not read {file_path}: {e}",
                extra={"stage_name": "ast_parsing", "file_path": file_path, "error": str(e)}
            )
            return None
