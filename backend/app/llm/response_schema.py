"""Response schema definitions for LLM outputs.

Defines strict dataclass schemas that LLM responses must conform to.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class TranslationLLMOutput:
    """Schema for translation LLM response.
    
    This is the ONLY valid structure for translation responses.
    Parser will reject any response that doesn't match this schema.
    
    Attributes:
        translated_code: The translated source code
        dependencies: List of dependency identifiers used
        notes: Additional notes or warnings about the translation
    """
    translated_code: str
    dependencies: List[str]
    notes: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "TranslationLLMOutput":
        """Create instance from dictionary with validation.
        
        Args:
            data: Dictionary with response data
            
        Returns:
            TranslationLLMOutput instance
            
        Raises:
            ValueError: If required keys are missing or types are invalid
        """
        required_keys = {"translated_code", "dependencies", "notes"}
        missing_keys = required_keys - set(data.keys())
        
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        # Validate types
        if not isinstance(data["translated_code"], str):
            raise ValueError("translated_code must be a string")
        
        if not isinstance(data["dependencies"], list):
            raise ValueError("dependencies must be a list")
        
        if not all(isinstance(dep, str) for dep in data["dependencies"]):
            raise ValueError("All dependencies must be strings")
        
        if not isinstance(data["notes"], str):
            raise ValueError("notes must be a string")
        
        return cls(
            translated_code=data["translated_code"],
            dependencies=data["dependencies"],
            notes=data["notes"]
        )
