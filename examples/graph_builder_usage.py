"""Example usage of the Dependency Graph Builder."""
import json
from app.parsers.base import ASTNode
from app.dependency_graph import GraphBuilder


def create_sample_ast_nodes():
    """Create sample AST nodes for demonstration."""
    nodes = [
        # Main calculator class
        ASTNode(
            id="Calculator.java::Calculator",
            name="Calculator",
            node_type="class",
            parameters=[],
            return_type=None,
            called_symbols=[],
            imports=["Math", "Logger"],
            file_path="Calculator.java",
            start_line=5,
            end_line=50,
            raw_source="public class Calculator"
        ),
        
        # Add method
        ASTNode(
            id="Calculator.java::add",
            name="add",
            node_type="method",
            parameters=["int a", "int b"],
            return_type="int",
            called_symbols=["validate", "log"],
            imports=[],
            file_path="Calculator.java",
            start_line=10,
            end_line=15,
            raw_source="public int add(int a, int b)"
        ),
        
        # Validate method
        ASTNode(
            id="Calculator.java::validate",
            name="validate",
            node_type="method",
            parameters=["int value"],
            return_type="boolean",
            called_symbols=[],
            imports=[],
            file_path="Calculator.java",
            start_line=20,
            end_line=25,
            raw_source="private boolean validate(int value)"
        ),
        
        # Logger utility
        ASTNode(
            id="Logger.java::Logger",
            name="Logger",
            node_type="class",
            parameters=[],
            return_type=None,
            called_symbols=[],
            imports=[],
            file_path="Logger.java",
            start_line=5,
            end_line=30,
            raw_source="public class Logger"
        ),
        
        # Log method
        ASTNode(
            id="Logger.java::log",
            name="log",
            node_type="method",
            parameters=["String message"],
            return_type="void",
            called_symbols=["format"],
            imports=[],
            file_path="Logger.java",
            start_line=10,
            end_line=15,
            raw_source="public void log(String message)"
        ),
        
        # Format method
        ASTNode(
            id="Logger.java::format",
            name="format",
            node_type="method",
            parameters=["String text"],
            return_type="String",
            called_symbols=[],
            imports=[],
            file_path="Logger.java",
            start_line=20,
            end_line=25,
            raw_source="private String format(String text)"
        ),
        
        # Math utility (external - won't be resolved)
        ASTNode(
            id="Utils.java::Math",
            name="Math",
            node_type="class",
            parameters=[],
            return_type=None,
            called_symbols=[],
            imports=[],
            file_path="Utils.java",
            start_line=5,
            end_line=20,
            raw_source="public class Math"
        ),
    ]
    
    return nodes


def demonstrate_basic_graph_building():
    """Demonstrate basic graph building."""
    print("=== Basic Graph Building ===\n")
    
    # Create sample AST nodes
    ast_nodes = create_sample_ast_nodes()
    print(f"Created {len(ast_nodes)} sample AST nodes")
    
    # Build graph
    builder = GraphBuilder()
    graph = builder.build_graph(ast_nodes)
    
    print(f"\nGraph Statistics:")
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")
    
    # Display nodes
    print(f"\nNodes in graph:")
    for node_id in list(graph.nodes())[:5]:
        node_data = graph.nodes[node_id]
        print(f"  - {node_id}")
        print(f"    Type: {node_data['node_type']}, File: {node_data['file_path']}")
    
    # Display edges
    print(f"\nEdges in graph:")
    for source, target, edge_data in list(graph.edges(data=True))[:5]:
        print(f"  - {source} --[{edge_data['edge_type']}]--> {target}")


def demonstrate_subgraph_extraction():
    """Demonstrate subgraph extraction with different depths."""
    print("\n\n=== Subgraph Extraction ===\n")
    
    ast_nodes = create_sample_ast_nodes()
    builder = GraphBuilder()
    builder.build_graph(ast_nodes)
    
    # Find the 'add' method node ID
    add_node_id = "Calculator.java:add:10"
    
    print(f"Root node: {add_node_id}\n")
    
    # Extract subgraphs at different depths
    for depth in [0, 1, 2]:
        subgraph = builder.get_subgraph(add_node_id, depth)
        print(f"Depth {depth}:")
        print(f"  Nodes: {subgraph.number_of_nodes()}")
        print(f"  Edges: {subgraph.number_of_edges()}")
        print(f"  Node IDs: {list(subgraph.nodes())}")
        print()


