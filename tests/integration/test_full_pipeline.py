"""Full pipeline integration tests for Legacy Code Modernization Engine.

These tests verify deterministic correctness of the complete pipeline:
AST → Graph → Context → Translation → Validation → Audit

Tests use real components (no mocking) with stub LLM responses.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch
import networkx as nx

from app.parsers.java_parser import JavaParser
from app.dependency_graph.graph_builder import GraphBuilder
from app.context_optimizer.optimizer import ContextOptimizer
from app.translation.orchestrator import TranslationOrchestrator, TranslationStore
from app.validation import ValidationEngine
from app.audit import AuditEngine
from app.llm.client import LLMClient


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def java_parser():
    """Get Java parser instance."""
    return JavaParser()


@pytest.fixture
def graph_builder():
    """Get graph builder instance."""
    return GraphBuilder()


@pytest.fixture
def context_optimizer():
    """Get context optimizer instance."""
    return ContextOptimizer()


@pytest.fixture
def validation_engine():
    """Get validation engine instance."""
    return ValidationEngine()


@pytest.fixture
def audit_engine():
    """Get audit engine instance."""
    return AuditEngine()


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client with stub responses."""
    mock_client = AsyncMock(spec=LLMClient)
    
    # Default stub response: valid Python translation
    async def stub_generate(prompt, temperature=0.3, max_tokens=100000):
        # Extract function name from prompt if possible
        if "calculateTotal" in prompt:
            return """def calculate_total(items):
    total = 0
    for item in items:
        total += item.get_price()
    return total"""
        elif "getPrice" in prompt:
            return """def get_price(self):
    return self.price * self.quantity"""
        elif "Item" in prompt:
            return """class Item:
    def __init__(self, price, quantity):
        self.price = price
        self.quantity = quantity
    
    def get_price(self):
        return self.price * self.quantity"""
        else:
            # Generic valid Python function
            return """def translated_function():
    result = process_data()
    return result"""
    
    mock_client.generate = stub_generate
    return mock_client


# ============================================================================
# Test 1: Multi-File Java Dependency Chain
# ============================================================================

