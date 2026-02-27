"""Tests for dependency graph builder."""

import pytest
import networkx as nx

from app.parsers.base import ASTNode
from app.dependency_graph import GraphBuilder


@pytest.fixture
def sample_ast_nodes():
    """Create sample AST nodes for testing."""
    return [
        ASTNode(
            id="file1.py::func_a",
            name="func_a",
            node_type="function",
            parameters=["x"],
            return_type="int",
            called_symbols=["func_b", "func_c"],
            imports=["math", "os"],
            file_path="file1.py",
            start_line=10,
            end_line=20,
            raw_source="def func_a(x):"
        ),
        ASTNode(
            id="file1.py::func_b",
            name="func_b",
            node_type="function",
            parameters=["y"],
            return_type="str",
            called_symbols=["func_c"],
            imports=[],
            file_path="file1.py",
            start_line=25,
            end_line=30,
            raw_source="def func_b(y):"
        ),
        ASTNode(
            id="file1.py::func_c",
            name="func_c",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=[],
            imports=[],
            file_path="file1.py",
            start_line=35,
            end_line=40,
            raw_source="def func_c():"
        ),
    ]


@pytest.fixture
def cyclic_ast_nodes():
    """Create AST nodes with circular dependencies."""
    return [
        ASTNode(
            id="cycle.py::func_a",
            name="func_a",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=["func_b"],
            imports=[],
            file_path="cycle.py",
            start_line=10,
            end_line=15,
            raw_source="def func_a():"
        ),
        ASTNode(
            id="cycle.py::func_b",
            name="func_b",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=["func_c"],
            imports=[],
            file_path="cycle.py",
            start_line=20,
            end_line=25,
            raw_source="def func_b():"
        ),
        ASTNode(
            id="cycle.py::func_c",
            name="func_c",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=["func_a"],  # Creates cycle
            imports=[],
            file_path="cycle.py",
            start_line=30,
            end_line=35,
            raw_source="def func_c():"
        ),
    ]


def test_build_graph_basic(sample_ast_nodes):
    """Test basic graph building."""
    builder = GraphBuilder()
    graph = builder.build_graph(sample_ast_nodes)
    
    # Verify graph type
    assert isinstance(graph, nx.DiGraph)
    
    # Verify node count
    assert graph.number_of_nodes() == 3
    
    # Verify nodes have correct attributes
    node_id = "file1.py:func_a:10"
    assert node_id in graph
    assert graph.nodes[node_id]["name"] == "func_a"
    assert graph.nodes[node_id]["node_type"] == "function"
    assert graph.nodes[node_id]["file_path"] == "file1.py"


def test_build_graph_edges(sample_ast_nodes):
    """Test edge creation."""
    builder = GraphBuilder()
    graph = builder.build_graph(sample_ast_nodes)
    
    # Verify edges exist
    assert graph.number_of_edges() > 0
    
    # Check specific edge
    source = "file1.py:func_a:10"
    target = "file1.py:func_b:25"
    assert graph.has_edge(source, target)
    
    # Verify edge type
    edge_data = graph.get_edge_data(source, target)
    assert edge_data["edge_type"] == "calls"


def test_build_graph_empty_input():
    """Test graph building with empty input."""
    builder = GraphBuilder()
    graph = builder.build_graph([])
    
    assert isinstance(graph, nx.DiGraph)
    assert graph.number_of_nodes() == 0
    assert graph.number_of_edges() == 0


def test_node_id_generation(sample_ast_nodes):
    """Test node ID format."""
    builder = GraphBuilder()
    graph = builder.build_graph(sample_ast_nodes)
    
    # Verify node ID format: {file_path}:{name}:{start_line}
    expected_id = "file1.py:func_a:10"
    assert expected_id in graph


def test_unresolved_symbols(sample_ast_nodes):
    """Test handling of unresolved symbols."""
    builder = GraphBuilder()
    graph = builder.build_graph(sample_ast_nodes)
    
    # Unresolved symbols (math, os) should not cause crashes
    # Graph should still be built successfully
    assert graph.number_of_nodes() == 3


