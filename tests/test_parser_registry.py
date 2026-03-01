"""Unit tests for parser registry implementation.

Tests verify:
- Parser registration and retrieval
- Decorator-based registration
- Error handling for unsupported languages
- Registry singleton behavior
"""

import pytest

from app.parsers.registry import ParserRegistry, get_registry, register_parser
from app.parsers.base import BaseParser, ASTNode
from app.parsers import JavaParser, CobolParser
from typing import List


class MockParser(BaseParser):
    """Mock parser for testing."""
    
    def supports_language(self) -> str:
        return "mock"
    
    def parse_file(self, file_path: str) -> List[ASTNode]:
        return []
    
    def extract_dependencies(self, nodes: List[ASTNode]) -> List[str]:
        return []


@pytest.fixture
def registry():
    """Create fresh ParserRegistry for testing."""
    reg = ParserRegistry()
    return reg


def test_registry_initialization(registry):
    """Test ParserRegistry initializes correctly."""
    assert registry is not None
    assert registry.get_supported_languages() == []


def test_manual_registration(registry):
    """Test manual parser registration."""
    registry.register('mock', MockParser)
    
    assert registry.is_supported('mock')
    assert 'mock' in registry.get_supported_languages()


def test_get_parser(registry):
    """Test retrieving registered parser."""
    registry.register('mock', MockParser)
    
    parser = registry.get_parser('mock')
    assert isinstance(parser, MockParser)
    assert parser.supports_language() == 'mock'


def test_case_insensitive_language(registry):
    """Test language identifiers are case-insensitive."""
    registry.register('Mock', MockParser)
    
    assert registry.is_supported('mock')
    assert registry.is_supported('MOCK')
    assert registry.is_supported('Mock')
    
    parser = registry.get_parser('MOCK')
    assert isinstance(parser, MockParser)


def test_unsupported_language_error(registry):
    """Test error when requesting unsupported language."""
    with pytest.raises(ValueError) as exc_info:
        registry.get_parser('unsupported')
    
    assert 'unsupported' in str(exc_info.value).lower()
    assert 'available' in str(exc_info.value).lower()


def test_duplicate_registration_warning(registry):
    """Test warning when registering duplicate language."""
    registry.register('mock', MockParser)
    
    # Second registration should succeed but log warning
    registry.register('mock', MockParser)
    
    # Should still work
    parser = registry.get_parser('mock')
    assert isinstance(parser, MockParser)


def test_invalid_parser_class(registry):
    """Test error when registering non-BaseParser class."""
    class NotAParser:
        pass
    
    with pytest.raises(ValueError) as exc_info:
        registry.register('invalid', NotAParser)
    
    assert 'BaseParser' in str(exc_info.value)


def test_get_supported_languages(registry):
    """Test getting list of supported languages."""
    registry.register('java', JavaParser)
    registry.register('cobol', CobolParser)
    registry.register('mock', MockParser)
    
    languages = registry.get_supported_languages()
    
    assert isinstance(languages, list)
    assert 'java' in languages
    assert 'cobol' in languages
    assert 'mock' in languages
    
    # Should be sorted
    assert languages == sorted(languages)


def test_clear_registry(registry):
    """Test clearing all registered parsers."""
    registry.register('mock', MockParser)
    assert registry.is_supported('mock')
    
    registry.clear()
    
    assert not registry.is_supported('mock')
    assert registry.get_supported_languages() == []


def test_global_registry_singleton():
    """Test global registry is singleton."""
    reg1 = get_registry()
    reg2 = get_registry()
    
    assert reg1 is reg2


def test_decorator_registration():
    """Test decorator-based parser registration."""
    # Create new registry for isolation
    test_registry = ParserRegistry()
    
    @register_parser('test-lang')
    class TestParser(BaseParser):
        def supports_language(self) -> str:
            return 'test-lang'
        
        def parse_file(self, file_path: str) -> List[ASTNode]:
            return []
        
        def extract_dependencies(self, nodes: List[ASTNode]) -> List[str]:
            return []
    
    # Should be registered in global registry
    global_reg = get_registry()
    assert global_reg.is_supported('test-lang')
    
    parser = global_reg.get_parser('test-lang')
    assert isinstance(parser, TestParser)


def test_java_parser_registered():
    """Test JavaParser is registered via decorator."""
    # Import triggers registration
    from app.parsers import JavaParser
    
    registry = get_registry()
    assert registry.is_supported('java')
    
    parser = registry.get_parser('java')
    assert isinstance(parser, JavaParser)


def test_cobol_parser_registered():
    """Test CobolParser is registered via decorator."""
    # Import triggers registration
    from app.parsers import CobolParser
    
    registry = get_registry()
    assert registry.is_supported('cobol')
    
    parser = registry.get_parser('cobol')
    assert isinstance(parser, CobolParser)


def test_multiple_parser_instances(registry):
    """Test that get_parser returns new instances."""
    registry.register('mock', MockParser)
    
    parser1 = registry.get_parser('mock')
    parser2 = registry.get_parser('mock')
    
    # Should be different instances
    assert parser1 is not parser2
    
    # But same type
    assert type(parser1) == type(parser2)


def test_is_supported(registry):
    """Test is_supported method."""
    assert not registry.is_supported('mock')
    
    registry.register('mock', MockParser)
    
    assert registry.is_supported('mock')
    assert registry.is_supported('MOCK')
    assert not registry.is_supported('other')


def test_registry_with_real_parsers():
    """Test registry with real Java and COBOL parsers."""
    # Import to trigger registration
    from app.parsers import JavaParser, CobolParser
    
    registry = get_registry()
    
    # Both should be registered
    assert registry.is_supported('java')
    assert registry.is_supported('cobol')
    
    # Should retrieve correct parsers
    java_parser = registry.get_parser('java')
    cobol_parser = registry.get_parser('cobol')
    
    assert isinstance(java_parser, JavaParser)
    assert isinstance(cobol_parser, CobolParser)
    
    assert java_parser.supports_language() == 'java'
    assert cobol_parser.supports_language() == 'cobol'


def test_empty_language_string(registry):
    """Test handling of empty language string."""
    with pytest.raises(ValueError):
        registry.get_parser('')


def test_none_language(registry):
    """Test handling of None language."""
    with pytest.raises(AttributeError):
        registry.get_parser(None)
