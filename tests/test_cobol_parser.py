"""Unit tests for COBOL parser implementation.

Tests verify:
- Complete parsing of COBOL constructs (PROGRAM-ID, SECTION, paragraph)
- CALL statement extraction
- PERFORM statement extraction
- ASTNode schema compliance
- Raw source preservation
"""

import pytest
import tempfile
from pathlib import Path

from app.parsers.cobol_parser import CobolParser
from app.parsers.base import ASTNode


@pytest.fixture
def cobol_parser():
    """Create CobolParser instance for testing."""
    return CobolParser()


@pytest.fixture
def simple_cobol_file(tmp_path):
    """Create a simple COBOL file for testing."""
    content = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. SIMPLE-PROG.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           DISPLAY "Hello World".
           STOP RUN.
"""
    file_path = tmp_path / "simple.cbl"
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def cobol_with_calls(tmp_path):
    """Create COBOL file with CALL statements."""
    content = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALLER-PROG.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           CALL 'SUBPROG1' USING WS-DATA.
           CALL 'SUBPROG2' USING WS-RESULT.
           STOP RUN.
"""
    file_path = tmp_path / "caller.cbl"
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def cobol_with_performs(tmp_path):
    """Create COBOL file with PERFORM statements."""
    content = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. PERFORM-PROG.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM INIT-ROUTINE.
           PERFORM PROCESS-DATA.
           PERFORM CLEANUP-ROUTINE.
           STOP RUN.
       
       INIT-ROUTINE.
           DISPLAY "Initializing".
       
       PROCESS-DATA.
           DISPLAY "Processing".
       
       CLEANUP-ROUTINE.
           DISPLAY "Cleaning up".
"""
    file_path = tmp_path / "perform.cbl"
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def cobol_with_sections(tmp_path):
    """Create COBOL file with SECTION definitions."""
    content = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. SECTION-PROG.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-DATA PIC X(10).
       
       PROCEDURE DIVISION.
       MAIN-SECTION SECTION.
       MAIN-LOGIC.
           DISPLAY "Main section".
           STOP RUN.
"""
    file_path = tmp_path / "sections.cbl"
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def complex_cobol_file(tmp_path):
    """Create complex COBOL file with multiple constructs."""
    content = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. COMPLEX-PROG.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-COUNTER PIC 9(3) VALUE 0.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM INIT-ROUTINE.
           CALL 'VALIDATOR' USING WS-COUNTER.
           PERFORM PROCESS-LOOP.
           CALL 'LOGGER' USING WS-COUNTER.
           STOP RUN.
       
       INIT-ROUTINE.
           MOVE 0 TO WS-COUNTER.
       
       PROCESS-LOOP.
           PERFORM CALCULATE-VALUE.
           ADD 1 TO WS-COUNTER.
       
       CALCULATE-VALUE.
           DISPLAY "Calculating".