def test_get_subgraph_depth_zero(sample_ast_nodes):
    """Test subgraph extraction with depth 0."""
    builder = GraphBuilder()
    builder.build_graph(sample_ast_nodes)
    
    root_id = "file1.py:func_a:10"
    subgraph = builder.get_subgraph(root_id, depth=0)
    
    # Depth 0 should only include root
    assert subgraph.number_of_nodes() == 1
    assert root_id in subgraph


def test_get_subgraph_depth_one(sample_ast_nodes):
    """Test subgraph extraction with depth 1."""
    builder = GraphBuilder()
    builder.build_graph(sample_ast_nodes)
    
    root_id = "file1.py:func_a:10"
    subgraph = builder.get_subgraph(root_id, depth=1)
    
    # Depth 1 should include root + direct dependencies
    assert subgraph.number_of_nodes() >= 2
    assert root_id in subgraph


def test_get_subgraph_depth_two(sample_ast_nodes):
    """Test subgraph extraction with depth 2."""
    builder = GraphBuilder()
    builder.build_graph(sample_ast_nodes)
    
    root_id = "file1.py:func_a:10"
    subgraph = builder.get_subgraph(root_id, depth=2)
    
    # Depth 2 should include more nodes
    assert subgraph.number_of_nodes() == 3  # All nodes in this case


def test_get_subgraph_invalid_root():
    """Test subgraph extraction with invalid root."""
    builder = GraphBuilder()
    builder.build_graph([])
    
    with pytest.raises(ValueError):
        builder.get_subgraph("nonexistent:node:0", depth=1)


def test_get_subgraph_negative_depth(sample_ast_nodes):
    """Test subgraph extraction with negative depth."""
    builder = GraphBuilder()
    builder.build_graph(sample_ast_nodes)
    
    with pytest.raises(ValueError):
        builder.get_subgraph("file1.py:func_a:10", depth=-1)


def test_export_json(sample_ast_nodes):
    """Test JSON export."""
    builder = GraphBuilder()
    builder.build_graph(sample_ast_nodes)
    
    json_data = builder.export_json()
    
    # Verify structure
    assert "nodes" in json_data
    assert "edges" in json_data
    assert isinstance(json_data["nodes"], list)
    assert isinstance(json_data["edges"], list)
    
    # Verify node structure
    assert len(json_data["nodes"]) == 3
    node = json_data["nodes"][0]
    assert "id" in node
    assert "name" in node
    assert "node_type" in node
    assert "file_path" in node
    
    # Verify edge structure
    if json_data["edges"]:
        edge = json_data["edges"][0]
        assert "source" in edge
        assert "target" in edge
        assert "edge_type" in edge


def test_export_json_empty_graph():
    """Test JSON export with empty graph."""
    builder = GraphBuilder()
    builder.build_graph([])
    
    json_data = builder.export_json()
    
    assert json_data["nodes"] == []
    assert json_data["edges"] == []


def test_get_node_dependencies(sample_ast_nodes):
    """Test getting node dependencies."""
    builder = GraphBuilder()
    builder.build_graph(sample_ast_nodes)
    
    node_id = "file1.py:func_a:10"
    dependencies = builder.get_node_dependencies(node_id)
    
    assert isinstance(dependencies, set)
    assert len(dependencies) >= 1


def test_get_node_dependents(sample_ast_nodes):
    """Test getting node dependents."""
    builder = GraphBuilder()
    builder.build_graph(sample_ast_nodes)
    
    node_id = "file1.py:func_c:35"
    dependents = builder.get_node_dependents(node_id)
    
    assert isinstance(dependents, set)
    # func_c is called by func_a and func_b
    assert len(dependents) >= 1


