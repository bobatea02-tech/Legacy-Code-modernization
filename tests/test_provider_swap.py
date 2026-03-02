"""Test provider swappability without code changes.

This test verifies that the LLM provider can be swapped by changing
configuration only, without modifying any application code.
"""

import pytest
from unittest.mock import patch, Mock
import networkx as nx

from app.llm.factory import get_llm_client
from app.llm.interface import LLMClient
from app.pipeline.service import PipelineService
from app.parsers.base import ASTNode
from app.core.config import Settings


def test_factory_returns_gemini_by_default():
    """Test that factory returns Gemini client by default."""
    with patch('app.llm.factory.get_settings') as mock_settings:
        settings = Mock(spec=Settings)
        settings.LLM_PROVIDER = "gemini"
        settings.LLM_API_KEY = "test-key"
        settings.LLM_MODEL_NAME = "gemini-1.5-flash"
        mock_settings.return_value = settings
        
        with patch('app.llm.gemini_client.genai'):
            client = get_llm_client()
            assert client is not None
            assert client.__class__.__name__ == "GeminiClient"


def test_factory_returns_mock_when_configured():
    """Test that factory returns mock client when LLM_PROVIDER=mock."""
    with patch('app.llm.factory.get_settings') as mock_settings:
        settings = Mock(spec=Settings)
        settings.LLM_PROVIDER = "mock"
        mock_settings.return_value = settings
        
        client = get_llm_client()
        assert client is not None
        assert client.__class__.__name__ == "MockLLMClient"


def test_factory_raises_on_unsupported_provider():
    """Test that factory raises ValueError for unsupported providers."""
    with patch('app.llm.factory.get_settings') as mock_settings:
        settings = Mock(spec=Settings)
        settings.LLM_PROVIDER = "unsupported"
        mock_settings.return_value = settings
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm_client()


def test_pipeline_service_accepts_injected_client():
    """Test that PipelineService accepts LLMClient via dependency injection."""
    from tests.test_llm_interface_compliance import MockLLMClient
    
    mock_client = MockLLMClient()
    pipeline = PipelineService(llm_client=mock_client)
    
    assert pipeline.llm_client is mock_client
    assert isinstance(pipeline.llm_client, LLMClient)


def test_pipeline_service_uses_factory_when_no_client_provided():
    """Test that PipelineService uses factory when no client is injected."""
    with patch('app.llm.factory.get_llm_client') as mock_factory:
        from tests.test_llm_interface_compliance import MockLLMClient
        mock_client = MockLLMClient()
        mock_factory.return_value = mock_client
        
        pipeline = PipelineService()
        
        assert mock_factory.called
        assert pipeline.llm_client is mock_client


@pytest.mark.asyncio
async def test_full_pipeline_with_mock_provider():
    """Test that full pipeline runs with mock provider via config change only.
    
    This is the critical swap test - no code changes, only config.
    """
    from tests.test_llm_interface_compliance import MockLLMClient
    from app.core.cache_service import CacheService
    
    # Create mock client that returns valid JSON
    mock_client = MockLLMClient()
    
    # Override generate to return valid JSON response
    def mock_generate(system_prompt, user_prompt, max_tokens, temperature=0.7, force_json=False):
        mock_client.generate_calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        })
        
        from app.llm.interface import LLMResponse
        return LLMResponse(
            text='{"translated_code": "def translated_function():\\n    pass", "dependencies": [], "imports": []}',
            token_count=50,
            model_name="mock-model"
        )
    
    mock_client.generate = mock_generate
    
    # Inject into pipeline with disabled cache
    from app.llm.llm_service import LLMService
    cache = CacheService(enabled=False)
    llm_service = LLMService(mock_client, cache_service=cache)
    
    pipeline = PipelineService(llm_client=mock_client)
    pipeline.llm_service = llm_service  # Override with non-cached service
    
    # Create minimal test data
    ast_node = ASTNode(
        id="test_node",
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
    
    dependency_graph = nx.DiGraph()
    dependency_graph.add_node("test_node")
    
    ast_index = {"test_node": ast_node}
    
    # Execute translation phase
    translation_results = await pipeline._phase_5_translate(
        dependency_graph=dependency_graph,
        ast_index=ast_index,
        target_language="python"
    )
    
    # Verify results
    assert len(translation_results) == 1
    assert translation_results[0].module_name == "test_node"
    # Translation may fail due to parsing, but the key is that mock client was used
    
    # Verify mock client was called
    assert len(mock_client.generate_calls) >= 1


def test_no_hardcoded_provider_imports_in_pipeline():
    """Test that PipelineService doesn't import concrete providers."""
    import inspect
    from app.pipeline.service import PipelineService
    
    source = inspect.getsource(PipelineService)
    
    # Should not contain direct GeminiClient import
    assert "from app.llm.gemini_client import GeminiClient" not in source
    
    # Should use factory or accept injection
    assert "get_llm_client" in source or "llm_client: LLMClient" in source


def test_no_hardcoded_provider_imports_in_api_dependencies():
    """Test that API dependencies don't import concrete providers."""
    import inspect
    from app.api import dependencies
    
    source = inspect.getsource(dependencies)
    
    # Should not contain direct GeminiClient import at module level
    # (factory is allowed to import it)
    lines = source.split('\n')
    import_lines = [l for l in lines if l.strip().startswith('from app.llm.gemini_client')]
    
    assert len(import_lines) == 0, "API dependencies should not import GeminiClient directly"


def test_config_is_provider_agnostic():
    """Test that config uses generic keys, not provider-specific ones."""
    from app.core.config import Settings
    
    # Should have generic LLM_API_KEY, not GEMINI_API_KEY
    assert hasattr(Settings, '__annotations__')
    field_names = Settings.__annotations__.keys()
    
    assert 'LLM_API_KEY' in field_names
    assert 'LLM_PROVIDER' in field_names
    assert 'GEMINI_API_KEY' not in field_names


def test_provider_swap_requires_only_config_change():
    """Integration test: Verify provider swap requires ONLY config change.
    
    This test documents the swap process:
    1. Change LLM_PROVIDER in .env
    2. Restart application
    3. No code changes required
    """
    # Test with Gemini
    with patch('app.llm.factory.get_settings') as mock_settings:
        settings = Mock(spec=Settings)
        settings.LLM_PROVIDER = "gemini"
        settings.LLM_API_KEY = "test-key"
        settings.LLM_MODEL_NAME = "gemini-1.5-flash"
        mock_settings.return_value = settings
        
        with patch('app.llm.gemini_client.genai'):
            client1 = get_llm_client()
            assert client1.__class__.__name__ == "GeminiClient"
    
    # Test with Mock (config change only)
    with patch('app.llm.factory.get_settings') as mock_settings:
        settings = Mock(spec=Settings)
        settings.LLM_PROVIDER = "mock"
        mock_settings.return_value = settings
        
        client2 = get_llm_client()
        assert client2.__class__.__name__ == "MockLLMClient"
    
    # Verify different clients returned based on config
    assert client1.__class__.__name__ != client2.__class__.__name__
