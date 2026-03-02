"""Test LLM provider failure scenarios."""

import pytest
from unittest.mock import Mock, patch
import networkx as nx

from app.translation.orchestrator import TranslationOrchestrator, TranslationStatus
from app.llm.llm_service import LLMService
from app.llm.exceptions import GeminiRequestError
from app.parsers.base import ASTNode


@pytest.mark.asyncio
async def test_api_quota_exceeded():
    """Test that API quota exceeded is handled gracefully."""
    # Create mock LLM service that raises quota error
    mock_llm = Mock(spec=LLMService)
    mock_llm.generate.side_effect = GeminiRequestError(
        "429 You exceeded your current quota"
    )
    
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    # Create minimal test data
    graph = nx.DiGraph()
    graph.add_node("test_node")
    
    ast_index = {
        "test_node": ASTNode(
            id="test_node",
            name="TestClass",
            node_type="class",
            file_path="test.java",
            start_line=1,
            end_line=10,
            raw_source="class TestClass {}",
            parameters=[],
            called_symbols=[]
        )
    }
    
    # Execute translation
    results = await orchestrator.translate_repository(graph, ast_index)
    
    # Verify failure handling
    assert len(results) == 1
    assert results[0].status == TranslationStatus.FAILED
    assert "429" in results[0].errors[0] or "quota" in results[0].errors[0].lower()
    assert results[0].module_name == "test_node"


@pytest.mark.asyncio
async def test_network_timeout():
    """Test that network timeout is handled gracefully."""
    mock_llm = Mock(spec=LLMService)
    mock_llm.generate.side_effect = GeminiRequestError("Network timeout")
    
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    graph = nx.DiGraph()
    graph.add_node("test_node")
    
    ast_index = {
        "test_node": ASTNode(
            id="test_node",
            name="TestFunc",
            node_type="function",
            file_path="test.py",
            start_line=1,
            end_line=5,
            raw_source="def test(): pass",
            parameters=[],
            called_symbols=[]
        )
    }
    
    results = await orchestrator.translate_repository(graph, ast_index)
    
    assert len(results) == 1
    assert results[0].status == TranslationStatus.FAILED
    assert "timeout" in results[0].errors[0].lower()


@pytest.mark.asyncio
async def test_model_not_found():
    """Test that model not found error is handled."""
    mock_llm = Mock(spec=LLMService)
    mock_llm.generate.side_effect = GeminiRequestError("Model not found: invalid-model")
    
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    graph = nx.DiGraph()
    graph.add_node("test_node")
    
    ast_index = {
        "test_node": ASTNode(
            id="test_node",
            name="TestMethod",
            node_type="method",
            file_path="test.java",
            start_line=1,
            end_line=3,
            raw_source="void test() {}",
            parameters=[],
            called_symbols=[]
        )
    }
    
    results = await orchestrator.translate_repository(graph, ast_index)
    
    assert len(results) == 1
    assert results[0].status == TranslationStatus.FAILED
    assert "model" in results[0].errors[0].lower()


@pytest.mark.asyncio
async def test_pipeline_continues_after_node_failure():
    """Test that pipeline continues translating remaining nodes after one fails."""
    mock_llm = Mock(spec=LLMService)
    
    # First call fails, second succeeds
    from app.llm.interface import LLMResponse
    mock_llm.generate.side_effect = [
        GeminiRequestError("API Error"),
        LLMResponse(
            text='{"translated_code": "def test(): pass", "dependencies": [], "notes": "OK"}',
            token_count=10,
            model_name="gemini-test"
        )
    ]
    
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    graph = nx.DiGraph()
    graph.add_node("node1")
    graph.add_node("node2")
    
    ast_index = {
        "node1": ASTNode(
            id="node1",
            name="Class1",
            node_type="class",
            file_path="test1.java",
            start_line=1,
            end_line=5,
            raw_source="class Class1 {}",
            parameters=[],
            called_symbols=[]
        ),
        "node2": ASTNode(
            id="node2",
            name="Class2",
            node_type="class",
            file_path="test2.java",
            start_line=1,
            end_line=5,
            raw_source="class Class2 {}",
            parameters=[],
            called_symbols=[]
        )
    }
    
    results = await orchestrator.translate_repository(graph, ast_index)
    
    # Verify both nodes were processed
    assert len(results) == 2
    assert results[0].status == TranslationStatus.FAILED
    assert results[1].status == TranslationStatus.SUCCESS
    assert results[1].translated_code == "def test(): pass"
