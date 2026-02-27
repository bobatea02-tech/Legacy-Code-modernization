"""Example usage of the Context Optimization Engine."""

from app.parsers import JavaParser
from app.dependency_graph import GraphBuilder
from app.context_optimizer import ContextOptimizer
from pathlib import Path


def demonstrate_basic_optimization():
    """Demonstrate basic context optimization."""
    print("=== Basic Context Optimization ===\n")
    
    # Step 1: Create sample Java file
    sample_java = """
import java.util.List;

public class Calculator {
    public int add(int a, int b) {
        return validate(a) + validate(b);
    }
    
    public int multiply(int a, int b) {
        return validate(a) * validate(b);
    }
    
    private int validate(int value) {
        if (value < 0) {
            throw new IllegalArgumentException("Negative value");
        }
        return value;
    }
    
    public int subtract(int a, int b) {
        return validate(a) - validate(b);
    }
}
"""
    
    sample_file = Path("temp_calc.java")
    sample_file.write_text(sample_java)
    
    try:
        # Step 2: Parse file
        print("Step 1: Parsing Java file...")
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(sample_file))
        print(f"  Parsed {len(ast_nodes)} AST nodes\n")
        
        # Step 3: Build dependency graph
        print("Step 2: Building dependency graph...")
        builder = GraphBuilder()
        graph = builder.build_graph(ast_nodes)
        print(f"  Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges\n")
        
        # Step 4: Create AST index
        ast_index = {builder._generate_node_id(node): node for node in ast_nodes}
        
        # Step 5: Optimize context for 'add' method
        print("Step 3: Optimizing context for 'add' method...")
        optimizer = ContextOptimizer(max_tokens=500, expansion_depth=2)
        
        # Find the 'add' method node ID
        add_node_id = None
        for node_id in graph.nodes():
            if "add:" in node_id and "add" in node_id:
                add_node_id = node_id
                break
        
        if add_node_id:
            result = optimizer.optimize_context(
                target_node_id=add_node_id,
                dependency_graph=graph,
                ast_index=ast_index
            )
            
            print(f"  Target: {result.target_node_id}")
            print(f"  Included nodes: {len(result.included_nodes)}")
            print(f"  Excluded nodes: {len(result.excluded_nodes)}")
            print(f"  Estimated tokens: {result.estimated_tokens}")
            print(f"\n  Included:")
            for node_id in result.included_nodes:
                print(f"    - {node_id}")
            
            if result.excluded_nodes:
                print(f"\n  Excluded:")
                for node_id in result.excluded_nodes:
                    print(f"    - {node_id}")
            
            print(f"\n  Combined source ({len(result.combined_source)} chars):")
            print("  " + "-" * 60)
            print("  " + result.combined_source[:200] + "...")
            print("  " + "-" * 60)
        
        print("\n=== Basic Optimization Complete ===")
        
    finally:
        if sample_file.exists():
            sample_file.unlink()


def demonstrate_depth_comparison():
    """Demonstrate optimization with different depths."""
    print("\n\n=== Depth Comparison ===\n")
    
    # Create sample with deeper dependencies
    sample_java = """
public class Chain {
    public void level1() {
        level2();
    }
    
    private void level2() {
        level3();
    }
    
    private void level3() {
        level4();
    }
    
    private void level4() {
        System.out.println("Deep");
    }
}
"""
    
    sample_file = Path("temp_chain.java")
    sample_file.write_text(sample_java)
    
    try:
        # Parse and build graph
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(sample_file))
        
        builder = GraphBuilder()
        graph = builder.build_graph(ast_nodes)
        
        ast_index = {builder._generate_node_id(node): node for node in ast_nodes}
        
        # Find level1 method
        level1_id = None
        for node_id in graph.nodes():
            if "level1:" in node_id:
                level1_id = node_id
                break
        
        if level1_id:
            print(f"Target: {level1_id}\n")
            
            # Test different depths
            for depth in [0, 1, 2, 3]:
                optimizer = ContextOptimizer(max_tokens=10000, expansion_depth=depth)
                
                result = optimizer.optimize_context(
                    target_node_id=level1_id,
                    dependency_graph=graph,
                    ast_index=ast_index,
                    expansion_depth=depth
                )
                
                print(f"Depth {depth}:")
                print(f"  Included: {len(result.included_nodes)} nodes")
                print(f"  Tokens: {result.estimated_tokens}")
                print(f"  Nodes: {result.included_nodes}")
                print()
        
        print("=== Depth Comparison Complete ===")
        
    finally:
        if sample_file.exists():
            sample_file.unlink()