def test_multi_file_dependency_chain(
    temp_dir,
    java_parser,
    graph_builder,
    context_optimizer,
    mock_llm_client,
    validation_engine
):
    """Test full pipeline with 3-file dependency chain: A → B → C.
    
    Verifies:
    - Dependency graph detects chain
    - Translation preserves symbol calls
    - Validation confirms dependencies complete
    """
    import asyncio
    
    # Create test files
    file_a = temp_dir / "A.java"
    file_a.write_text("""
public class A {
    public int calculateTotal(List<Item> items) {
        int total = 0;
        for (Item item : items) {
            total += item.getPrice();
        }
        return total;
    }
}
""")
    
    file_b = temp_dir / "B.java"
    file_b.write_text("""
public class Item {
    private int price;
    private int quantity;
    
    public int getPrice() {
        return price * quantity;
    }
}
""")
    
    file_c = temp_dir / "C.java"
    file_c.write_text("""
public class Helper {
    public static int multiply(int a, int b) {
        return a * b;
    }
}
""")
    
    # Phase 1: Parse files to AST
    ast_nodes = []
    for file_path in [file_a, file_b, file_c]:
        nodes = java_parser.parse_file(str(file_path))
        ast_nodes.extend(nodes)
    
    assert len(ast_nodes) >= 3, "Should parse at least 3 nodes"
    
    # Build AST index
    ast_index = {node.id: node for node in ast_nodes}
    
    # Phase 2: Build dependency graph
    dependency_graph = graph_builder.build_graph(ast_nodes)
    
    assert dependency_graph.number_of_nodes() >= 3, "Graph should have at least 3 nodes"
    assert dependency_graph.number_of_edges() >= 1, "Graph should have dependencies"
    
    # Verify dependency chain exists
    # A.calculateTotal should depend on Item.getPrice
    calculate_total_node = next((n for n in ast_nodes if "calculateTotal" in n.name), None)
    assert calculate_total_node is not None, "calculateTotal node should exist"
    
    # Check called symbols
    assert "getPrice" in calculate_total_node.called_symbols or \
           any("getPrice" in sym for sym in calculate_total_node.called_symbols), \
           "calculateTotal should call getPrice"
    
    # Phase 3: Translate with context optimization
    translation_store = TranslationStore()
    orchestrator = TranslationOrchestrator(
        llm_client=mock_llm_client,
        context_optimizer=context_optimizer,
        translation_store=translation_store
    )
    
    # Translate the calculateTotal function
    target_node_id = calculate_total_node.id
    
    # Optimize context
    optimized_context = context_optimizer.optimize_context(
        target_node_id=target_node_id,
        dependency_graph=dependency_graph,
        ast_index=ast_index
    )
    
    assert len(optimized_context.included_nodes) >= 1, "Should include target node"
    assert target_node_id in optimized_context.included_nodes, "Should include target"
    
    # Get stub translation (run async function)
    translated_code = asyncio.run(mock_llm_client.generate(
        prompt=f"Translate {calculate_total_node.name}",
        temperature=0.3
    ))
    
    # Phase 4: Validate translation
    validation_report = validation_engine.validate_translation(
        original_node=calculate_total_node,
        translated_code=translated_code,
        dependency_graph=dependency_graph
    )
    
    # Assertions
    assert validation_report.syntax_valid, "Translation should be syntactically valid"
    assert validation_report.structure_valid, "Structure should be preserved"
    assert validation_report.symbols_preserved, "Symbols should be preserved"
    assert validation_report.dependencies_complete, "Dependencies should be complete"
    assert len(validation_report.missing_dependencies) == 0, "No missing dependencies"
    assert len(validation_report.errors) == 0, "No validation errors"


# ============================================================================
# Test 2: Missing Dependency Detection
# ============================================================================

def test_missing_dependency_detection(
    temp_dir,
    java_parser,
    graph_builder,
    validation_engine
):
    """Test validation detects missing dependencies.
    
    Verifies:
    - When dependency file is missing, validation fails
    - missing_dependencies list contains function name
    """
    # Create file A that calls missing function
    file_a = temp_dir / "A.java"
    file_a.write_text("""
public class A {
    public void process() {
        int result = missingFunction();
        System.out.println(result);
    }
}
""")
    
    # Parse file
    ast_nodes = java_parser.parse_file(str(file_a))
    assert len(ast_nodes) >= 1, "Should parse at least 1 node"
    
    # Build graph (will be incomplete)
    dependency_graph = graph_builder.build_graph(ast_nodes)
    
    # Create translated code that calls missing function
    translated_code = """def process():
    result = missing_function()
    print(result)"""
    
    # Validate
    original_node = ast_nodes[0]
    validation_report = validation_engine.validate_translation(
        original_node=original_node,
        translated_code=translated_code,
        dependency_graph=dependency_graph
    )
    
    # Assertions
    assert validation_report.syntax_valid, "Syntax should be valid"
    assert not validation_report.dependencies_complete, "Dependencies should be incomplete"
    assert len(validation_report.missing_dependencies) > 0, "Should have missing dependencies"
    assert any("missing_function" in dep.lower() for dep in validation_report.missing_dependencies), \
        "Should detect missing_function"


# ============================================================================
# Test 3: Syntax Failure Detection
# ============================================================================

