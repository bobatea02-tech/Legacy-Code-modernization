"""Tests for LLM interface compliance and swappability."""

import pytest
from unittest.mock import Mock
import networkx as nx

from app.llm.interface import LLMClient, LLMResponse
from app.llm.gemini_client import GeminiClient
from app.llm.llm_service import LLMService
from app.translation.orchestrator import TranslationOrchestrator
from app.parsers.base import ASTNode


class MockLLMClient(LLMClient):
    """Mock LLM client for testing interface compliance."""
    
    def __init__(self):
        """Initialize mock client."""
        self.generate_calls = []
        self.embed_calls = []
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float = 0.7,
        force_json: bool = False
    ) -> LLMResponse:
        """Mock generate method."""
        self.generate_calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        })
        
        return LLMResponse(
            text="def translated_function():\n    pass",
            token_count=50,
            model_name="mock-model"
        )
    
    def embed(self, text: str) -> list:
        """Mock embed method."""
        self.embed_calls.append(text)
        return [0.1, 0.2, 0.3]


def test_gemini_client_implements_interface():
    """Test that GeminiClient implements LLMClient interface."""
    assert issubclass(GeminiClient, LLMClient)


def test_mock_client_implements_interface():
    """Test that MockLLMClient implements LLMClient interface."""
    assert issubclass(MockLLMClient, LLMClient)


def test_interface_compliance_generate():
    """Test that mock client can be used in place of real client."""
    mock_client = MockLLMClient()
    
    response = mock_client.generate(
        system_prompt="You are a translator",
        user_prompt="Translate this code",
        max_tokens=1000,
        temperature=0.3
    )
    
    assert isinstance(response, LLMResponse)
    assert response.text == "def translated_function():\n    pass"
    assert response.token_count == 50
    assert len(mock_client.generate_calls) == 1


def test_interface_compliance_embed():
    """Test embed method compliance."""
    mock_client = MockLLMClient()
    
    embedding = mock_client.embed("test text")
    
    assert isinstance(embedding, list)
    assert len(embedding) == 3
    assert len(mock_client.embed_calls) == 1


def test_llm_service_works_with_mock_client():
    """Test that LLMService works with any LLMClient implementation."""
    mock_client = MockLLMClient()
    # Disable caching for this test
    from app.core.cache_service import CacheService
    cache = CacheService(enabled=False)
    service = LLMService(mock_client, cache_service=cache)
    
    response = service.generate(
        system_prompt="system",
        user_prompt="user",
        max_tokens=1000,
        temperature=0.7
    )
    
    assert response.text == "def translated_function():\n    pass"
    assert len(mock_client.generate_calls) == 1


@pytest.mark.asyncio
async def test_orchestrator_works_with_mock_client():
    """Test that TranslationOrchestrator works with any LLMClient via LLMService."""
    mock_client = MockLLMClient()
    # Disable caching for this test
    from app.core.cache_service import CacheService
    cache = CacheService(enabled=False)
    service = LLMService(mock_client, cache_service=cache)
    orchestrator = TranslationOrchestrator(llm_service=service)
    
    # Create simple dependency graph
    graph = nx.DiGraph()
    graph.add_node("node1")
    
    # Create AST index
    ast_node = ASTNode(
        id="node1",
        name="test_function",
        node_type="function",
        parameters=[],
        return_type="void",
        called_symbols=[],
        imports=[],
        file_path="test.java",
        start_line=1,
        end_line=5,
        raw_source="public void testFunction() {}"
    )
    ast_index = {"node1": ast_node}
    
    # Translate
    results = await orchestrator.translate_repository(
        dependency_graph=graph,
        ast_index=ast_index,
        target_language="python"
    )
    
    assert len(results) == 1
    assert results[0].module_name == "node1"
    assert len(mock_client.generate_calls) == 1


def test_structured_prompts_passed_correctly():
    """Test that system and user prompts are passed separately."""
    mock_client = MockLLMClient()
    
    mock_client.generate(
        system_prompt="You are a code translator",
        user_prompt="Translate: def foo(): pass",
        max_tokens=1000,
        temperature=0.3
    )
    
    call = mock_client.generate_calls[0]
    assert call["system_prompt"] == "You are a code translator"
    assert call["user_prompt"] == "Translate: def foo(): pass"
    assert call["system_prompt"] != call["user_prompt"]
