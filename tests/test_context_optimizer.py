"""Tests for context optimization engine."""

import pytest
import networkx as nx

from app.parsers.base import ASTNode
from app.context_optimizer import (
    ContextOptimizer,
    OptimizedContext,
    MissingNodeError,
    EmptyGraphError,
    TokenLimitExceededError
)


@pytest.fixture
def sample_ast_nodes():
    """Create sample AST nodes for testing."""
    return {
        "file1.py:func_a:10": ASTNode(
            id="file1.py::func_a",
            name="func_a",
            node_type="function",
            parameters=["x"],
            return_type="int",
            called_symbols=["func_b"],
            imports=[],
            file_path="file1.py",
            start_line=10,
            end_line=15,
            raw_source="def func_a(x):\n    return func_b(x)"
        ),
        "file1.py:func_b:20": ASTNode(
            id="file1.py::func_b",
            name="func_b",
            node_type="function",
            parameters=["y"],
            return_type="int",
            called_symbols=["func_c"],
            imports=[],
            file_path="file1.py",
            start_line=20,
            end_line=25,
            raw_source="def func_b(y):\n    return func_c(y)"
        ),
        "file1.py:func_c:30": ASTNode(
            id="file1.py::func_c",
            name="func_c",
            node_type="function",
            parameters=["z"],
            return_type="int",
            called_symbols=[],
            imports=[],
            file_path="file1.py",
            start_line=30,
            end_line=35,
            raw_source="def func_c(z):\n    return z * 2"
        ),
    }


@pytest.fixture
def sample_graph(sample_ast_nodes):
    """Create sample dependency graph."""
    graph = nx.DiGraph()
    
    # Add nodes
    for node_id in sample_ast_nodes.keys():
        graph.add_node(node_id)
    
    # Add edges
    graph.add_edge("file1.py:func_a:10", "file1.py:func_b:20", edge_type="calls")
    graph.add_edge("file1.py:func_b:20", "file1.py:func_c:30", edge_type="calls")
    
    return graph


def test_optimizer_initialization():
    """Test optimizer initialization with defaults."""
    optimizer = ContextOptimizer()
    
    assert optimizer.max_tokens > 0
    assert optimizer.expansion_depth > 0


def test_optimizer_initialization_custom():
    """Test optimizer initialization with custom values."""
    optimizer = ContextOptimizer(max_tokens=5000, expansion_depth=2)
    
    assert optimizer.max_tokens == 5000
    assert optimizer.expansion_depth == 2


def test_optimize_context_basic(sample_graph, sample_ast_nodes):
    """Test basic context optimization."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=2)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes
    )
    
    assert isinstance(result, OptimizedContext)
    assert "file1.py:func_a:10" in result.included_nodes
    assert result.estimated_tokens > 0
    assert result.combined_source != ""


def test_optimize_context_target_always_included(sample_graph, sample_ast_nodes):
    """Test that target node is always included."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=2)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes
    )
    
    # Target must be first in included nodes
    assert result.included_nodes[0] == "file1.py:func_a:10"


def test_optimize_context_depth_zero(sample_graph, sample_ast_nodes):
    """Test optimization with depth 0 (target only)."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=0)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes,
        expansion_depth=0
    )
    
    # Only target node should be included
    assert len(result.included_nodes) == 1
    assert result.included_nodes[0] == "file1.py:func_a:10"


def test_optimize_context_depth_one(sample_graph, sample_ast_nodes):
    """Test optimization with depth 1 (target + direct dependencies)."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=1)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes,
        expansion_depth=1
    )
    
    # Should include target and func_b
    assert "file1.py:func_a:10" in result.included_nodes
    assert "file1.py:func_b:20" in result.included_nodes
    assert len(result.included_nodes) == 2


