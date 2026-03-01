"""Tests for LLMService."""

import pytest
from unittest.mock import Mock, MagicMock

from app.llm.llm_service import LLMService
from app.llm.interface import LLMResponse
from app.core.cache_service import CacheService
from app.core.retry_policy import RetryPolicy


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = Mock()
    client.generate = Mock(return_value=LLMResponse(
        text="translated code",
        token_count=100,
        model_name="test-model"
    ))
    return client


@pytest.fixture
def mock_cache_service():
    """Create mock cache service."""
    cache = Mock(spec=CacheService)
    cache.enabled = True
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    cache.get_cache_key = Mock(return_value="test_key")
    return cache


@pytest.fixture
def mock_retry_policy():
    """Create mock retry policy."""
    policy = Mock(spec=RetryPolicy)
    policy.max_retries = 3
    policy.execute = Mock(side_effect=lambda func, **kwargs: func(**kwargs))
    return policy


def test_llm_service_initialization(mock_llm_client):
    """Test LLM service initialization."""
    service = LLMService(mock_llm_client)
    assert service.llm_client == mock_llm_client
    assert service.cache_service is not None
    assert service.retry_policy is not None


def test_llm_service_generate_no_cache(mock_llm_client, mock_cache_service, mock_retry_policy):
    """Test generate without cache hit."""
    service = LLMService(
        mock_llm_client,
        cache_service=mock_cache_service,
        retry_policy=mock_retry_policy
    )
    
    response = service.generate(
        system_prompt="system",
        user_prompt="user",
        max_tokens=1000,
        temperature=0.7
    )
    
    assert response.text == "translated code"
    assert response.token_count == 100
    mock_llm_client.generate.assert_called_once()
    mock_cache_service.set.assert_called_once()


def test_llm_service_generate_with_cache_hit(mock_llm_client, mock_cache_service, mock_retry_policy):
    """Test generate with cache hit."""
    cached_data = {
        "text": "cached response",
        "token_count": 50,
        "model_name": "cached-model"
    }
    mock_cache_service.get = Mock(return_value=cached_data)
    
    service = LLMService(
        mock_llm_client,
        cache_service=mock_cache_service,
        retry_policy=mock_retry_policy
    )
    
    response = service.generate(
        system_prompt="system",
        user_prompt="user",
        max_tokens=1000,
        temperature=0.7
    )
    
    assert response.text == "cached response"
    assert response.token_count == 50
    mock_llm_client.generate.assert_not_called()


def test_llm_service_clear_cache(mock_llm_client, mock_cache_service):
    """Test cache clearing."""
    service = LLMService(mock_llm_client, cache_service=mock_cache_service)
    
    service.clear_cache()
    
    mock_cache_service.clear.assert_called_once()
