"""Example usage of the AST parsing interface."""
import json
from app.parsers import JavaParser, CobolParser, ASTNode


def demonstrate_java_parser():
    """Demonstrate Java parser usage."""
    print("=== Java Parser Demo ===")
    parser = JavaParser()
    print(f"Language: {parser.supports_language()}")
    
    # Create a sample Java file for testing
    sample_java = """
import java.util.List;
import java.io.File;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    private String formatResult(int result) {
        return String.valueOf(result);
    }
}
"""
    
    # Write sample file
    with open('temp_sample.java', 'w') as f:
        f.write(sample_java)
    
    # Parse the file
    nodes = parser.parse_file('temp_sample.java')
    print(f"Found {len(nodes)} AST nodes")
    
    # Display nodes
    for node in nodes:
        print(f"\nNode: {node.name}")
        print(f"  Type: {node.node_type}")
        print(f"  Line: {node.start_line}")
        print(f"  Imports: {node.imports}")
        print(f"  JSON: {json.dumps(node.to_dict(), indent=2)}")
    
    # Extract dependencies
    deps = parser.extract_dependencies(nodes)
    print(f"\nDependencies: {deps}")
    
    # Cleanup
    import os
    os.remove('temp_sample.java')


def demonstrate_cobol_parser():
    """Demonstrate COBOL parser usage."""
    print("\n\n=== COBOL Parser Demo ===")
    parser = CobolParser()
    print(f"Language: {parser.supports_language()}")
    
    # Create a sample COBOL file for testing
    sample_cobol = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYROLL.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC SECTION.
       START-PARA.
           CALL 'CALCPAY'
           CALL 'PRINTPAY'
           STOP RUN.
       
       CALC-SECTION SECTION.
       CALCULATE-PAY.
           COMPUTE GROSS-PAY = HOURS * RATE.
"""
    
    # Write sample file
    with open('temp_sample.cbl', 'w') as f:
        f.write(sample_cobol)
    
    # Parse the file
    nodes = parser.parse_file('temp_sample.cbl')
    print(f"Found {len(nodes)} AST nodes")
    
    # Display nodes
    for node in nodes:
        print(f"\nNode: {node.name}")
        print(f"  Type: {node.node_type}")
        print(f"  Line: {node.start_line}")
        print(f"  Called: {node.called_symbols}")
    
    # Extract dependencies
    deps = parser.extract_dependencies(nodes)
    print(f"\nDependencies: {deps}")
    
    # Cleanup
    import os
    os.remove('temp_sample.cbl')


def demonstrate_ast_node_serialization():
    """Demonstrate ASTNode JSON serialization."""
    print("\n\n=== ASTNode Serialization Demo ===")
    
    node = ASTNode(
        id="example.py::my_function",
        name="my_function",
        node_type="function",
        parameters=["arg1: str", "arg2: int"],
        return_type="bool",
        called_symbols=["helper_func", "validate"],
        imports=["os", "sys"],
        file_path="example.py",
        start_line=10,
        end_line=25,
        raw_source="def my_function(arg1: str, arg2: int) -> bool:"
    )
    
    # Convert to JSON
    json_data = json.dumps(node.to_dict(), indent=2)
    print("JSON representation:")
    print(json_data)
    
    # Demonstrate it's JSON-serializable
    parsed = json.loads(json_data)
    print(f"\nParsed back - Node name: {parsed['name']}, Type: {parsed['node_type']}")


if __name__ == "__main__":
    demonstrate_java_parser()
    demonstrate_cobol_parser()
    demonstrate_ast_node_serialization()