"""
    file_path = tmp_path / "complex.cbl"
    file_path.write_text(content)
    return str(file_path)


def test_parser_initialization(cobol_parser):
    """Test CobolParser initializes correctly."""
    assert cobol_parser is not None
    assert cobol_parser.supports_language() == "cobol"


def test_simple_cobol_parsing(cobol_parser, simple_cobol_file):
    """Test parsing simple COBOL file."""
    nodes = cobol_parser.parse_file(simple_cobol_file)
    
    assert len(nodes) > 0
    
    # Check for PROGRAM-ID node
    program_nodes = [n for n in nodes if n.node_type == "program"]
    assert len(program_nodes) == 1
    assert program_nodes[0].name == "SIMPLE-PROG"
    
    # Check for paragraph node
    paragraph_nodes = [n for n in nodes if n.node_type == "paragraph"]
    assert len(paragraph_nodes) >= 1
    assert any(n.name == "MAIN-LOGIC" for n in paragraph_nodes)


def test_call_statement_extraction(cobol_parser, cobol_with_calls):
    """Test CALL statement extraction."""
    nodes = cobol_parser.parse_file(cobol_with_calls)
    
    # Find program node
    program_nodes = [n for n in nodes if n.node_type == "program"]
    assert len(program_nodes) == 1
    
    program_node = program_nodes[0]
    
    # Check called symbols
    assert "SUBPROG1" in program_node.called_symbols
    assert "SUBPROG2" in program_node.called_symbols


def test_perform_statement_extraction(cobol_parser, cobol_with_performs):
    """Test PERFORM statement extraction."""
    nodes = cobol_parser.parse_file(cobol_with_performs)
    
    # Find MAIN-LOGIC paragraph
    main_logic = [n for n in nodes if n.name == "MAIN-LOGIC"]
    assert len(main_logic) == 1
    
    main_node = main_logic[0]
    
    # Check performed paragraphs in called_symbols
    assert "INIT-ROUTINE" in main_node.called_symbols
    assert "PROCESS-DATA" in main_node.called_symbols
    assert "CLEANUP-ROUTINE" in main_node.called_symbols
    
    # Verify all paragraphs are parsed
    paragraph_names = [n.name for n in nodes if n.node_type == "paragraph"]
    assert "INIT-ROUTINE" in paragraph_names
    assert "PROCESS-DATA" in paragraph_names
    assert "CLEANUP-ROUTINE" in paragraph_names


def test_section_extraction(cobol_parser, cobol_with_sections):
    """Test SECTION extraction."""
    nodes = cobol_parser.parse_file(cobol_with_sections)
    
    # Find section nodes
    section_nodes = [n for n in nodes if n.node_type == "section"]
    
    # Should have WORKING-STORAGE SECTION and MAIN-SECTION
    section_names = [n.name for n in section_nodes]
    assert "WORKING-STORAGE" in section_names
    assert "MAIN-SECTION" in section_names


def test_complex_cobol_parsing(cobol_parser, complex_cobol_file):
    """Test parsing complex COBOL file with multiple constructs."""
    nodes = cobol_parser.parse_file(complex_cobol_file)
    
    # Verify node count
    assert len(nodes) >= 6  # program + section + 4 paragraphs
    
    # Check program node
    program_nodes = [n for n in nodes if n.node_type == "program"]
    assert len(program_nodes) == 1
    assert program_nodes[0].name == "COMPLEX-PROG"
    
    # Check program dependencies include both CALL and PERFORM
    program_deps = program_nodes[0].called_symbols
    assert "VALIDATOR" in program_deps
    assert "LOGGER" in program_deps
    assert "INIT-ROUTINE" in program_deps
    assert "PROCESS-LOOP" in program_deps
    
    # Check paragraph nodes
    paragraph_nodes = [n for n in nodes if n.node_type == "paragraph"]
    paragraph_names = [n.name for n in paragraph_nodes]
    assert "MAIN-LOGIC" in paragraph_names
    assert "INIT-ROUTINE" in paragraph_names
    assert "PROCESS-LOOP" in paragraph_names
    assert "CALCULATE-VALUE" in paragraph_names
    
    # Check PROCESS-LOOP has PERFORM dependency
    process_loop = [n for n in nodes if n.name == "PROCESS-LOOP"][0]
    assert "CALCULATE-VALUE" in process_loop.called_symbols


def test_astnode_schema_compliance(cobol_parser, simple_cobol_file):
    """Test that all ASTNode objects comply with schema."""
    nodes = cobol_parser.parse_file(simple_cobol_file)
    
    for node in nodes:
        # Check all required fields exist
        assert hasattr(node, 'id')
        assert hasattr(node, 'name')
        assert hasattr(node, 'node_type')
        assert hasattr(node, 'parameters')
        assert hasattr(node, 'return_type')
        assert hasattr(node, 'called_symbols')
        assert hasattr(node, 'imports')
        assert hasattr(node, 'file_path')
        assert hasattr(node, 'start_line')
        assert hasattr(node, 'end_line')
        assert hasattr(node, 'raw_source')
        
        # Check types
        assert isinstance(node.id, str)
        assert isinstance(node.name, str)
        assert isinstance(node.node_type, str)
        assert isinstance(node.parameters, list)
        assert isinstance(node.called_symbols, list)
        assert isinstance(node.imports, list)
        assert isinstance(node.file_path, str)
        assert isinstance(node.start_line, int)
        assert isinstance(node.end_line, int)
        assert isinstance(node.raw_source, str)
        
        # Check non-empty required fields
        assert len(node.id) > 0
        assert len(node.name) > 0
        assert len(node.node_type) > 0
        assert node.start_line > 0


def test_raw_source_preservation(cobol_parser, simple_cobol_file):
    """Test that raw_source is preserved exactly."""
    nodes = cobol_parser.parse_file(simple_cobol_file)
    
    for node in nodes:
        # Raw source should not be empty
        assert len(node.raw_source) > 0
        
        # Raw source should contain the node name
        assert node.name in node.raw_source.upper()


def test_extract_dependencies(cobol_parser, cobol_with_calls):
    """Test extract_dependencies method."""
    nodes = cobol_parser.parse_file(cobol_with_calls)
    dependencies = cobol_parser.extract_dependencies(nodes)
    
    # Should return sorted list of unique dependencies
    assert isinstance(dependencies, list)
    assert "SUBPROG1" in dependencies
    assert "SUBPROG2" in dependencies
    
    # Check sorted
    assert dependencies == sorted(dependencies)


def test_empty_file_handling(cobol_parser, tmp_path):
    """Test handling of empty file."""
    empty_file = tmp_path / "empty.cbl"
    empty_file.write_text("")
    
    nodes = cobol_parser.parse_file(str(empty_file))
    assert nodes == []


def test_nonexistent_file_handling(cobol_parser):
    """Test handling of nonexistent file."""
    nodes = cobol_parser.parse_file("/nonexistent/file.cbl")
    assert nodes == []


def test_case_insensitivity(cobol_parser, tmp_path):
    """Test that COBOL parsing is case-insensitive."""
    content = """       identification division.
       program-id. lowercase-prog.
       
       procedure division.
       main-logic.
           call 'SUBPROG' using ws-data.
           perform init-routine.
           stop run.
       
       init-routine.
           display "Init".
