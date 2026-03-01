"""Parser registry for language-agnostic parser selection.

This module provides a registry pattern for parser management,
enabling dynamic parser registration and retrieval without
hardcoded if/elif chains.
"""

from typing import Dict, Type, Optional, Callable
from functools import wraps

from app.parsers.base import BaseParser
from app.core.logging import get_logger

logger = get_logger(__name__)


class ParserRegistry:
    """Registry for managing language parsers.
    
    Provides centralized parser registration and retrieval
    without coupling to specific parser implementations.
    """
    
    def __init__(self) -> None:
        """Initialize empty parser registry."""
        self._parsers: Dict[str, Type[BaseParser]] = {}
        logger.debug("ParserRegistry initialized")
    
    def register(self, language: str, parser_class: Type[BaseParser]) -> None:
        """Register a parser for a specific language.
        
        Args:
            language: Language identifier (e.g., 'java', 'cobol', 'python')
            parser_class: Parser class implementing BaseParser interface
            
        Raises:
            ValueError: If language already registered or parser invalid
        """
        language_lower = language.lower()
        
        # Validate parser implements BaseParser
        if not issubclass(parser_class, BaseParser):
            raise ValueError(
                f"Parser class {parser_class.__name__} must inherit from BaseParser"
            )
        
        # Check for duplicate registration
        if language_lower in self._parsers:
            logger.warning(
                f"Parser for '{language_lower}' already registered, overwriting",
                extra={"language": language_lower}
            )
        
        self._parsers[language_lower] = parser_class
        logger.info(
            f"Registered parser: {parser_class.__name__} for language '{language_lower}'",
            extra={"language": language_lower, "parser": parser_class.__name__}
        )
    
    def get_parser(self, language: str) -> BaseParser:
        """Retrieve parser instance for specified language.
        
        Args:
            language: Language identifier
            
        Returns:
            Parser instance implementing BaseParser interface
            
        Raises:
            ValueError: If no parser registered for language
        """
        language_lower = language.lower()
        
        parser_class = self._parsers.get(language_lower)
        if parser_class is None:
            available = ', '.join(self._parsers.keys())
            raise ValueError(
                f"No parser registered for language '{language_lower}'. "
                f"Available: {available}"
            )
        
        # Instantiate parser
        parser = parser_class()
        logger.debug(
            f"Retrieved parser for '{language_lower}': {parser_class.__name__}",
            extra={"language": language_lower, "parser": parser_class.__name__}
        )
        
        return parser
    
    def is_supported(self, language: str) -> bool:
        """Check if language is supported.
        
        Args:
            language: Language identifier
            
        Returns:
            True if parser registered for language
        """
        return language.lower() in self._parsers
    
    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.
        
        Returns:
            List of registered language identifiers
        """
        return sorted(list(self._parsers.keys()))
    
    def clear(self) -> None:
        """Clear all registered parsers.
        
        Primarily for testing purposes.
        """
        self._parsers.clear()
        logger.debug("Parser registry cleared")


# Global registry instance
_global_registry: Optional[ParserRegistry] = None


def get_registry() -> ParserRegistry:
    """Get global parser registry instance.
    
    Returns:
        Global ParserRegistry singleton
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ParserRegistry()
    return _global_registry


def register_parser(language: str) -> Callable:
    """Decorator for automatic parser registration.
    
    Usage:
        @register_parser('java')
        class JavaParser(BaseParser):
            ...
    
    Args:
        language: Language identifier
        
    Returns:
        Decorator function
    """
    def decorator(parser_class: Type[BaseParser]) -> Type[BaseParser]:
        """Register parser class in global registry.
        
        Args:
            parser_class: Parser class to register
            
        Returns:
            Unmodified parser class
        """
        registry = get_registry()
        registry.register(language, parser_class)
        return parser_class
    
    return decorator
