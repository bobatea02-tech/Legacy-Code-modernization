"""Prompt versioning schemas and data structures."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PromptBundle:
    """Structured prompt bundle with system and user prompts.
    
    Attributes:
        system_prompt: System-level instructions for the LLM
        user_prompt: User input/query for the LLM
        version: Semantic version of the prompt template
        metadata: Additional metadata about the prompt
    """
    system_prompt: str
    user_prompt: str
    version: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "version": self.version,
            "metadata": self.metadata
        }