"""
    file_path = tmp_path / "lowercase.cbl"
    file_path.write_text(content)
    
    nodes = cobol_parser.parse_file(str(file_path))
    
    # Should parse successfully despite lowercase
    assert len(nodes) > 0
    
    # Check program node
    program_nodes = [n for n in nodes if n.node_type == "program"]
    assert len(program_nodes) == 1
    assert program_nodes[0].name == "LOWERCASE-PROG"
    
    # Check dependencies
    assert "SUBPROG" in program_nodes[0].called_symbols
    assert "INIT-ROUTINE" in program_nodes[0].called_symbols


def test_astnode_immutability(cobol_parser, simple_cobol_file):
    """Test that ASTNode objects are immutable (frozen dataclass)."""
    nodes = cobol_parser.parse_file(simple_cobol_file)
    
    if nodes:
        node = nodes[0]
        
        # Attempt to modify should raise FrozenInstanceError
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            node.name = "MODIFIED"
        
        with pytest.raises(Exception):
            node.called_symbols = []


def test_node_id_format(cobol_parser, simple_cobol_file):
    """Test that node IDs follow expected format."""
    nodes = cobol_parser.parse_file(simple_cobol_file)
    
    for node in nodes:
        # ID should contain file path and node name
        assert simple_cobol_file in node.id or "simple.cbl" in node.id
        assert "::" in node.id
        assert node.name in node.id


def test_multiple_paragraphs(cobol_parser, cobol_with_performs):
    """Test parsing file with multiple paragraphs."""
    nodes = cobol_parser.parse_file(cobol_with_performs)
    
    paragraph_nodes = [n for n in nodes if n.node_type == "paragraph"]
    
    # Should have at least 4 paragraphs
    assert len(paragraph_nodes) >= 4
    
    # Each paragraph should have unique ID
    ids = [n.id for n in paragraph_nodes]
    assert len(ids) == len(set(ids))


def test_real_sample_file(cobol_parser):
    """Test parsing real sample COBOL file from repository."""
    sample_file = "sample_repos/cobol_small/main.cbl"
    
    # Check if file exists
    if not Path(sample_file).exists():
        pytest.skip("Sample file not found")
    
    nodes = cobol_parser.parse_file(sample_file)
    
    # Should parse successfully
    assert len(nodes) > 0
    
    # Check for expected constructs
    program_nodes = [n for n in nodes if n.node_type == "program"]
    assert len(program_nodes) >= 1
    
    # Check for CALL statements
    program_node = program_nodes[0]
    assert "VALIDATION" in program_node.called_symbols or "PAYMENT" in program_node.called_symbols
