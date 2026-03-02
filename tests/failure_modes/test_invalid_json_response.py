"""Test invalid JSON response handling."""

import pytest
from unittest.mock import Mock

from app.llm.response_parser import parse_llm_json
from app.llm.response_schema import TranslationLLMOutput
from app.llm.exceptions import StructuredLLMError


def test_missing_braces():
    """Test response with missing closing brace."""
    invalid_json = '{"translated_code": "def test(): pass", "dependencies": [], "notes": "test"'
    
    with pytest.raises(StructuredLLMError, match="Unmatched braces"):
        parse_llm_json(invalid_json, "node1", "gemini", "1.0")


def test_markdown_wrapped_json():
    """Test that markdown-wrapped JSON is parsed correctly."""
    markdown_json = '''```json
{
    "translated_code": "def hello(): pass",
    "dependencies": ["os"],
    "notes": "Simple function"
}
```'''
    
    result = parse_llm_json(markdown_json, "node1", "gemini", "1.0")
    assert result["translated_code"] == "def hello(): pass"
    assert result["dependencies"] == ["os"]


def test_multiple_json_objects():
    """Test response with multiple JSON objects (only first is extracted)."""
    multiple_json = '''
{"translated_code": "first", "dependencies": [], "notes": "first"}
{"translated_code": "second", "dependencies": [], "notes": "second"}
'''
    
    result = parse_llm_json(multiple_json, "node1", "gemini", "1.0")
    assert result["translated_code"] == "first"


def test_non_json_text_before():
    """Test JSON with explanation text before it."""
    text_before = '''
Here is the translation:

{
    "translated_code": "def func(): return 42",
    "dependencies": [],
    "notes": "Returns constant"
}
'''
    
    result = parse_llm_json(text_before, "node1", "gemini", "1.0")
    assert result["translated_code"] == "def func(): return 42"


def test_non_json_text_after():
    """Test JSON with text after it."""
    text_after = '''{
    "translated_code": "x = 1",
    "dependencies": [],
    "notes": "Assignment"
}

Hope this helps!'''
    
    result = parse_llm_json(text_after, "node1", "gemini", "1.0")
    assert result["translated_code"] == "x = 1"


def test_completely_invalid_json():
    """Test completely invalid JSON."""
    invalid = "This is not JSON at all"
    
    with pytest.raises(StructuredLLMError, match="No JSON object found"):
        parse_llm_json(invalid, "node1", "gemini", "1.0")


def test_json_with_syntax_error():
    """Test JSON with syntax error (missing comma)."""
    syntax_error = '''{
    "translated_code": "def test(): pass"
    "dependencies": []
    "notes": "test"
}'''
    
    with pytest.raises(StructuredLLMError, match="Invalid JSON"):
        parse_llm_json(syntax_error, "node1", "gemini", "1.0")


def test_empty_response():
    """Test empty response."""
    with pytest.raises(StructuredLLMError, match="empty response"):
        parse_llm_json("", "node1", "gemini", "1.0")


def test_whitespace_only_response():
    """Test whitespace-only response."""
    with pytest.raises(StructuredLLMError, match="empty response"):
        parse_llm_json("   \n\t  ", "node1", "gemini", "1.0")


def test_json_array_instead_of_object():
    """Test JSON array instead of object."""
    array_json = '["item1", "item2"]'
    
    with pytest.raises(StructuredLLMError, match="No JSON object found"):
        parse_llm_json(array_json, "node1", "gemini", "1.0")


def test_schema_violation_missing_field():
    """Test schema validation with missing required field."""
    incomplete_json = '{"translated_code": "def test(): pass", "dependencies": []}'
    
    parsed = parse_llm_json(incomplete_json, "node1", "gemini", "1.0")
    
    with pytest.raises(ValueError, match="Missing required keys"):
        TranslationLLMOutput.from_dict(parsed)


def test_schema_violation_wrong_type():
    """Test schema validation with wrong field type."""
    wrong_type = '''{
    "translated_code": 123,
    "dependencies": [],
    "notes": "test"
}'''
    
    parsed = parse_llm_json(wrong_type, "node1", "gemini", "1.0")
    
    with pytest.raises(ValueError, match="translated_code must be a string"):
        TranslationLLMOutput.from_dict(parsed)


def test_schema_violation_dependencies_not_list():
    """Test schema validation with dependencies as string instead of list."""
    wrong_deps = '''{
    "translated_code": "def test(): pass",
    "dependencies": "not a list",
    "notes": "test"
}'''
    
    parsed = parse_llm_json(wrong_deps, "node1", "gemini", "1.0")
    
    with pytest.raises(ValueError, match="dependencies must be a list"):
        TranslationLLMOutput.from_dict(parsed)
