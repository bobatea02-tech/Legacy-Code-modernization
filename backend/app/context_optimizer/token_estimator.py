"""Token estimation module for context optimization.

This module provides token estimation strategies for different LLM providers.
Token estimation is isolated from optimization logic to enable swapping
tokenization strategies without modifying the optimizer.
"""

from abc import ABC, abstractmethod
import re
from typing import Optional


class TokenEstimator(ABC):
    """Abstract base class for token estimation strategies.
    
    Different LLM providers use different tokenizers (tiktoken for OpenAI,
    sentencepiece for others). This interface allows swapping implementations
    without changing optimizer logic.
    """
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            Estimated token count
        """
        pass
    
    @abstractmethod
    def clean_source(self, source: str) -> str:
        """Clean source code by removing comments and unused imports.
        
        Args:
            source: Raw source code
            
        Returns:
            Cleaned source code
        """
        pass
    
    @abstractmethod
    def remove_comments(self, source: str) -> str:
        """Remove comments from source code.
        
        Args:
            source: Source code
            
        Returns:
            Source code without comments
        """
        pass
    
    @abstractmethod
    def remove_unused_imports(self, source: str) -> str:
        """Remove unused import statements.
        
        Args:
            source: Source code
            
        Returns:
            Source code without unused imports
        """
        pass


class HeuristicTokenEstimator(TokenEstimator):
    """Heuristic-based token estimator using character count approximation.
    
    This is a simple implementation using the GPT-style approximation of
    ~4 characters per token. For production use with specific LLM providers,
    consider using proper tokenizers like tiktoken (OpenAI) or sentencepiece.
    
    Attributes:
        chars_per_token: Number of characters per token (default: 4)
    """
    
    def __init__(self, chars_per_token: int = 4):
        """Initialize heuristic token estimator.
        
        Args:
            chars_per_token: Average characters per token (default: 4 for GPT-style)
        """
        self.chars_per_token = chars_per_token
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using character-based heuristic.
        
        Uses simple approximation: token_count ≈ char_count / chars_per_token
        This is a placeholder - production should use proper tokenizers.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        char_count = len(text)
        estimated = max(1, char_count // self.chars_per_token)
        
        return estimated
    
    def clean_source(self, source: str) -> str:
        """Clean source code by removing comments and unused imports.
        
        Args:
            source: Raw source code
            
        Returns:
            Cleaned source code
        """
        if not source:
            return ""
        
        # Apply cleaning functions
        cleaned = self.remove_comments(source)
        cleaned = self.remove_unused_imports(cleaned)
        
        return cleaned.strip()
    
    def remove_comments(self, source: str) -> str:
        """Remove comments from source code.
        
        Removes basic single-line and multi-line comments.
        This is a naive implementation - production should use language-specific
        parsers to avoid breaking strings containing comment-like patterns.
        
        Args:
            source: Source code
            
        Returns:
            Source code without comments
        """
        if not source:
            return ""
        
        # Remove single-line comments (// and #)
        lines = source.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove // comments (Java, C, JavaScript)
            if '//' in line:
                line = line.split('//')[0]
            
            # Remove # comments (Python, shell)
            if '#' in line and not line.strip().startswith('#include'):
                # Preserve #include directives
                line = line.split('#')[0]
            
            # Keep non-empty lines
            if line.strip():
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        
        # Remove multi-line comments /* ... */ (naive approach)
        result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)
        
        return result
    
    def remove_unused_imports(self, source: str) -> str:
        """Remove unused import statements.
        
        Placeholder implementation - currently returns source as-is.
        Production implementation should:
        1. Parse import statements
        2. Analyze symbol usage in code
        3. Remove imports for unused symbols
        
        Args:
            source: Source code
            
        Returns:
            Source code (unchanged in this implementation)
        """
        # Placeholder: return source unchanged
        # Production would analyze symbol usage and remove unused imports
        return source


class TiktokenEstimator(TokenEstimator):
    """Token estimator using OpenAI's tiktoken library.
    
    This is a stub for future implementation. Requires tiktoken package.
    Use this for accurate token counting with OpenAI models.
    
    Note: Not implemented in current version to avoid external dependencies.
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        """Initialize tiktoken estimator.
        
        Args:
            model_name: OpenAI model name for tokenizer selection
        """
        self.model_name = model_name
        raise NotImplementedError(
            "TiktokenEstimator requires tiktoken package. "
            "Install with: pip install tiktoken"
        )
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens using tiktoken."""
        raise NotImplementedError("TiktokenEstimator not implemented")
    
    def clean_source(self, source: str) -> str:
        """Clean source code."""
        raise NotImplementedError("TiktokenEstimator not implemented")
    
    def remove_comments(self, source: str) -> str:
        """Remove comments."""
        raise NotImplementedError("TiktokenEstimator not implemented")
    
    def remove_unused_imports(self, source: str) -> str:
        """Remove unused imports."""
        raise NotImplementedError("TiktokenEstimator not implemented")