def test_optimize_context_depth_two(sample_graph, sample_ast_nodes):
    """Test optimization with depth 2."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=2)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes,
        expansion_depth=2
    )
    
    # Should include all three nodes
    assert len(result.included_nodes) == 3


def test_optimize_context_token_limit(sample_graph, sample_ast_nodes):
    """Test that token limit is respected."""
    # Create nodes with more content to test token limiting
    large_ast_nodes = {
        "file1.py:func_a:10": ASTNode(
            id="file1.py::func_a",
            name="func_a",
            node_type="function",
            parameters=["x"],
            return_type="int",
            called_symbols=["func_b", "func_c"],
            imports=[],
            file_path="file1.py",
            start_line=10,
            end_line=15,
            raw_source="def func_a(x):\n    # This is a longer function with more content\n    result = func_b(x)\n    return result"
        ),
        "file1.py:func_b:20": ASTNode(
            id="file1.py::func_b",
            name="func_b",
            node_type="function",
            parameters=["y"],
            return_type="int",
            called_symbols=[],
            imports=[],
            file_path="file1.py",
            start_line=20,
            end_line=25,
            raw_source="def func_b(y):\n    # Another function with substantial content\n    value = y * 2\n    return value"
        ),
        "file1.py:func_c:30": ASTNode(
            id="file1.py::func_c",
            name="func_c",
            node_type="function",
            parameters=["z"],
            return_type="int",
            called_symbols=[],
            imports=[],
            file_path="file1.py",
            start_line=30,
            end_line=35,
            raw_source="def func_c(z):\n    # Yet another function with more text\n    result = z * 3\n    return result"
        ),
    }
    
    # Set low token limit
    optimizer = ContextOptimizer(max_tokens=30, expansion_depth=2)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=large_ast_nodes,
        max_tokens=30
    )
    
    # Should stop adding nodes when token limit reached
    assert result.estimated_tokens <= 30
    # With low limit, should exclude some nodes
    assert len(result.included_nodes) < 3


def test_optimize_context_empty_graph():
    """Test optimization with empty graph."""
    optimizer = ContextOptimizer()
    empty_graph = nx.DiGraph()
    
    with pytest.raises(EmptyGraphError):
        optimizer.optimize_context(
            target_node_id="nonexistent",
            dependency_graph=empty_graph,
            ast_index={}
        )


def test_optimize_context_missing_target_in_graph(sample_ast_nodes):
    """Test optimization with missing target node in graph."""
    optimizer = ContextOptimizer()
    graph = nx.DiGraph()
    graph.add_node("other_node")
    
    with pytest.raises(MissingNodeError):
        optimizer.optimize_context(
            target_node_id="file1.py:func_a:10",
            dependency_graph=graph,
            ast_index=sample_ast_nodes
        )


def test_optimize_context_missing_target_in_ast(sample_graph):
    """Test optimization with missing target node in AST index."""
    optimizer = ContextOptimizer()
    
    with pytest.raises(MissingNodeError):
        optimizer.optimize_context(
            target_node_id="file1.py:func_a:10",
            dependency_graph=sample_graph,
            ast_index={}
        )


def test_optimize_context_target_exceeds_limit(sample_graph, sample_ast_nodes):
    """Test when target node alone exceeds token limit."""
    optimizer = ContextOptimizer(max_tokens=1, expansion_depth=2)
    
    with pytest.raises(TokenLimitExceededError):
        optimizer.optimize_context(
            target_node_id="file1.py:func_a:10",
            dependency_graph=sample_graph,
            ast_index=sample_ast_nodes,
            max_tokens=1
        )


def test_estimate_tokens():
    """Test token estimation via token_estimator."""
    optimizer = ContextOptimizer()
    
    # Empty string
    assert optimizer.token_estimator.estimate_tokens("") == 0
    
    # Short text
    tokens = optimizer.token_estimator.estimate_tokens("hello world")
    assert tokens > 0
    
    # Longer text should have more tokens
    short_tokens = optimizer.token_estimator.estimate_tokens("hello")
    long_tokens = optimizer.token_estimator.estimate_tokens("hello world this is a longer text")
    assert long_tokens > short_tokens


def test_estimate_tokens_deterministic():
    """Test that token estimation is deterministic."""
    optimizer = ContextOptimizer()
    text = "def func():\n    return 42"
    
    tokens1 = optimizer.token_estimator.estimate_tokens(text)
    tokens2 = optimizer.token_estimator.estimate_tokens(text)
    
    assert tokens1 == tokens2


def test_remove_comments_single_line():
    """Test removal of single-line comments via token_estimator."""
    optimizer = ContextOptimizer()
    
    source = """
def func():
    // This is a comment
    return 42  // Another comment
