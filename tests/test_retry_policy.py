"""Tests for RetryPolicy."""

import pytest
from unittest.mock import Mock

from app.core.retry_policy import RetryPolicy, with_retry


def test_retry_policy_initialization():
    """Test retry policy initialization."""
    policy = RetryPolicy(max_retries=3, initial_delay=1.0)
    assert policy.max_retries == 3
    assert policy.initial_delay == 1.0


def test_retry_policy_success_first_attempt():
    """Test successful execution on first attempt."""
    policy = RetryPolicy(max_retries=3, initial_delay=0.1)
    
    mock_func = Mock(return_value="success")
    result = policy.execute(mock_func, "arg1", kwarg1="value1")
    
    assert result == "success"
    assert mock_func.call_count == 1


def test_retry_policy_success_after_retries():
    """Test successful execution after retries."""
    policy = RetryPolicy(max_retries=3, initial_delay=0.1)
    
    mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
    result = policy.execute(mock_func)
    
    assert result == "success"
    assert mock_func.call_count == 3


def test_retry_policy_all_attempts_fail():
    """Test all retry attempts fail."""
    policy = RetryPolicy(max_retries=3, initial_delay=0.1)
    
    mock_func = Mock(side_effect=Exception("persistent failure"))
    
    with pytest.raises(Exception, match="persistent failure"):
        policy.execute(mock_func)
    
    assert mock_func.call_count == 3


def test_with_retry_decorator():
    """Test with_retry decorator."""
    call_count = 0
    
    @with_retry(max_retries=3, initial_delay=0.1)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("fail")
        return "success"
    
    result = flaky_function()
    
    assert result == "success"
    assert call_count == 2
