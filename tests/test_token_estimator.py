"""Unit tests for token estimator module.

Tests verify:
- Token estimation accuracy (sanity checks)
- Source code cleaning
- Comment removal
- Import removal
- Estimator swappability
"""

import pytest

from app.context_optimizer.token_estimator import (
    TokenEstimator,
    HeuristicTokenEstimator,
    TiktokenEstimator
)


@pytest.fixture
def heuristic_estimator():
    """Create HeuristicTokenEstimator for testing."""
    return HeuristicTokenEstimator()


@pytest.fixture
def custom_estimator():
    """Create HeuristicTokenEstimator with custom chars_per_token."""
    return HeuristicTokenEstimator(chars_per_token=5)


def test_heuristic_estimator_initialization():
    """Test HeuristicTokenEstimator initializes with default parameters."""
    estimator = HeuristicTokenEstimator()
    assert estimator.chars_per_token == 4


def test_heuristic_estimator_custom_chars_per_token():
    """Test HeuristicTokenEstimator with custom chars_per_token."""
    estimator = HeuristicTokenEstimator(chars_per_token=5)
    assert estimator.chars_per_token == 5


def test_estimate_tokens_empty_string(heuristic_estimator):
    """Test token estimation for empty string."""
    tokens = heuristic_estimator.estimate_tokens("")
    assert tokens == 0


def test_estimate_tokens_short_text(heuristic_estimator):
    """Test token estimation for short text."""
    text = "Hello world"  # 11 chars
    tokens = heuristic_estimator.estimate_tokens(text)
    # 11 / 4 = 2.75, rounds to 2
    assert tokens == 2


def test_estimate_tokens_long_text(heuristic_estimator):
    """Test token estimation for longer text."""
    text = "This is a longer piece of text that should result in more tokens."  # 66 chars
    tokens = heuristic_estimator.estimate_tokens(text)
    # 66 / 4 = 16.5, rounds to 16
    assert tokens == 16


def test_estimate_tokens_minimum_one(heuristic_estimator):
    """Test that token estimation returns at least 1 for non-empty text."""
    text = "a"  # 1 char
    tokens = heuristic_estimator.estimate_tokens(text)
    assert tokens >= 1


def test_estimate_tokens_custom_ratio(custom_estimator):
    """Test token estimation with custom chars_per_token ratio."""
    text = "Hello world"  # 11 chars
    tokens = custom_estimator.estimate_tokens(text)
    # 11 / 5 = 2.2, rounds to 2
    assert tokens == 2


def test_remove_comments_single_line_slash(heuristic_estimator):
    """Test removal of // style comments."""
    source = """
    int x = 5; // This is a comment
    int y = 10;
    """
    cleaned = heuristic_estimator.remove_comments(source)
    assert "// This is a comment" not in cleaned
    assert "int x = 5;" in cleaned
    assert "int y = 10;" in cleaned


def test_remove_comments_single_line_hash(heuristic_estimator):
    """Test removal of # style comments."""
    source = """
    x = 5  # This is a comment
    y = 10
    """
    cleaned = heuristic_estimator.remove_comments(source)
    assert "# This is a comment" not in cleaned
    assert "x = 5" in cleaned
    assert "y = 10" in cleaned


def test_remove_comments_preserves_include(heuristic_estimator):
    """Test that #include directives are preserved."""
    source = """
    #include <stdio.h>
    int main() {
        return 0;
    }
    """
    cleaned = heuristic_estimator.remove_comments(source)
    assert "#include <stdio.h>" in cleaned


def test_remove_comments_multiline(heuristic_estimator):
    """Test removal of /* */ style comments."""
    source = """
    int x = 5;
    /* This is a
       multiline comment */
    int y = 10;
    """
    cleaned = heuristic_estimator.remove_comments(source)
    assert "/* This is a" not in cleaned
    assert "multiline comment */" not in cleaned
    assert "int x = 5;" in cleaned
    assert "int y = 10;" in cleaned


def test_remove_comments_empty_string(heuristic_estimator):
    """Test comment removal on empty string."""
    cleaned = heuristic_estimator.remove_comments("")
    assert cleaned == ""


