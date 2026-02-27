"""Integration example: AST Parsing to Dependency Graph.

Demonstrates the full pipeline from parsing source files to building
a dependency graph suitable for context optimization.
"""

import json
from pathlib import Path
from app.parsers import JavaParser
from app.dependency_graph import GraphBuilder


def demonstrate_integration():
    """Demonstrate full pipeline integration."""
    print("=== Parser to Graph Integration ===\n")
    
    # Step 1: Create sample Java file
    sample_java = """
import java.util.List;
import java.io.File;

public class Calculator {
    private Logger logger;
    
    public Calculator() {
        this.logger = new Logger();
    }
    
    public int add(int a, int b) {
        logger.log("Adding numbers");
        return validate(a) + validate(b);
    }
    
    public int multiply(int a, int b) {
        logger.log("Multiplying numbers");
        return validate(a) * validate(b);
    }
    
    private int validate(int value) {
        if (value < 0) {
            throw new IllegalArgumentException("Negative value");
        }
        return value;
    }
}
"""
    
    # Write sample file
    sample_file = Path("temp_calculator.java")
    sample_file.write_text(sample_java)
    
    try:
        # Step 2: Parse Java file
        print("Step 1: Parsing Java file...")
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(sample_file))
        print(f"  [OK] Parsed {len(ast_nodes)} AST nodes\n")
        
        # Display parsed nodes
        print("Parsed AST Nodes:")
        for node in ast_nodes:
            print(f"  - {node.name} ({node.node_type}) at line {node.start_line}")
        print()
        
        # Step 3: Build dependency graph
        print("Step 2: Building dependency graph...")
        builder = GraphBuilder()
        graph = builder.build_graph(ast_nodes)
        print(f"  [OK] Built graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges\n")
        
        # Step 4: Analyze graph structure
        print("Step 3: Analyzing graph structure...")
        stats = builder.get_graph_stats()
        print(f"  Node count: {stats['node_count']}")
        print(f"  Edge count: {stats['edge_count']}")
        print(f"  Is DAG: {stats['is_dag']}")
        print(f"  Connected components: {stats['connected_components']}")
        print(f"  Density: {stats['density']:.4f}\n")
        
        # Step 5: Extract subgraph for specific method
        print("Step 4: Extracting subgraph for 'add' method...")
        add_node_id = None
        for node_id in graph.nodes():
            if "add" in node_id and "add:" in node_id:
                add_node_id = node_id
                break
        
        if add_node_id:
            print(f"  Root: {add_node_id}")
            
            for depth in [0, 1, 2]:
                subgraph = builder.get_subgraph(add_node_id, depth)
                print(f"  Depth {depth}: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")
            print()
        
        # Step 6: Query dependencies
        print("Step 5: Querying dependencies...")
        if add_node_id:
            deps = builder.get_node_dependencies(add_node_id)
            print(f"  '{add_node_id}' depends on:")
            for dep in deps:
                print(f"    -> {dep}")
            print()
        
        # Step 7: Export to JSON
        print("Step 6: Exporting to JSON...")
        json_data = builder.export_json()
        
        output_file = Path("graph_output.json")
        output_file.write_text(json.dumps(json_data, indent=2))
        print(f"  [OK] Exported to {output_file}")
        print(f"  Size: {output_file.stat().st_size} bytes\n")
        
        # Step 8: Demonstrate context optimization use case
        print("Step 7: Context optimization use case...")
        print("  Scenario: Translating 'add' method with relevant context")
        
        if add_node_id:
            # Get subgraph with depth 1 (method + direct dependencies)
            context_subgraph = builder.get_subgraph(add_node_id, depth=1)
            context_nodes = list(context_subgraph.nodes())
            
            print(f"  Context includes {len(context_nodes)} nodes:")
            for node_id in context_nodes:
                node_data = graph.nodes[node_id]
                print(f"    - {node_data['name']} ({node_data['node_type']})")
            
            print(f"\n  This context can be passed to LLM for translation")
            print(f"  Token budget: ~{len(context_nodes) * 100} tokens (estimated)\n")
        
        print("=== Integration Complete ===")
        
    finally:
        # Cleanup
        if sample_file.exists():
            sample_file.unlink()
        
        output_file = Path("graph_output.json")
        if output_file.exists():
            output_file.unlink()


def demonstrate_multi_file_integration():
    """Demonstrate integration with multiple files."""
    print("\n\n=== Multi-File Integration ===\n")
    
    # Create multiple Java files
    files = {
        "Main.java": """
public class Main {
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        int result = calc.add(5, 3);
        Logger.log(result);
    }
}
""",
        "Calculator.java": """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int subtract(int a, int b) {
        return a - b;
    }
}
""",
        "Logger.java": """
public class Logger {
    public static void log(Object message) {
        System.out.println(message);
    }
}
"""
    }
    
    # Write files
    file_paths = []
    for filename, content in files.items():
        path = Path(filename)
        path.write_text(content)
        file_paths.append(path)
    
    try:
        # Parse all files
        print("Parsing multiple files...")
        parser = JavaParser()
        all_ast_nodes = []
        
        for file_path in file_paths:
            nodes = parser.parse_file(str(file_path))
            all_ast_nodes.extend(nodes)
            print(f"  {file_path.name}: {len(nodes)} nodes")
        
        print(f"\nTotal AST nodes: {len(all_ast_nodes)}\n")
        
        # Build unified graph
        print("Building unified dependency graph...")
        builder = GraphBuilder()
        graph = builder.build_graph(all_ast_nodes)
        
        print(f"  Nodes: {graph.number_of_nodes()}")
        print(f"  Edges: {graph.number_of_edges()}")
        
        # Show cross-file dependencies
        print("\nCross-file dependencies:")
        for source, target, edge_data in graph.edges(data=True):
            source_file = graph.nodes[source]['file_path']
            target_file = graph.nodes[target]['file_path']
            
            if source_file != target_file:
                print(f"  {source_file} -> {target_file}")
                print(f"    {source} --[{edge_data['edge_type']}]--> {target}")
        
        print("\n=== Multi-File Integration Complete ===")
        
    finally:
        # Cleanup
        for path in file_paths:
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    demonstrate_integration()
    demonstrate_multi_file_integration()
