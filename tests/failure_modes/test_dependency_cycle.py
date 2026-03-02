"""Test dependency cycle detection and handling."""

import pytest
import networkx as nx

from app.translation.orchestrator import TranslationOrchestrator
from app.dependency_graph.graph_builder import GraphBuilder
from app.parsers.base import ASTNode
from unittest.mock import Mock
from app.llm.llm_service import LLMService


@pytest.mark.asyncio
async def test_circular_dependency_detection():
    """Test that circular dependencies are detected and raise ValueError."""
    mock_llm = Mock(spec=LLMService)
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    # Create graph with circular dependency: A -> B -> C -> A
    graph = nx.DiGraph()
    graph.add_edge("nodeA", "nodeB")
    graph.add_edge("nodeB", "nodeC")
    graph.add_edge("nodeC", "nodeA")  # Creates cycle
    
    ast_index = {
        "nodeA": ASTNode(
            id="nodeA",
            name="ClassA",
            node_type="class",
            file_path="a.java",
            start_line=1,
            end_line=5,
            raw_source="class A {}",
            parameters=[],
            called_symbols=["ClassB"]
        ),
        "nodeB": ASTNode(
            id="nodeB",
            name="ClassB",
            node_type="class",
            file_path="b.java",
            start_line=1,
            end_line=5,
            raw_source="class B {}",
            parameters=[],
            called_symbols=["ClassC"]
        ),
        "nodeC": ASTNode(
            id="nodeC",
            name="ClassC",
            node_type="class",
            file_path="c.java",
            start_line=1,
            end_line=5,
            raw_source="class C {}",
            parameters=[],
            called_symbols=["ClassA"]
        )
    }
    
    # Should raise ValueError with cycle information
    with pytest.raises(ValueError, match="Circular dependencies detected"):
        await orchestrator.translate_repository(graph, ast_index)


def test_graph_builder_detects_cycles():
    """Test that GraphBuilder detects and logs cycles."""
    builder = GraphBuilder()
    
    # Create AST nodes with circular dependencies
    nodes = [
        ASTNode(
            id="file1.py:FuncA:1",
            name="FuncA",
            node_type="function",
            file_path="file1.py",
            start_line=1,
            end_line=3,
            raw_source="def FuncA(): FuncB()",
            parameters=[],
            called_symbols=["FuncB"]
        ),
        ASTNode(
            id="file1.py:FuncB:5",
            name="FuncB",
            node_type="function",
            file_path="file1.py",
            start_line=5,
            end_line=7,
            raw_source="def FuncB(): FuncA()",
            parameters=[],
            called_symbols=["FuncA"]
        )
    ]
    
    graph = builder.build_graph(nodes)
    
    # Verify graph was built (cycles are logged but don't prevent graph creation)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 2
    
    # Verify cycle exists
    cycles = list(nx.simple_cycles(graph))
    assert len(cycles) > 0


@pytest.mark.asyncio
async def test_no_infinite_recursion_on_cycle():
    """Test that cycle detection doesn't cause infinite recursion."""
    mock_llm = Mock(spec=LLMService)
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    # Create self-referencing node
    graph = nx.DiGraph()
    graph.add_edge("nodeA", "nodeA")  # Self-loop
    
    ast_index = {
        "nodeA": ASTNode(
            id="nodeA",
            name="RecursiveFunc",
            node_type="function",
            file_path="test.py",
            start_line=1,
            end_line=3,
            raw_source="def recursive(): recursive()",
            parameters=[],
            called_symbols=["recursive"]
        )
    }
    
    # Should detect cycle and raise, not hang
    with pytest.raises(ValueError, match="Circular dependencies"):
        await orchestrator.translate_repository(graph, ast_index)


def test_cycle_error_message_contains_details():
    """Test that cycle error message contains useful information."""
    mock_llm = Mock(spec=LLMService)
    orchestrator = TranslationOrchestrator(llm_service=mock_llm)
    
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "A")
    
    ast_index = {
        "A": ASTNode(
            id="A",
            name="A",
            node_type="class",
            file_path="a.py",
            start_line=1,
            end_line=2,
            raw_source="class A: pass",
            parameters=[],
            called_symbols=[]
        ),
        "B": ASTNode(
            id="B",
            name="B",
            node_type="class",
            file_path="b.py",
            start_line=1,
            end_line=2,
            raw_source="class B: pass",
            parameters=[],
            called_symbols=[]
        )
    }
    
    try:
        import asyncio
        asyncio.run(orchestrator.translate_repository(graph, ast_index))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        error_msg = str(e)
        assert "Circular dependencies" in error_msg
        assert "cycles found" in error_msg