def test_remove_unused_imports_placeholder(heuristic_estimator):
    """Test that remove_unused_imports is placeholder (returns unchanged)."""
    source = "import os\nimport sys\nx = 5"
    result = heuristic_estimator.remove_unused_imports(source)
    # Placeholder implementation returns source unchanged
    assert result == source


def test_clean_source_combines_operations(heuristic_estimator):
    """Test that clean_source applies both comment removal and import removal."""
    source = """
    import os  # Import OS module
    // This is a comment
    int x = 5;
    """
    cleaned = heuristic_estimator.clean_source(source)
    
    # Comments should be removed
    assert "// This is a comment" not in cleaned
    assert "# Import OS module" not in cleaned
    
    # Code should remain
    assert "import os" in cleaned
    assert "int x = 5;" in cleaned


def test_clean_source_strips_whitespace(heuristic_estimator):
    """Test that clean_source strips leading/trailing whitespace."""
    source = "\n\n  int x = 5;  \n\n"
    cleaned = heuristic_estimator.clean_source(source)
    assert cleaned == "int x = 5;"


def test_clean_source_empty_string(heuristic_estimator):
    """Test clean_source on empty string."""
    cleaned = heuristic_estimator.clean_source("")
    assert cleaned == ""


def test_token_estimator_is_abstract():
    """Test that TokenEstimator cannot be instantiated directly."""
    with pytest.raises(TypeError):
        TokenEstimator()


def test_heuristic_estimator_implements_interface():
    """Test that HeuristicTokenEstimator implements TokenEstimator interface."""
    estimator = HeuristicTokenEstimator()
    assert isinstance(estimator, TokenEstimator)
    assert hasattr(estimator, 'estimate_tokens')
    assert hasattr(estimator, 'clean_source')
    assert hasattr(estimator, 'remove_comments')
    assert hasattr(estimator, 'remove_unused_imports')


def test_tiktoken_estimator_not_implemented():
    """Test that TiktokenEstimator raises NotImplementedError."""
    with pytest.raises(NotImplementedError) as exc_info:
        TiktokenEstimator()
    assert "tiktoken package" in str(exc_info.value)


def test_estimator_swappability():
    """Test that estimators can be swapped via interface."""
    estimators = [
        HeuristicTokenEstimator(),
        HeuristicTokenEstimator(chars_per_token=5)
    ]
    
    text = "Hello world"
    
    for estimator in estimators:
        # All should implement the interface
        assert isinstance(estimator, TokenEstimator)
        
        # All should return valid token counts
        tokens = estimator.estimate_tokens(text)
        assert isinstance(tokens, int)
        assert tokens > 0


def test_estimate_tokens_consistency(heuristic_estimator):
    """Test that token estimation is deterministic."""
    text = "This is a test string for consistency checking."
    
    tokens1 = heuristic_estimator.estimate_tokens(text)
    tokens2 = heuristic_estimator.estimate_tokens(text)
    
    assert tokens1 == tokens2


def test_clean_source_preserves_code_structure(heuristic_estimator):
    """Test that clean_source preserves essential code structure."""
    source = """
    def calculate(x, y):  # Calculate sum
        # This is a helper function
        return x + y  // Return result
    """
    
    cleaned = heuristic_estimator.clean_source(source)
    
    # Function definition should be preserved
    assert "def calculate(x, y):" in cleaned
    assert "return x + y" in cleaned


def test_token_estimation_sanity_check(heuristic_estimator):
    """Sanity check: longer text should have more tokens."""
    short_text = "Hello"
    long_text = "Hello world this is a much longer piece of text"
    
    short_tokens = heuristic_estimator.estimate_tokens(short_text)
    long_tokens = heuristic_estimator.estimate_tokens(long_text)
    
    assert long_tokens > short_tokens


def test_token_estimation_approximate_accuracy(heuristic_estimator):
    """Test that token estimation is approximately accurate for typical code."""
    # Typical function with ~150 characters
    code = """
    def process_data(input_list):
        result = []
        for item in input_list:
            result.append(item * 2)
        return result
    """
    
    tokens = heuristic_estimator.estimate_tokens(code)
    
    # Should be roughly 30-40 tokens (150 chars / 4 = 37.5)
    assert 30 <= tokens <= 45
