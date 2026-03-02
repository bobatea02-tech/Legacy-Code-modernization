"""Tests for LLM response parsing.

Tests deterministic parsing behavior with various response formats.
"""

import pytest
from app.llm.response_parser import parse_llm_json
from app.llm.response_schema import TranslationLLMOutput
from app.llm.exceptions import StructuredLLMError


class TestResponseParser:
    """Test suite for parse_llm_json function."""
    
    def test_valid_json(self):
        """Test parsing valid JSON response."""
        raw_response = '''
        {
            "translated_code": "def hello(): pass",
            "dependencies": ["module1", "module2"],
            "notes": "Translation complete"
        }
        '''
        
        result = parse_llm_json(
            raw_response=raw_response,
            node_id="test_node",
            model_name="gemini-1.5-flash",
            prompt_version="1.0.0"
        )
        
        assert result["translated_code"] == "def hello(): pass"
        assert result["dependencies"] == ["module1", "module2"]
        assert result["notes"] == "Translation complete"
    
    def test_markdown_wrapped_json(self):
        """Test parsing JSON wrapped in markdown code fences."""
        raw_response = '''```json
        {
            "translated_code": "def test(): return True",
            "dependencies": [],
            "notes": "No dependencies"
        }
        ```'''
        
        result = parse_llm_json(
            raw_response=raw_response,
            node_id="test_node",
            model_name="gemini-1.5-flash",
            prompt_version="1.0.0"
        )
        
        assert result["translated_code"] == "def test(): return True"
        assert result["dependencies"] == []
        assert result["notes"] == "No dependencies"
    
    def test_markdown_without_language_tag(self):
        """Test parsing JSON wrapped in markdown without language tag."""
        raw_response = '''```
        {
            "translated_code": "class Foo: pass",
            "dependencies": ["base"],
            "notes": "Simple class"
        }
        ```'''
        
        result = parse_llm_json(
            raw_response=raw_response,
            node_id="test_node",
            model_name="gemini-1.5-flash",
            prompt_version="1.0.0"
        )
        
        assert result["translated_code"] == "class Foo: pass"
        assert result["dependencies"] == ["base"]
    
    def test_explanation_before_json(self):
        """Test parsing JSON with explanation text before it."""
        raw_response = '''Here is the translation:
        
        {
            "translated_code": "x = 42",
            "dependencies": [],
            "notes": "Simple assignment"
        }
        
        Hope this helps!'''
        
        result = parse_llm_json(
            raw_response=raw_response,
            node_id="test_node",
            model_name="gemini-1.5-flash",
            prompt_version="1.0.0"
        )
        
        assert result["translated_code"] == "x = 42"
        assert result["dependencies"] == []
    
    def test_nested_json_objects(self):
        """Test parsing JSON with nested objects in strings."""
        raw_response = '''{
            "translated_code": "def func(): return {'key': 'value'}",
            "dependencies": ["json"],
            "notes": "Returns dict"
        }'''
        
        result = parse_llm_json(
            raw_response=raw_response,
            node_id="test_node",
            model_name="gemini-1.5-flash",
            prompt_version="1.0.0"
        )
        
        assert "{'key': 'value'}" in result["translated_code"]
    
    def test_empty_response(self):
        """Test that empty response raises StructuredLLMError."""
        with pytest.raises(StructuredLLMError, match="LLM returned empty response"):
            parse_llm_json(
                raw_response="",
                node_id="test_node",
                model_name="gemini-1.5-flash",
                prompt_version="1.0.0"
            )
    
    def test_no_json_object(self):
        """Test that response without JSON object raises error."""
        raw_response = "This is just plain text without any JSON"
        
        with pytest.raises(StructuredLLMError, match="No JSON object found"):
            parse_llm_json(
                raw_response=raw_response,
                node_id="test_node",
                model_name="gemini-1.5-flash",
                prompt_version="1.0.0"
            )
    
    def test_invalid_json_syntax(self):
        """Test that invalid JSON syntax raises error."""
        raw_response = '''{
            "translated_code": "def test(): pass",
            "dependencies": ["mod1"
            "notes": "Missing comma"
        }'''
        
        with pytest.raises(StructuredLLMError, match="Invalid JSON"):
            parse_llm_json(
                raw_response=raw_response,
                node_id="test_node",
                model_name="gemini-1.5-flash",
                prompt_version="1.0.0"
            )
    
    def test_unmatched_braces(self):
        """Test that unmatched braces raise error."""
        raw_response = '''{
            "translated_code": "def test(): pass",
            "dependencies": [],
            "notes": "Missing closing brace"
        '''
        
        with pytest.raises(StructuredLLMError, match="Unmatched braces"):
            parse_llm_json(
                raw_response=raw_response,
                node_id="test_node",
                model_name="gemini-1.5-flash",
                prompt_version="1.0.0"
            )
    
    def test_json_array_instead_of_object(self):
        """Test that JSON array raises error."""
        raw_response = '''["item1", "item2", "item3"]'''
        
        with pytest.raises(StructuredLLMError, match="No JSON object found"):
            parse_llm_json(
                raw_response=raw_response,
                node_id="test_node",
                model_name="gemini-1.5-flash",
                prompt_version="1.0.0"
            )