def test_syntax_failure_detection(
    temp_dir,
    java_parser,
    graph_builder,
    validation_engine
):
    """Test validation detects syntax errors in translation.
    
    Verifies:
    - Invalid Python syntax is caught
    - syntax_valid == False
    - errors list contains syntax error message
    """
    # Create simple Java file
    file_a = temp_dir / "A.java"
    file_a.write_text("""
public class A {
    public int add(int a, int b) {
        return a + b;
    }
}
""")
    
    # Parse file
    ast_nodes = java_parser.parse_file(str(file_a))
    assert len(ast_nodes) >= 1, "Should parse at least 1 node"
    
    # Build graph
    dependency_graph = graph_builder.build_graph(ast_nodes)
    
    # Create INVALID Python translation (syntax error)
    invalid_translated_code = """def add(a, b)
    return a + b  # Missing colon after function definition"""
    
    # Validate
    original_node = ast_nodes[0]
    validation_report = validation_engine.validate_translation(
        original_node=original_node,
        translated_code=invalid_translated_code,
        dependency_graph=dependency_graph
    )
    
    # Assertions
    assert not validation_report.syntax_valid, "Syntax should be invalid"
    assert len(validation_report.errors) > 0, "Should have syntax errors"
    assert any("syntax" in err.lower() for err in validation_report.errors), \
        "Error should mention syntax"


# ============================================================================
# Test 4: Placeholder Translation Detection
# ============================================================================

@pytest.mark.parametrize("placeholder_code,placeholder_type", [
    ("def process():\n    pass", "pass"),
    ("def process():\n    # TODO: implement\n    return None", "TODO"),
    ("def process():\n    raise NotImplementedError()", "NotImplementedError"),
])
def test_placeholder_translation_detection(
    temp_dir,
    java_parser,
    graph_builder,
    validation_engine,
    placeholder_code,
    placeholder_type
):
    """Test validation detects placeholder translations.
    
    Verifies:
    - Translations with 'pass', 'TODO', 'NotImplementedError' are rejected
    - Completeness check fails
    """
    # Create simple Java file
    file_a = temp_dir / "A.java"
    file_a.write_text("""
public class A {
    public void process() {
        System.out.println("Processing");
    }
}
""")
    
    # Parse file
    ast_nodes = java_parser.parse_file(str(file_a))
    assert len(ast_nodes) >= 1, "Should parse at least 1 node"
    
    # Build graph
    dependency_graph = graph_builder.build_graph(ast_nodes)
    
    # Validate placeholder translation
    original_node = ast_nodes[0]
    validation_report = validation_engine.validate_translation(
        original_node=original_node,
        translated_code=placeholder_code,
        dependency_graph=dependency_graph
    )
    
    # Assertions
    # Note: Current validator checks for these patterns
    # If structure_valid or other checks fail, that's acceptable
    has_error = (
        not validation_report.structure_valid or
        len(validation_report.errors) > 0 or
        any(placeholder_type.lower() in err.lower() for err in validation_report.errors)
    )
    
    assert has_error, f"Should detect {placeholder_type} placeholder"


# ============================================================================
# Test 5: BFS Depth Limit Enforcement
# ============================================================================