"""
    
    cleaned = optimizer.token_estimator.remove_comments(source)
    
    assert "//" not in cleaned
    assert "return 42" in cleaned


def test_remove_comments_python():
    """Test removal of Python comments via token_estimator."""
    optimizer = ContextOptimizer()
    
    source = """
def func():
    # This is a comment
    return 42  # Another comment
"""
    
    cleaned = optimizer.token_estimator.remove_comments(source)
    
    assert "# This is a comment" not in cleaned
    assert "return 42" in cleaned


def test_remove_comments_preserves_code():
    """Test that comment removal preserves actual code."""
    optimizer = ContextOptimizer()
    
    source = "def func():\n    return 42"
    cleaned = optimizer.token_estimator.remove_comments(source)
    
    assert "def func()" in cleaned
    assert "return 42" in cleaned


def test_clean_source():
    """Test source code cleaning via token_estimator."""
    optimizer = ContextOptimizer()
    
    source = """
def func():
    // Comment
    return 42
"""
    
    cleaned = optimizer.token_estimator.clean_source(source)
    
    assert cleaned != ""
    assert "//" not in cleaned


def test_clean_source_empty():
    """Test cleaning empty source via token_estimator."""
    optimizer = ContextOptimizer()
    
    cleaned = optimizer.token_estimator.clean_source("")
    assert cleaned == ""


def test_remove_unused_imports():
    """Test unused import removal (placeholder) via token_estimator."""
    optimizer = ContextOptimizer()
    
    source = "import os\nimport sys\n\ndef func():\n    return 42"
    
    # Currently a placeholder, should return unchanged
    result = optimizer.token_estimator.remove_unused_imports(source)
    assert result == source


def test_optimized_context_to_dict(sample_graph, sample_ast_nodes):
    """Test OptimizedContext serialization."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=2)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes
    )
    
    result_dict = result.to_dict()
    
    assert "included_nodes" in result_dict
    assert "excluded_nodes" in result_dict
    assert "combined_source" in result_dict
    assert "estimated_tokens" in result_dict
    assert "target_node_id" in result_dict
    assert "expansion_depth" in result_dict


def test_deterministic_output(sample_graph, sample_ast_nodes):
    """Test that same input produces same output."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=2)
    
    result1 = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes
    )
    
    result2 = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes
    )
    
    assert result1.included_nodes == result2.included_nodes
    assert result1.excluded_nodes == result2.excluded_nodes
    assert result1.estimated_tokens == result2.estimated_tokens


def test_combined_source_format(sample_graph, sample_ast_nodes):
    """Test that combined source has proper formatting."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=2)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes
    )
    
    # Should contain file path comments
    assert "// File:" in result.combined_source
    assert "file1.py" in result.combined_source
    
    # Should contain actual code
    assert "func_a" in result.combined_source


def test_large_graph_performance():
    """Test performance with larger graph."""
    # Create a larger graph
    graph = nx.DiGraph()
    ast_index = {}
    
    for i in range(100):
        node_id = f"file.py:func{i}:{i*10}"
        graph.add_node(node_id)
        
        ast_index[node_id] = ASTNode(
            id=f"file.py::func{i}",
            name=f"func{i}",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=[f"func{i+1}"] if i < 99 else [],
            imports=[],
            file_path="file.py",
            start_line=i*10,
            end_line=i*10+5,
            raw_source=f"def func{i}():\n    return {i}"
        )
        
        if i < 99:
            graph.add_edge(node_id, f"file.py:func{i+1}:{(i+1)*10}", edge_type="calls")
    
    optimizer = ContextOptimizer(max_tokens=5000, expansion_depth=3)
    
    result = optimizer.optimize_context(
        target_node_id="file.py:func0:0",
        dependency_graph=graph,
        ast_index=ast_index
    )
    
    # Should complete without error
    assert len(result.included_nodes) > 0
    assert result.estimated_tokens <= 5000


def test_override_parameters(sample_graph, sample_ast_nodes):
    """Test that method parameters override instance defaults."""
    optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=5)
    
    result = optimizer.optimize_context(
        target_node_id="file1.py:func_a:10",
        dependency_graph=sample_graph,
        ast_index=sample_ast_nodes,
        max_tokens=100,  # Override
        expansion_depth=1  # Override
    )
    
    # Should use overridden values
    assert result.expansion_depth == 1
    assert result.estimated_tokens <= 100