class TestTranslationLLMOutput:
    """Test suite for TranslationLLMOutput schema."""
    
    def test_valid_schema(self):
        """Test creating output from valid dictionary."""
        data = {
            "translated_code": "def main(): pass",
            "dependencies": ["os", "sys"],
            "notes": "Standard imports"
        }
        
        output = TranslationLLMOutput.from_dict(data)
        
        assert output.translated_code == "def main(): pass"
        assert output.dependencies == ["os", "sys"]
        assert output.notes == "Standard imports"
    
    def test_missing_translated_code(self):
        """Test that missing translated_code raises ValueError."""
        data = {
            "dependencies": [],
            "notes": "Missing code"
        }
        
        with pytest.raises(ValueError, match="Missing required keys"):
            TranslationLLMOutput.from_dict(data)
    
    def test_missing_dependencies(self):
        """Test that missing dependencies raises ValueError."""
        data = {
            "translated_code": "x = 1",
            "notes": "Missing deps"
        }
        
        with pytest.raises(ValueError, match="Missing required keys"):
            TranslationLLMOutput.from_dict(data)
    
    def test_missing_notes(self):
        """Test that missing notes raises ValueError."""
        data = {
            "translated_code": "y = 2",
            "dependencies": []
        }
        
        with pytest.raises(ValueError, match="Missing required keys"):
            TranslationLLMOutput.from_dict(data)
    
    def test_invalid_translated_code_type(self):
        """Test that non-string translated_code raises ValueError."""
        data = {
            "translated_code": 123,
            "dependencies": [],
            "notes": "Invalid type"
        }
        
        with pytest.raises(ValueError, match="translated_code must be a string"):
            TranslationLLMOutput.from_dict(data)
    
    def test_invalid_dependencies_type(self):
        """Test that non-list dependencies raises ValueError."""
        data = {
            "translated_code": "z = 3",
            "dependencies": "not a list",
            "notes": "Invalid type"
        }
        
        with pytest.raises(ValueError, match="dependencies must be a list"):
            TranslationLLMOutput.from_dict(data)
    
    def test_invalid_dependency_item_type(self):
        """Test that non-string items in dependencies raise ValueError."""
        data = {
            "translated_code": "a = 4",
            "dependencies": ["valid", 123, "also_valid"],
            "notes": "Mixed types"
        }
        
        with pytest.raises(ValueError, match="All dependencies must be strings"):
            TranslationLLMOutput.from_dict(data)
    
    def test_invalid_notes_type(self):
        """Test that non-string notes raises ValueError."""
        data = {
            "translated_code": "b = 5",
            "dependencies": [],
            "notes": ["not", "a", "string"]
        }
        
        with pytest.raises(ValueError, match="notes must be a string"):
            TranslationLLMOutput.from_dict(data)
    
    def test_empty_dependencies_list(self):
        """Test that empty dependencies list is valid."""
        data = {
            "translated_code": "c = 6",
            "dependencies": [],
            "notes": "No deps"
        }
        
        output = TranslationLLMOutput.from_dict(data)
        assert output.dependencies == []
    
    def test_empty_strings_allowed(self):
        """Test that empty strings are allowed in fields."""
        data = {
            "translated_code": "",
            "dependencies": [],
            "notes": ""
        }
        
        output = TranslationLLMOutput.from_dict(data)
        assert output.translated_code == ""
        assert output.notes == ""


class TestIntegration:
    """Integration tests combining parser and schema validation."""
    
    def test_full_pipeline_valid(self):
        """Test complete pipeline with valid response."""
        raw_response = '''```json
        {
            "translated_code": "def calculate(x, y):\\n    return x + y",
            "dependencies": ["math", "typing"],
            "notes": "Simple addition function"
        }
        ```'''
        
        parsed = parse_llm_json(
            raw_response=raw_response,
            node_id="calc_node",
            model_name="gemini-1.5-flash",
            prompt_version="1.0.0"
        )
        
        output = TranslationLLMOutput.from_dict(parsed)
        
        assert "def calculate" in output.translated_code
        assert len(output.dependencies) == 2
        assert "math" in output.dependencies
    
    def test_full_pipeline_invalid_schema(self):
        """Test pipeline with valid JSON but invalid schema."""
        raw_response = '''{
            "code": "def test(): pass",
            "deps": [],
            "comment": "Wrong keys"
        }'''
        
        parsed = parse_llm_json(
            raw_response=raw_response,
            node_id="test_node",
            model_name="gemini-1.5-flash",
            prompt_version="1.0.0"
        )
        
        with pytest.raises(ValueError, match="Missing required keys"):
            TranslationLLMOutput.from_dict(parsed)
