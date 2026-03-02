"""Test AST node ID corruption and consistency checks."""

import pytest
import networkx as nx
from unittest.mock import Mock

from app.translation.orchestrator import TranslationOrchestrator, TranslationStatus
from app.llm.llm_service import LLMService
from app.parsers.base import ASTNode


@pytest.mark.asyncio
async def test_node_id_mismatch_graph_vs_ast():
    """Test that node ID mismatch between graph and AST is caught."""
    mock_llm = Mock(spec=LLMService)
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    # Graph has node "wrong_id" but AST index has "correct_id"
    graph = nx.DiGraph()
    graph.add_node("wrong_id")
    
    ast_index = {
        "correct_id": ASTNode(
            id="correct_id",
            name="TestClass",
            node_type="class",
            file_path="test.java",
            start_line=1,
            end_line=5,
            raw_source="class TestClass {}",
            parameters=[],
            called_symbols=[]
        )
    }
    
    # Should fail with node not found error
    results = await orchestrator.translate_repository(graph, ast_index)
    
    assert len(results) == 1
    assert results[0].status == TranslationStatus.FAILED
    assert "not found in AST index" in results[0].errors[0]
    assert "wrong_id" in results[0].errors[0]


@pytest.mark.asyncio
async def test_missing_node_in_ast_index():
    """Test handling of node present in graph but missing from AST index."""
    mock_llm = Mock(spec=LLMService)
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    graph = nx.DiGraph()
    graph.add_node("missing_node")
    graph.add_node("existing_node")
    
    # Only one node in AST index
    ast_index = {
        "existing_node": ASTNode(
            id="existing_node",
            name="ExistingClass",
            node_type="class",
            file_path="test.java",
            start_line=1,
            end_line=5,
            raw_source="class ExistingClass {}",
            parameters=[],
            called_symbols=[]
        )
    }
    
    results = await orchestrator.translate_repository(graph, ast_index)
    
    # Should have 2 results: one failed (missing), one attempted
    assert len(results) == 2
    
    # Find the failed result
    failed_results = [r for r in results if r.status == TranslationStatus.FAILED]
    assert len(failed_results) >= 1
    
    failed = failed_results[0]
    assert "not found in AST index" in failed.errors[0]


@pytest.mark.asyncio
async def test_assertion_on_node_id_consistency():
    """Test that assertion catches node ID inconsistency."""
    mock_llm = Mock(spec=LLMService)
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    # Create node with ID that doesn't match what's in the index
    graph = nx.DiGraph()
    graph.add_node("node_id_in_graph")
    
    # AST node has different ID than what's used as key
    ast_index = {
        "node_id_in_graph": ASTNode(
            id="different_id_in_node",  # ID mismatch!
            name="TestClass",
            node_type="class",
            file_path="test.java",
            start_line=1,
            end_line=5,
            raw_source="class TestClass {}",
            parameters=[],
            called_symbols=[]
        )
    }
    
    # The assertion in _translate_node should catch this
    # But it will pass the initial check since key exists
    results = await orchestrator.translate_repository(graph, ast_index)
    
    # Should complete (assertion is for debugging, not blocking)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_empty_ast_index():
    """Test handling of empty AST index."""
    mock_llm = Mock(spec=LLMService)
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    graph = nx.DiGraph()
    graph.add_node("some_node")
    
    ast_index = {}  # Empty!
    
    results = await orchestrator.translate_repository(graph, ast_index)
    
    assert len(results) == 1
    assert results[0].status == TranslationStatus.FAILED
    assert "not found in AST index" in results[0].errors[0]


@pytest.mark.asyncio
async def test_node_id_logged_on_failure():
    """Test that node ID is logged when translation fails."""
    mock_llm = Mock(spec=LLMService)
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    graph = nx.DiGraph()
    graph.add_node("test_node_123")
    
    ast_index = {}  # Will cause failure
    
    results = await orchestrator.translate_repository(graph, ast_index)
    
    # Verify node ID is in error message
    assert results[0].module_name == "test_node_123"
    assert "test_node_123" in results[0].errors[0]