def test_optimizer_with_custom_token_estimator():
    """Test ContextOptimizer with custom TokenEstimator injection."""
    from app.context_optimizer.token_estimator import HeuristicTokenEstimator
    
    # Create custom estimator with different ratio
    custom_estimator = HeuristicTokenEstimator(chars_per_token=5)
    
    # Create optimizer with custom estimator
    optimizer = ContextOptimizer(token_estimator=custom_estimator)
    
    # Verify estimator was injected
    assert optimizer.token_estimator is custom_estimator
    assert optimizer.token_estimator.chars_per_token == 5


def test_optimizer_default_token_estimator():
    """Test that ContextOptimizer uses default HeuristicTokenEstimator if none provided."""
    from app.context_optimizer.token_estimator import HeuristicTokenEstimator
    
    optimizer = ContextOptimizer()
    
    # Should have default estimator
    assert optimizer.token_estimator is not None
    assert isinstance(optimizer.token_estimator, HeuristicTokenEstimator)
    assert optimizer.token_estimator.chars_per_token == 4


def test_context_window_exceeded_error():
    """Test that ContextWindowExceededError is raised when context exceeds safe limit."""
    from app.context_optimizer.schema import ContextWindowExceededError
    from app.context_optimizer.token_estimator import HeuristicTokenEstimator
    
    # Create optimizer with very low token limit
    optimizer = ContextOptimizer(max_tokens=100)
    
    # Create graph with large nodes
    graph = nx.DiGraph()
    graph.add_node("node1")
    
    # Create AST node with large source (>90 tokens at 4 chars/token = >360 chars)
    large_source = "x" * 400  # 400 chars = 100 tokens, exceeds 90% of 100
    
    ast_index = {
        "node1": ASTNode(
            id="test::node1",
            name="node1",
            node_type="function",
            parameters=[],
            return_type=None,
            called_symbols=[],
            imports=[],
            file_path="test.py",
            start_line=1,
            end_line=10,
            raw_source=large_source
        )
    }
    
    # Should raise ContextWindowExceededError
    with pytest.raises(ContextWindowExceededError) as exc_info:
        optimizer.optimize_context("node1", graph, ast_index)
    
    assert "exceeds safe limit" in str(exc_info.value)


def test_context_window_within_safe_limit():
    """Test that optimization succeeds when context is within safe limit."""
    optimizer = ContextOptimizer(max_tokens=1000)
    
    # Create simple graph
    graph = nx.DiGraph()
    graph.add_node("node1")
    
    # Create AST node with small source
    small_source = "def test(): pass"  # ~16 chars = 4 tokens
    
    ast_index = {
        "node1": ASTNode(
            id="test::node1",
            name="node1",
            node_type="function",
            parameters=[],
            return_type=None,
            called_symbols=[],
            imports=[],
            file_path="test.py",
            start_line=1,
            end_line=1,
            raw_source=small_source
        )
    }
    
    # Should succeed without raising
    result = optimizer.optimize_context("node1", graph, ast_index)
    
    assert result.target_node_id == "node1"
    assert len(result.included_nodes) == 1
    assert result.estimated_tokens < 1000 * 0.9  # Within safe limit


def test_token_estimator_used_for_estimation():
    """Test that optimizer uses injected token estimator for token counting."""
    from app.context_optimizer.token_estimator import HeuristicTokenEstimator
    
    # Create custom estimator with different ratio
    custom_estimator = HeuristicTokenEstimator(chars_per_token=2)  # More tokens per char
    optimizer = ContextOptimizer(token_estimator=custom_estimator, max_tokens=1000)
    
    # Create graph
    graph = nx.DiGraph()
    graph.add_node("node1")
    
    # Create AST node
    source = "x" * 100  # 100 chars
    ast_index = {
        "node1": ASTNode(
            id="test::node1",
            name="node1",
            node_type="function",
            parameters=[],
            return_type=None,
            called_symbols=[],
            imports=[],
            file_path="test.py",
            start_line=1,
            end_line=1,
            raw_source=source
        )
    }
    
    result = optimizer.optimize_context("node1", graph, ast_index)
    
    # With chars_per_token=2, 100 chars = 50 tokens
    # Should be approximately 50 (may vary due to cleaning)
    assert 40 <= result.estimated_tokens <= 60