def demonstrate_json_export():
    """Demonstrate JSON export functionality."""
    print("\n\n=== JSON Export ===\n")
    
    ast_nodes = create_sample_ast_nodes()
    builder = GraphBuilder()
    builder.build_graph(ast_nodes)
    
    # Export to JSON
    json_data = builder.export_json()
    
    print(f"Exported {len(json_data['nodes'])} nodes and {len(json_data['edges'])} edges")
    print(f"\nSample node:")
    print(json.dumps(json_data['nodes'][0], indent=2))
    
    print(f"\nSample edge:")
    if json_data['edges']:
        print(json.dumps(json_data['edges'][0], indent=2))
    
    # Verify JSON serialization
    json_str = json.dumps(json_data, indent=2)
    print(f"\nJSON serialization successful: {len(json_str)} characters")


def demonstrate_dependency_queries():
    """Demonstrate dependency and dependent queries."""
    print("\n\n=== Dependency Queries ===\n")
    
    ast_nodes = create_sample_ast_nodes()
    builder = GraphBuilder()
    builder.build_graph(ast_nodes)
    
    # Query dependencies
    add_node_id = "Calculator.java:add:10"
    
    dependencies = builder.get_node_dependencies(add_node_id)
    print(f"Dependencies of {add_node_id}:")
    for dep in dependencies:
        print(f"  - {dep}")
    
    # Query dependents
    log_node_id = "Logger.java:log:10"
    dependents = builder.get_node_dependents(log_node_id)
    print(f"\nDependents of {log_node_id}:")
    for dep in dependents:
        print(f"  - {dep}")


def demonstrate_graph_stats():
    """Demonstrate graph statistics."""
    print("\n\n=== Graph Statistics ===\n")
    
    ast_nodes = create_sample_ast_nodes()
    builder = GraphBuilder()
    builder.build_graph(ast_nodes)
    
    stats = builder.get_graph_stats()
    
    print("Graph Metrics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def demonstrate_empty_input():
    """Demonstrate safe handling of empty input."""
    print("\n\n=== Empty Input Handling ===\n")
    
    builder = GraphBuilder()
    graph = builder.build_graph([])
    
    print(f"Graph with empty input:")
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")
    print(f"  Safe: ✓")


def demonstrate_cycle_detection():
    """Demonstrate cycle detection."""
    print("\n\n=== Cycle Detection ===\n")
    
    # Create nodes with circular dependencies
    cyclic_nodes = [
        ASTNode(
            id="A.java::funcA",
            name="funcA",
            node_type="function",
            parameters=[],
            return_type="void",
            called_symbols=["funcB"],
            imports=[],
            file_path="A.java",
            start_line=10,
            end_line=15,
            raw_source="void funcA()"
        ),
        ASTNode(
            id="B.java::funcB",
            name="funcB",
            node_type="function",
            parameters=[],
            return_type="void",
            called_symbols=["funcC"],
            imports=[],
            file_path="B.java",
            start_line=10,
            end_line=15,
            raw_source="void funcB()"
        ),
        ASTNode(
            id="C.java::funcC",
            name="funcC",
            node_type="function",
            parameters=[],
            return_type="void",
            called_symbols=["funcA"],  # Creates cycle: A -> B -> C -> A
            imports=[],
            file_path="C.java",
            start_line=10,
            end_line=15,
            raw_source="void funcC()"
        ),
    ]
    
    builder = GraphBuilder()
    graph = builder.build_graph(cyclic_nodes)
    
    stats = builder.get_graph_stats()
    print(f"Graph has cycles: {not stats['is_dag']}")
    print(f"Check logs for cycle details")


if __name__ == "__main__":
    demonstrate_basic_graph_building()
    demonstrate_subgraph_extraction()
    demonstrate_json_export()
    demonstrate_dependency_queries()
    demonstrate_graph_stats()
    demonstrate_empty_input()
    demonstrate_cycle_detection()
    
    print("\n\n=== All Demonstrations Complete ===")