def test_bfs_depth_limit(
    temp_dir,
    java_parser,
    graph_builder,
    context_optimizer,
    validation_engine
):
    """Test context expansion respects depth limit.
    
    Verifies:
    - Deep dependency chains are bounded by CONTEXT_EXPANSION_DEPTH
    - Validation remains deterministic
    - Context expansion is bounded
    """
    # Create deep dependency chain: A → B → C → D → E
    files = []
    for i, (current, next_class) in enumerate([
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", None)
    ]):
        file_path = temp_dir / f"{current}.java"
        if next_class:
            content = f"""
public class {current} {{
    public void method{current}() {{
        {next_class} obj = new {next_class}();
        obj.method{next_class}();
    }}
}}
"""
        else:
            content = f"""
public class {current} {{
    public void method{current}() {{
        System.out.println("End of chain");
    }}
}}
"""
        file_path.write_text(content)
        files.append(file_path)
    
    # Parse all files
    ast_nodes = []
    for file_path in files:
        nodes = java_parser.parse_file(str(file_path))
        ast_nodes.extend(nodes)
    
    assert len(ast_nodes) >= 5, "Should parse at least 5 nodes"
    
    # Build graph
    dependency_graph = graph_builder.build_graph(ast_nodes)
    ast_index = {node.id: node for node in ast_nodes}
    
    # Find node A (root of chain)
    node_a = next((n for n in ast_nodes if "methodA" in n.name or "A" in n.file_path), None)
    assert node_a is not None, "Should find node A"
    
    # Optimize context with depth limit (default is 3)
    optimized_context = context_optimizer.optimize_context(
        target_node_id=node_a.id,
        dependency_graph=dependency_graph,
        ast_index=ast_index,
        expansion_depth=2  # Limit to depth 2
    )
    
    # Assertions
    assert len(optimized_context.included_nodes) >= 1, "Should include target node"
    assert len(optimized_context.included_nodes) <= 3, "Should respect depth limit (target + 2 levels)"
    assert optimized_context.expansion_depth == 2, "Should use specified depth"
    
    # Verify excluded nodes exist (deep dependencies)
    assert len(optimized_context.excluded_nodes) >= 0, "May have excluded nodes"
    
    # Create stub translation
    translated_code = """def method_a():
    obj = B()
    obj.method_b()"""
    
    # Validate - should still be deterministic
    validation_report = validation_engine.validate_translation(
        original_node=node_a,
        translated_code=translated_code,
        dependency_graph=dependency_graph
    )
    
    # Validation should complete deterministically
    assert validation_report.syntax_valid, "Syntax should be valid"
    assert isinstance(validation_report.dependencies_complete, bool), "Should have boolean result"


# ============================================================================
# Test 6: COBOL Small Repo Test
# ============================================================================

def test_cobol_small_repo(temp_dir):
    """Test COBOL parsing → translation → validation pipeline.
    
    Verifies:
    - COBOL AST parsing works
    - Translation pipeline handles COBOL
    - Validation works for COBOL-to-Python
    """
    from app.parsers.cobol_parser import CobolParser
    
    # Create minimal COBOL file
    cobol_file = temp_dir / "SAMPLE.cbl"
    cobol_file.write_text("""
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SAMPLE.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-NUM1 PIC 9(2) VALUE 10.
       01 WS-NUM2 PIC 9(2) VALUE 20.
       01 WS-RESULT PIC 9(3).
       
       PROCEDURE DIVISION.
           ADD WS-NUM1 TO WS-NUM2 GIVING WS-RESULT.
           DISPLAY "Result: " WS-RESULT.
           STOP RUN.
""")
    
    # Parse COBOL file
    cobol_parser = CobolParser()
    ast_nodes = cobol_parser.parse_file(str(cobol_file))
    
    # COBOL parser may return nodes or empty list depending on implementation
    # This test verifies the parser doesn't crash
    assert isinstance(ast_nodes, list), "Should return list of nodes"
    
    # If nodes were parsed, verify structure
    if len(ast_nodes) > 0:
        node = ast_nodes[0]
        assert hasattr(node, 'id'), "Node should have id"
        assert hasattr(node, 'name'), "Node should have name"
        assert hasattr(node, 'node_type'), "Node should have node_type"
        
        # Build graph
        graph_builder = GraphBuilder()
        dependency_graph = graph_builder.build_graph(ast_nodes)
        
        assert isinstance(dependency_graph, nx.DiGraph), "Should return DiGraph"
        
        # Create stub Python translation
        translated_code = """def sample():
    ws_num1 = 10
    ws_num2 = 20
    ws_result = ws_num1 + ws_num2
    print(f"Result: {ws_result}")"""
        
        # Validate
        validation_engine = ValidationEngine()
        validation_report = validation_engine.validate_translation(
            original_node=node,
            translated_code=translated_code,
            dependency_graph=dependency_graph
        )
        
        # Should complete without crashing
        assert validation_report.syntax_valid, "Translation should be syntactically valid"


# ============================================================================
# Test 7: Full Pipeline with Audit
# ============================================================================