def demonstrate_token_limit():
    """Demonstrate token limit enforcement."""
    print("\n\n=== Token Limit Enforcement ===\n")
    
    sample_java = """
public class Large {
    public void method1() {
        method2();
        method3();
        method4();
    }
    
    private void method2() {
        System.out.println("Method 2 with some content");
    }
    
    private void method3() {
        System.out.println("Method 3 with some content");
    }
    
    private void method4() {
        System.out.println("Method 4 with some content");
    }
}
"""
    
    sample_file = Path("temp_large.java")
    sample_file.write_text(sample_java)
    
    try:
        # Parse and build graph
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(sample_file))
        
        builder = GraphBuilder()
        graph = builder.build_graph(ast_nodes)
        
        ast_index = {builder._generate_node_id(node): node for node in ast_nodes}
        
        # Find method1
        method1_id = None
        for node_id in graph.nodes():
            if "method1:" in node_id:
                method1_id = node_id
                break
        
        if method1_id:
            print(f"Target: {method1_id}\n")
            
            # Test different token limits
            for max_tokens in [50, 100, 200, 500]:
                optimizer = ContextOptimizer(max_tokens=max_tokens, expansion_depth=2)
                
                result = optimizer.optimize_context(
                    target_node_id=method1_id,
                    dependency_graph=graph,
                    ast_index=ast_index,
                    max_tokens=max_tokens
                )
                
                print(f"Token limit {max_tokens}:")
                print(f"  Included: {len(result.included_nodes)} nodes")
                print(f"  Excluded: {len(result.excluded_nodes)} nodes")
                print(f"  Actual tokens: {result.estimated_tokens}")
                print()
        
        print("=== Token Limit Enforcement Complete ===")
        
    finally:
        if sample_file.exists():
            sample_file.unlink()


def demonstrate_comment_removal():
    """Demonstrate comment removal."""
    print("\n\n=== Comment Removal ===\n")
    
    optimizer = ContextOptimizer()
    
    # Test Java comments
    java_code = """
public class Test {
    // This is a single-line comment
    public void method() {
        int x = 5;  // Inline comment
        return x;
    }
}
"""
    
    print("Original Java code:")
    print(java_code)
    
    cleaned = optimizer.remove_comments(java_code)
    print("\nCleaned Java code:")
    print(cleaned)
    
    # Test Python comments
    python_code = """
def test():
    # This is a comment
    x = 5  # Inline comment
    return x
"""
    
    print("\n\nOriginal Python code:")
    print(python_code)
    
    cleaned = optimizer.remove_comments(python_code)
    print("\nCleaned Python code:")
    print(cleaned)
    
    print("\n=== Comment Removal Complete ===")


def demonstrate_token_estimation():
    """Demonstrate token estimation."""
    print("\n\n=== Token Estimation ===\n")
    
    optimizer = ContextOptimizer()
    
    samples = [
        "hello",
        "hello world",
        "def func():\n    return 42",
        "public class Calculator {\n    public int add(int a, int b) {\n        return a + b;\n    }\n}",
    ]
    
    print("Token estimates:")
    for sample in samples:
        tokens = optimizer.estimate_tokens(sample)
        print(f"  {len(sample):3d} chars -> {tokens:3d} tokens: {sample[:40]}...")
    
    print("\n=== Token Estimation Complete ===")


if __name__ == "__main__":
    demonstrate_basic_optimization()
    demonstrate_depth_comparison()
    demonstrate_token_limit()
    demonstrate_comment_removal()
    demonstrate_token_estimation()
    
    print("\n\n=== All Demonstrations Complete ===")
