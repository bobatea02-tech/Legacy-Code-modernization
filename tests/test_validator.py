"""Tests for ValidationEngine."""

import pytest
import networkx as nx
from app.parsers.base import ASTNode
from app.validation import ValidationEngine, ValidationReport


@pytest.fixture
def validator():
    """Create ValidationEngine instance."""
    return ValidationEngine()


@pytest.fixture
def sample_node():
    """Create sample AST node for testing."""
    return ASTNode(
        id="test_001",
        name="calculate_sum",
        node_type="function",
        parameters=["a", "b"],
        return_type="int",
        called_symbols=["add", "validate"],
        imports=["math"],
        file_path="test.java",
        start_line=10,
        end_line=15,
        raw_source="public int calculateSum(int a, int b) { return add(a, b); }"
    )


def test_valid_translation(validator, sample_node):
    """Test validation of correct translation."""
    translated_code = """
def calculate_sum(a: int, b: int) -> int:
    validate(a)
    validate(b)
    return add(a, b)
"""
    
    report = validator.validate_translation(sample_node, translated_code)
    
    assert report.syntax_valid is True
    assert report.structure_valid is True
    assert report.symbols_preserved is True
    assert len(report.errors) == 0


def test_syntax_error(validator, sample_node):
    """Test detection of syntax errors."""
    invalid_code = """
def calculate_sum(a: int, b: int) -> int:
    return add(a, b
"""  # Missing closing parenthesis
    
    report = validator.validate_translation(sample_node, invalid_code)
    
    assert report.syntax_valid is False
    assert len(report.errors) > 0
    assert any("Syntax error" in error for error in report.errors)


def test_missing_function_name(validator, sample_node):
    """Test detection of missing function name."""
    code_without_name = """
def different_name(a: int, b: int) -> int:
    return add(a, b)
"""
    
    report = validator.validate_translation(sample_node, code_without_name)
    
    assert report.structure_valid is False
    assert any("not found" in error for error in report.errors)


def test_parameter_count_mismatch(validator, sample_node):
    """Test detection of parameter count mismatch."""
    code_wrong_params = """
def calculate_sum(a: int) -> int:
    return add(a, 0)
"""
    
    report = validator.validate_translation(sample_node, code_wrong_params)
    
    assert report.structure_valid is False
    assert any("Parameter count mismatch" in error for error in report.errors)


def test_missing_symbols(validator, sample_node):
    """Test detection of missing called symbols."""
    code_missing_symbols = """
def calculate_sum(a: int, b: int) -> int:
    # Missing 'add' and 'validate' calls
    return a + b
"""
    
    report = validator.validate_translation(sample_node, code_missing_symbols)
    
    assert report.symbols_preserved is False
    assert any("Missing called symbols" in error for error in report.errors)


def test_incomplete_translation_todo(validator, sample_node):
    """Test detection of TODO markers."""
    incomplete_code = """
def calculate_sum(a: int, b: int) -> int:
    # TODO: Implement validation
    return add(a, b)
"""
    
    report = validator.validate_translation(sample_node, incomplete_code)
    
    assert any("Incomplete translation" in error for error in report.errors)


def test_incomplete_translation_pass(validator, sample_node):
    """Test detection of pass statements."""
    incomplete_code = """
def calculate_sum(a: int, b: int) -> int:
    pass
"""
    
    report = validator.validate_translation(sample_node, incomplete_code)
    
    assert any("Incomplete translation" in error for error in report.errors)


def test_incomplete_translation_not_implemented(validator, sample_node):
    """Test detection of NotImplemented."""
    incomplete_code = """
def calculate_sum(a: int, b: int) -> int:
    raise NotImplementedError()
"""
    
    report = validator.validate_translation(sample_node, incomplete_code)
    
    assert any("Incomplete translation" in error for error in report.errors)