def test_get_graph_stats(sample_ast_nodes):
    """Test graph statistics."""
    builder = GraphBuilder()
    builder.build_graph(sample_ast_nodes)
    
    stats = builder.get_graph_stats()
    
    assert "node_count" in stats
    assert "edge_count" in stats
    assert "is_dag" in stats
    assert "connected_components" in stats
    assert "density" in stats
    
    assert stats["node_count"] == 3
    assert stats["edge_count"] > 0


def test_cycle_detection(cyclic_ast_nodes):
    """Test cycle detection."""
    builder = GraphBuilder()
    graph = builder.build_graph(cyclic_ast_nodes)
    
    # Graph should be built successfully even with cycles
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 3
    
    # Verify it's not a DAG
    stats = builder.get_graph_stats()
    assert stats["is_dag"] is False


def test_symbol_resolution_same_file(sample_ast_nodes):
    """Test symbol resolution within same file."""
    builder = GraphBuilder()
    graph = builder.build_graph(sample_ast_nodes)
    
    # func_a calls func_b (same file)
    source = "file1.py:func_a:10"
    target = "file1.py:func_b:25"
    
    assert graph.has_edge(source, target)


def test_multiple_files():
    """Test graph building with multiple files."""
    nodes = [
        ASTNode(
            id="file1.py::func1",
            name="func1",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=["func2"],
            imports=[],
            file_path="file1.py",
            start_line=10,
            end_line=15,
            raw_source="def func1():"
        ),
        ASTNode(
            id="file2.py::func2",
            name="func2",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=[],
            imports=[],
            file_path="file2.py",
            start_line=10,
            end_line=15,
            raw_source="def func2():"
        ),
    ]
    
    builder = GraphBuilder()
    graph = builder.build_graph(nodes)
    
    # Verify cross-file edge
    assert graph.number_of_nodes() == 2
    assert graph.has_edge("file1.py:func1:10", "file2.py:func2:10")


def test_edge_types():
    """Test different edge types (calls vs imports)."""
    nodes = [
        ASTNode(
            id="main.py::main",
            name="main",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=["helper"],
            imports=["utils"],
            file_path="main.py",
            start_line=10,
            end_line=15,
            raw_source="def main():"
        ),
        ASTNode(
            id="main.py::helper",
            name="helper",
            node_type="function",
            parameters=[],
            return_type="None",
            called_symbols=[],
            imports=[],
            file_path="main.py",
            start_line=20,
            end_line=25,
            raw_source="def helper():"
        ),
        ASTNode(
            id="utils.py::utils",
            name="utils",
            node_type="module",
            parameters=[],
            return_type=None,
            called_symbols=[],
            imports=[],
            file_path="utils.py",
            start_line=1,
            end_line=10,
            raw_source="# utils module"
        ),
    ]
    
    builder = GraphBuilder()
    graph = builder.build_graph(nodes)
    
    # Check calls edge
    calls_edge = graph.get_edge_data("main.py:main:10", "main.py:helper:20")
    assert calls_edge["edge_type"] == "calls"
    
    # Check imports edge
    imports_edge = graph.get_edge_data("main.py:main:10", "utils.py:utils:1")
    assert imports_edge["edge_type"] == "imports"


def test_large_graph_performance():
    """Test performance with large number of nodes."""
    # Create 1000 nodes
    nodes = []
    for i in range(1000):
        nodes.append(
            ASTNode(
                id=f"file{i}.py::func{i}",
                name=f"func{i}",
                node_type="function",
                parameters=[],
                return_type="None",
                called_symbols=[f"func{i+1}"] if i < 999 else [],
                imports=[],
                file_path=f"file{i}.py",
                start_line=10,
                end_line=15,
                raw_source=f"def func{i}():"
            )
        )
    
    builder = GraphBuilder()
    graph = builder.build_graph(nodes)
    
    # Verify all nodes added
    assert graph.number_of_nodes() == 1000
    
    # Performance should be acceptable (O(n))
    assert graph.number_of_edges() > 0
