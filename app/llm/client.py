"""LLM client abstraction - re-export interface."""
from app.llm.interface import LLMClient, LLMResponse

__all__ = ['LLMClient', 'LLMResponse']