def test_dependency_graph_validation(validator):
    """Test validation with dependency graph."""
    node = ASTNode(
        id="test_002",
        name="process_data",
        node_type="function",
        parameters=["data"],
        return_type="bool",
        called_symbols=["validate_data", "transform_data"],
        imports=[],
        file_path="processor.java",
        start_line=20,
        end_line=30,
        raw_source="public boolean processData(String data) { return true; }"
    )
    
    # Create dependency graph
    graph = nx.DiGraph()
    graph.add_node(
        "processor.java:process_data:20",
        name="process_data",
        node_type="function",
        file_path="processor.java",
        start_line=20,
        end_line=30
    )
    graph.add_node(
        "processor.java:validate_data:5",
        name="validate_data",
        node_type="function",
        file_path="processor.java",
        start_line=5,
        end_line=10
    )
    graph.add_edge(
        "processor.java:process_data:20",
        "processor.java:validate_data:5",
        edge_type="calls"
    )
    
    # Code missing transform_data but has validate_data in graph
    translated_code = """
def process_data(data: str) -> bool:
    # validate_data is in graph, so it's OK
    # transform_data is missing and not in graph
    return True
"""
    
    report = validator.validate_translation(node, translated_code, graph)
    
    assert report.dependencies_complete is False
    assert "transform_data" in report.missing_dependencies


def test_unit_test_stub_generation(validator, sample_node):
    """Test unit test stub generation."""
    translated_code = """
def calculate_sum(a: int, b: int) -> int:
    return add(a, b)
"""
    
    report = validator.validate_translation(sample_node, translated_code)
    
    assert report.unit_test_stub is not None
    assert "test_calculate_sum" in report.unit_test_stub
    assert "def test_calculate_sum():" in report.unit_test_stub
    assert "assert result is not None" in report.unit_test_stub


def test_control_flow_preservation(validator):
    """Test control flow block count validation."""
    node = ASTNode(
        id="test_003",
        name="complex_function",
        node_type="function",
        parameters=["x"],
        return_type="int",
        called_symbols=[],
        imports=[],
        file_path="test.java",
        start_line=1,
        end_line=20,
        raw_source="""
        public int complexFunction(int x) {
            if (x > 0) {
                for (int i = 0; i < x; i++) {
                    if (i % 2 == 0) {
                        continue;
                    }
                }
            }
            return x;
        }
        """
    )
    
    # Translation with similar control flow
    good_translation = """
def complex_function(x: int) -> int:
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                continue
    return x
"""
    
    report = validator.validate_translation(node, good_translation)
    assert report.structure_valid is True
    
    # Translation with very different control flow
    bad_translation = """
def complex_function(x: int) -> int:
    return x
"""
    
    report = validator.validate_translation(node, bad_translation)
    assert report.structure_valid is False


def test_validation_report_dataclass():
    """Test ValidationReport dataclass structure."""
    report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test_example(): pass",
        errors=[]
    )
    
    assert report.structure_valid is True
    assert report.symbols_preserved is True
    assert report.syntax_valid is True
    assert report.dependencies_complete is True
    assert report.missing_dependencies == []
    assert report.unit_test_stub == "def test_example(): pass"
    assert report.errors == []


def test_empty_called_symbols(validator):
    """Test validation with no called symbols."""
    node = ASTNode(
        id="test_004",
        name="simple_function",
        node_type="function",
        parameters=["x"],
        return_type="int",
        called_symbols=[],  # No dependencies
        imports=[],
        file_path="test.java",
        start_line=1,
        end_line=3,
        raw_source="public int simpleFunction(int x) { return x * 2; }"
    )
    
    translated_code = """
def simple_function(x: int) -> int:
    return x * 2
"""
    
    report = validator.validate_translation(node, translated_code)
    
    assert report.symbols_preserved is True
    assert report.dependencies_complete is True
    assert len(report.missing_dependencies) == 0


def test_class_method_parameter_extraction(validator):
    """Test parameter extraction for class methods."""
    node = ASTNode(
        id="test_005",
        name="process",
        node_type="method",
        parameters=["data"],  # Excluding 'self'
        return_type="str",
        called_symbols=[],
        imports=[],
        file_path="test.java",
        start_line=10,
        end_line=15,
        raw_source="public String process(String data) { return data; }"
    )
    
    # Python class method with self
    translated_code = """
class Processor:
    def process(self, data: str) -> str:
        return data
"""
    
    report = validator.validate_translation(node, translated_code)
    
    # Should pass because we exclude 'self' from count
    assert report.structure_valid is True