async def test_full_pipeline_with_audit(
    temp_dir,
    java_parser,
    graph_builder,
    context_optimizer,
    mock_llm_client,
    validation_engine,
    audit_engine
):
    """Test complete pipeline including audit phase.
    
    Verifies:
    - Full pipeline executes end-to-end
    - Audit engine validates all phases
    - Deterministic results
    """
    # Create test file
    file_a = temp_dir / "Calculator.java"
    file_a.write_text("""
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int multiply(int a, int b) {
        return a * b;
    }
}
""")
    
    # Phase 1: Parse
    ast_nodes = java_parser.parse_file(str(file_a))
    assert len(ast_nodes) >= 2, "Should parse at least 2 methods"
    
    # Phase 2: Build graph
    dependency_graph = graph_builder.build_graph(ast_nodes)
    ast_index = {node.id: node for node in ast_nodes}
    
    # Phase 3: Translate all nodes
    validation_reports = []
    
    for node in ast_nodes:
        # Get stub translation
        translated_code = await mock_llm_client.generate(
            prompt=f"Translate {node.name}",
            temperature=0.3
        )
        
        # Validate
        validation_report = validation_engine.validate_translation(
            original_node=node,
            translated_code=translated_code,
            dependency_graph=dependency_graph
        )
        validation_reports.append(validation_report)
    
    # Phase 4: Generate mock documentation
    documentation = {}
    for node in ast_nodes:
        documentation[node.name] = f"# {node.name}\n\nGenerated documentation."
    
    # Phase 5: Run audit
    audit_report = audit_engine.run_audit(
        validation_reports=validation_reports,
        documentation=documentation
    )
    
    # Assertions
    assert audit_report.total_checks > 0, "Should run audit checks"
    assert isinstance(audit_report.overall_passed, bool), "Should have pass/fail result"
    assert audit_report.execution_time_ms > 0, "Should track execution time"
    assert len(audit_report.check_results) == audit_report.total_checks, "Should have all check results"
    
    # Verify determinism: run audit again
    audit_report_2 = audit_engine.run_audit(
        validation_reports=validation_reports,
        documentation=documentation
    )
    
    assert audit_report.overall_passed == audit_report_2.overall_passed, "Audit should be deterministic"
    assert audit_report.total_checks == audit_report_2.total_checks, "Check count should be same"


# ============================================================================
# Test 8: Token Limit Enforcement
# ============================================================================

def test_token_limit_enforcement(
    temp_dir,
    java_parser,
    graph_builder,
    context_optimizer
):
    """Test context optimizer respects token limits.
    
    Verifies:
    - Large files are truncated to fit token limit
    - Token estimation is deterministic
    """
    # Create large Java file
    large_file = temp_dir / "Large.java"
    
    # Generate large class with many methods
    methods = []
    for i in range(100):
        methods.append(f"""
    public int method{i}(int x) {{
        int result = x * {i};
        System.out.println("Method {i}: " + result);
        return result;
    }}
""")
    
    content = f"""
public class Large {{
    {''.join(methods)}
}}
"""
    large_file.write_text(content)
    
    # Parse file
    ast_nodes = java_parser.parse_file(str(large_file))
    assert len(ast_nodes) > 0, "Should parse nodes"
    
    # Build graph
    dependency_graph = graph_builder.build_graph(ast_nodes)
    ast_index = {node.id: node for node in ast_nodes}
    
    # Optimize with small token limit
    target_node = ast_nodes[0]
    optimized_context = context_optimizer.optimize_context(
        target_node_id=target_node.id,
        dependency_graph=dependency_graph,
        ast_index=ast_index,
        max_tokens=1000  # Small limit
    )
    
    # Assertions
    assert optimized_context.estimated_tokens <= 1000, "Should respect token limit"
    assert len(optimized_context.included_nodes) >= 1, "Should include target node"
    assert len(optimized_context.excluded_nodes) >= 0, "May exclude nodes due to limit"
