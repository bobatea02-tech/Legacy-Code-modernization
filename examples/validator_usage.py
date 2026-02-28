"""Example usage of ValidationEngine for code validation.

This demonstrates how to use the deterministic validation engine
to validate translated code without LLM usage.
"""

import networkx as nx
from app.parsers.base import ASTNode
from app.validation import ValidationEngine, ValidationReport


def example_basic_validation():
    """Example: Basic validation without dependency graph."""
    
    # Create a sample original AST node
    original_node = ASTNode(
        id="sample_001",
        name="calculate_total",
        node_type="function",
        parameters=["price", "quantity", "tax_rate"],
        return_type="float",
        called_symbols=["round", "multiply"],
        imports=["math"],
        file_path="sample.java",
        start_line=10,
        end_line=20,
        raw_source="""
        public float calculateTotal(float price, int quantity, float taxRate) {
            float subtotal = multiply(price, quantity);
            float tax = subtotal * taxRate;
            return round(subtotal + tax);
        }
        """
    )
    
    # Sample translated Python code
    translated_code = """
def calculate_total(price: float, quantity: int, tax_rate: float) -> float:
    \"\"\"Calculate total with tax.\"\"\"
    subtotal = multiply(price, quantity)
    tax = subtotal * tax_rate
    return round(subtotal + tax, 2)
"""
    
    # Initialize validation engine
    validator = ValidationEngine()
    
    # Validate translation
    report: ValidationReport = validator.validate_translation(
        original_node=original_node,
        translated_code=translated_code,
        dependency_graph=None
    )
    
    # Print results
    print("=== Validation Report ===")
    print(f"Syntax Valid: {report.syntax_valid}")
    print(f"Structure Valid: {report.structure_valid}")
    print(f"Symbols Preserved: {report.symbols_preserved}")
    print(f"Dependencies Complete: {report.dependencies_complete}")
    print(f"Missing Dependencies: {report.missing_dependencies}")
    print(f"\nErrors: {report.errors if report.errors else 'None'}")
    print(f"\n=== Generated Test Stub ===")
    print(report.unit_test_stub)


def example_validation_with_graph():
    """Example: Validation with dependency graph."""
    
    # Create original node
    original_node = ASTNode(
        id="sample_002",
        name="process_order",
        node_type="function",
        parameters=["order_id"],
        return_type="bool",
        called_symbols=["validate_order", "calculate_total", "save_order"],
        imports=[],
        file_path="order_service.java",
        start_line=50,
        end_line=65,
        raw_source="""
        public boolean processOrder(String orderId) {
            if (validateOrder(orderId)) {
                float total = calculateTotal(orderId);
                return saveOrder(orderId, total);
            }
            return false;
        }
        """
    )
    
    # Create dependency graph
    graph = nx.DiGraph()
    
    # Add nodes
    graph.add_node(
        "order_service.java:process_order:50",
        name="process_order",
        node_type="function",
        file_path="order_service.java",
        start_line=50,
        end_line=65
    )
    graph.add_node(
        "order_service.java:validate_order:10",
        name="validate_order",
        node_type="function",
        file_path="order_service.java",
        start_line=10,
        end_line=20
    )
    graph.add_node(
        "order_service.java:calculate_total:25",
        name="calculate_total",
        node_type="function",
        file_path="order_service.java",
        start_line=25,
        end_line=35
    )
    
    # Add edges
    graph.add_edge(
        "order_service.java:process_order:50",
        "order_service.java:validate_order:10",
        edge_type="calls"
    )
    graph.add_edge(
        "order_service.java:process_order:50",
        "order_service.java:calculate_total:25",
        edge_type="calls"
    )
    
    # Translated code (missing save_order)
    translated_code = """
def process_order(order_id: str) -> bool:
    \"\"\"Process an order.\"\"\"
    if validate_order(order_id):
        total = calculate_total(order_id)
        # save_order is missing - should be caught by validation
        return True
    return False
"""
    
    # Validate
    validator = ValidationEngine()
    report = validator.validate_translation(
        original_node=original_node,
        translated_code=translated_code,
        dependency_graph=graph
    )
    
    # Print results
    print("\n=== Validation with Dependency Graph ===")
    print(f"Syntax Valid: {report.syntax_valid}")
    print(f"Structure Valid: {report.structure_valid}")
    print(f"Symbols Preserved: {report.symbols_preserved}")
    print(f"Dependencies Complete: {report.dependencies_complete}")
    print(f"Missing Dependencies: {report.missing_dependencies}")
    print(f"\nErrors:")
    for error in report.errors:
        print(f"  - {error}")


def example_invalid_syntax():
    """Example: Validation with syntax errors."""
    
    original_node = ASTNode(
        id="sample_003",
        name="bad_function",
        node_type="function",
        parameters=["x"],
        return_type="int",
        called_symbols=[],
        imports=[],
        file_path="test.java",
        start_line=1,
        end_line=5,
        raw_source="public int badFunction(int x) { return x * 2; }"
    )
    
    # Invalid Python syntax
    invalid_code = """
def bad_function(x: int) -> int:
    return x * 2
    # Missing closing quote
    message = "incomplete string
"""
    
    validator = ValidationEngine()
    report = validator.validate_translation(
        original_node=original_node,
        translated_code=invalid_code,
        dependency_graph=None
    )
    
    print("\n=== Validation with Syntax Error ===")
    print(f"Syntax Valid: {report.syntax_valid}")
    print(f"Errors: {report.errors}")


if __name__ == "__main__":
    print("ValidationEngine Examples\n")
    
    # Run examples
    example_basic_validation()
    example_validation_with_graph()
    example_invalid_syntax()
    
    print("\n✓ All examples completed")
