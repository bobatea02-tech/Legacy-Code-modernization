"""Tests for Gemini API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from app.llm import (
    GeminiClient,
    LLMResponse,
    estimate_tokens
)
from app.llm.exceptions import (
    APIKeyMissingError,
    TokenLimitExceededError,
    GeminiRequestError
)


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock()
    settings.GEMINI_API_KEY = "test-api-key"
    settings.LLM_MODEL_NAME = "gemini-1.5-flash"
    settings.MAX_TOKEN_LIMIT = 10000
    settings.CACHE_ENABLED = False
    settings.LLM_RETRY_COUNT = 3
    settings.LLM_RETRY_DELAY = 0.1
    settings.TEMP_REPO_DIR = ".temp_test"
    return settings


@pytest.fixture
def mock_genai():
    """Mock google.generativeai module."""
    with patch('app.llm.gemini_client.genai') as mock:
        yield mock


def test_estimate_tokens():
    """Test token estimation function."""
    # Empty string
    assert estimate_tokens("") == 0
    
    # Short text
    tokens = estimate_tokens("hello world")
    assert tokens > 0
    
    # Longer text should have more tokens
    short_tokens = estimate_tokens("hello")
    long_tokens = estimate_tokens("hello world this is a longer text with more content")
    assert long_tokens > short_tokens


def test_estimate_tokens_heuristic():
    """Test token estimation heuristic (~4 chars per token)."""
    text = "a" * 100  # 100 characters
    tokens = estimate_tokens(text)
    assert tokens == 25  # 100 / 4


@patch('app.llm.gemini_client.get_settings')
def test_client_initialization(mock_get_settings, mock_settings, mock_genai):
    """Test GeminiClient initialization."""
    mock_get_settings.return_value = mock_settings
    
    client = GeminiClient()
    
    assert client.model_name == "gemini-1.5-flash"
    assert client.cache_enabled == False
    mock_genai.configure.assert_called_once_with(api_key="test-api-key")


@patch('app.llm.gemini_client.get_settings')
def test_client_initialization_missing_api_key(mock_get_settings, mock_settings):
    """Test initialization fails with missing API key."""
    mock_settings.GEMINI_API_KEY = ""
    mock_get_settings.return_value = mock_settings
    
    with pytest.raises(APIKeyMissingError):
        GeminiClient()


@patch('app.llm.gemini_client.get_settings')
def test_generate_basic(mock_get_settings, mock_settings, mock_genai):
    """Test basic generation."""
    mock_get_settings.return_value = mock_settings
    
    # Mock model response
    mock_response = Mock()
    mock_response.text = "Generated response text"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
    
    client = GeminiClient()
    response = client.generate("Test prompt")
    
    assert isinstance(response, LLMResponse)
    assert response.text == "Generated response text"
    assert response.cached == False
    assert response.latency_ms >= 0  # Can be 0 for mocked calls
    assert response.request_id.startswith("req_")


@patch('app.llm.gemini_client.get_settings')
def test_generate_with_metadata(mock_get_settings, mock_settings, mock_genai):
    """Test generation with metadata."""
    mock_get_settings.return_value = mock_settings
    
    mock_response = Mock()
    mock_response.text = "Response"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
    
    client = GeminiClient()
    metadata = {
        "module_name": "Calculator",
        "phase_name": "translation",
        "token_hint": 500
    }
    
    response = client.generate("Test prompt", metadata=metadata)
    
    assert isinstance(response, LLMResponse)
    assert response.text == "Response"


@patch('app.llm.gemini_client.get_settings')
def test_generate_token_limit_exceeded(mock_get_settings, mock_settings, mock_genai):
    """Test token limit enforcement."""
    mock_settings.MAX_TOKEN_LIMIT = 10  # Very low limit
    mock_get_settings.return_value = mock_settings
    
    client = GeminiClient()
    
    # Long prompt that exceeds limit
    long_prompt = "a" * 100  # 100 chars = ~25 tokens
    
    with pytest.raises(TokenLimitExceededError):
        client.generate(long_prompt)


@patch('app.llm.gemini_client.get_settings')
def test_generate_with_retry(mock_get_settings, mock_settings, mock_genai):
    """Test retry logic on failure."""
    mock_get_settings.return_value = mock_settings
    mock_settings.LLM_RETRY_DELAY = 0.01  # Fast retry for testing
    
    # First two calls fail, third succeeds
    mock_model = mock_genai.GenerativeModel.return_value
    mock_model.generate_content.side_effect = [
        Exception("Network error"),
        Exception("Rate limit"),
        Mock(text="Success after retries")
    ]
    
    client = GeminiClient()
    response = client.generate("Test prompt")
    
    assert response.text == "Success after retries"
    assert mock_model.generate_content.call_count == 3


@patch('app.llm.gemini_client.get_settings')
def test_generate_all_retries_fail(mock_get_settings, mock_settings, mock_genai):
    """Test failure after all retries exhausted."""
    mock_get_settings.return_value = mock_settings
    mock_settings.LLM_RETRY_COUNT = 2
    mock_settings.LLM_RETRY_DELAY = 0.01
    
    mock_model = mock_genai.GenerativeModel.return_value
    mock_model.generate_content.side_effect = Exception("Persistent error")
    
    client = GeminiClient()
    
    with pytest.raises(GeminiRequestError):
        client.generate("Test prompt")


@patch('app.llm.gemini_client.get_settings')
def test_generate_empty_response(mock_get_settings, mock_settings, mock_genai):
    """Test handling of empty response."""
    mock_get_settings.return_value = mock_settings
    
    mock_response = Mock()
    mock_response.text = ""
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
    
    client = GeminiClient()
    
    with pytest.raises(GeminiRequestError):
        client.generate("Test prompt")


@patch('app.llm.gemini_client.get_settings')
def test_caching_enabled(mock_get_settings, mock_settings, mock_genai):
    """Test response caching."""
    mock_settings.CACHE_ENABLED = True
    mock_get_settings.return_value = mock_settings
    
    mock_response = Mock()
    mock_response.text = "Cached response"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
    
    client = GeminiClient()
    
    # First call - not cached
    response1 = client.generate("Test prompt")
    assert response1.cached == False
    
    # Second call with same prompt - should be cached
    response2 = client.generate("Test prompt")
    assert response2.cached == True
    assert response2.text == "Cached response"
    
    # API should only be called once
    assert mock_genai.GenerativeModel.return_value.generate_content.call_count == 1


@patch('app.llm.gemini_client.get_settings')
def test_cache_key_includes_model(mock_get_settings, mock_settings, mock_genai):
    """Test that cache key includes model name."""
    mock_settings.CACHE_ENABLED = True
    mock_get_settings.return_value = mock_settings
    
    mock_response = Mock()
    mock_response.text = "Response"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
    
    client = GeminiClient()
    
    # Generate cache key
    key1 = client._get_cache_key("Test prompt")
    
    # Change model name
    client.model_name = "different-model"
    key2 = client._get_cache_key("Test prompt")
    
    # Keys should be different
    assert key1 != key2


@patch('app.llm.gemini_client.get_settings')
def test_clear_cache(mock_get_settings, mock_settings, mock_genai):
    """Test cache clearing."""
    mock_settings.CACHE_ENABLED = True
    mock_get_settings.return_value = mock_settings
    
    mock_response = Mock()
    mock_response.text = "Response"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
    
    client = GeminiClient()
    
    # Generate and cache response
    client.generate("Test prompt")
    assert len(client.cache) > 0
    
    # Clear cache
    client.clear_cache()
    assert len(client.cache) == 0


@patch('app.llm.gemini_client.get_settings')
def test_request_id_generation(mock_get_settings, mock_settings, mock_genai):
    """Test request ID generation."""
    mock_get_settings.return_value = mock_settings
    
    mock_response = Mock()
    mock_response.text = "Response"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
    
    client = GeminiClient()
    
    # Generate two requests
    response1 = client.generate("Prompt 1")
    response2 = client.generate("Prompt 2")
    
    # Request IDs should be different
    assert response1.request_id != response2.request_id
    assert response1.request_id.startswith("req_")
    assert response2.request_id.startswith("req_")


@patch('app.llm.gemini_client.get_settings')
def test_llm_response_to_dict(mock_get_settings, mock_settings, mock_genai):
    """Test LLMResponse serialization."""
    mock_get_settings.return_value = mock_settings
    
    mock_response = Mock()
    mock_response.text = "Response"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
    
    client = GeminiClient()
    response = client.generate("Test prompt")
    
    response_dict = response.to_dict()
    
    assert "text" in response_dict
    assert "token_estimate" in response_dict
    assert "cached" in response_dict
    assert "latency_ms" in response_dict
    assert "request_id" in response_dict


@patch('app.llm.gemini_client.get_settings')
def test_exponential_backoff(mock_get_settings, mock_settings, mock_genai):
    """Test exponential backoff timing."""
    mock_get_settings.return_value = mock_settings
    mock_settings.LLM_RETRY_DELAY = 0.1
    mock_settings.LLM_RETRY_COUNT = 3
    
    mock_model = mock_genai.GenerativeModel.return_value
    mock_model.generate_content.side_effect = [
        Exception("Error 1"),
        Exception("Error 2"),
        Mock(text="Success")
    ]
    
    client = GeminiClient()
    
    start_time = time.time()
    response = client.generate("Test prompt")
    elapsed = time.time() - start_time
    
    # Should have waited: 0.1 + 0.2 = 0.3 seconds minimum
    assert elapsed >= 0.3
    assert response.text == "Success"


@patch('app.llm.gemini_client.get_settings')
def test_latency_measurement(mock_get_settings, mock_settings, mock_genai):
    """Test latency measurement."""
    mock_get_settings.return_value = mock_settings
    
    def slow_generate(*args, **kwargs):
        time.sleep(0.1)
        return Mock(text="Response")
    
    mock_genai.GenerativeModel.return_value.generate_content = slow_generate
    
    client = GeminiClient()
    response = client.generate("Test prompt")
    
    # Latency should be at least 100ms
    assert response.latency_ms >= 100


def test_llm_response_dataclass():
    """Test LLMResponse dataclass."""
    response = LLMResponse(
        text="Test response",
        token_estimate=100,
        cached=False,
        latency_ms=250,
        request_id="req_test123"
    )
    
    assert response.text == "Test response"
    assert response.token_estimate == 100
    assert response.cached == False
    assert response.latency_ms == 250
    assert response.request_id == "req_test123"
