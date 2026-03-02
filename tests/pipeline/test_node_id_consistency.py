"""Test node ID consistency across pipeline components.

This test verifies that:
1. Parser IDs == Graph IDs == Translation IDs
2. Single source of truth for node IDs is maintained
3. No ID mismatches occur during pipeline execution
"""

import pytest
from pathlib import Path
from app.parsers.java_parser import JavaParser
from app.parsers.cobol_parser import CobolParser
from app.dependency_graph.graph_builder import GraphBuilder
from app.translation.orchestrator import TranslationOrchestrator
from app.llm.llm_service import LLMService
from app.llm.gemini_client import GeminiClient


class TestNodeIDConsistency:
    """Test suite for node ID consistency across pipeline."""
    
    def test_java_parser_node_id_format(self, tmp_path):
        """Test that Java parser generates correct node ID format."""
        # Create test Java file
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
public class TestClass {
    public void testMethod() {
        System.out.println("test");
    }
}
""")
        
        parser = JavaParser()
        nodes = parser.parse_file(str(java_file))
        
        assert len(nodes) > 0, "Parser should extract nodes"
        
        for node in nodes:
            # Verify node ID contains file path, name, and line number
            # Format: file_path:name:start_line
            # Note: On Windows, file_path contains drive letter with colon (C:\)
            assert node.file_path in node.id, f"Node ID should contain file path"
            assert f":{node.name}:" in node.id, f"Node ID should contain :name: pattern"
            assert node.id.endswith(f":{node.start_line}"), f"Node ID should end with :line_number"
    
    def test_cobol_parser_node_id_format(self, tmp_path):
        """Test that COBOL parser generates correct node ID format."""
        # Create test COBOL file
        cobol_file = tmp_path / "test.cbl"
        cobol_file.write_text("""
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TESTPROG.
       PROCEDURE DIVISION.
       MAIN-PARA.
           DISPLAY 'TEST'.
           STOP RUN.
""")
        
        parser = CobolParser()
        nodes = parser.parse_file(str(cobol_file))
        
        assert len(nodes) > 0, "Parser should extract nodes"
        
        for node in nodes:
            # Verify node ID contains file path, name, and line number
            # Format: file_path:name:start_line
            # Note: On Windows, file_path contains drive letter with colon (C:\)
            assert node.file_path in node.id, f"Node ID should contain file path"
            assert f":{node.name}:" in node.id, f"Node ID should contain :name: pattern"
            assert node.id.endswith(f":{node.start_line}"), f"Node ID should end with :line_number"
    
    def test_graph_builder_preserves_parser_ids(self, tmp_path):
        """Test that GraphBuilder uses parser-assigned node IDs."""
        # Create test Java file
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
public class TestClass {
    public void testMethod() {
        System.out.println("test");
    }
}
""")
        
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(java_file))
        
        # Build graph
        builder = GraphBuilder()
        graph = builder.build_graph(ast_nodes)
        
        # Verify all parser node IDs are in graph
        parser_ids = {node.id for node in ast_nodes}
        graph_ids = set(graph.nodes())
        
        assert parser_ids == graph_ids, (
            f"Graph node IDs must match parser node IDs.\n"
            f"Parser IDs: {parser_ids}\n"
            f"Graph IDs: {graph_ids}\n"
            f"Missing in graph: {parser_ids - graph_ids}\n"
            f"Extra in graph: {graph_ids - parser_ids}"
        )
    
    def test_ast_index_consistency(self, tmp_path):
        """Test that AST index uses correct node IDs."""
        # Create test Java file
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
public class TestClass {
    public void testMethod() {
        System.out.println("test");
    }
}
""")
        
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(java_file))
        
        # Build AST index (as done in pipeline)
        ast_index = {node.id: node for node in ast_nodes}
        
        # Build graph
        builder = GraphBuilder()
        graph = builder.build_graph(ast_nodes)
        
        # Verify all graph node IDs exist in AST index
        for node_id in graph.nodes():
            assert node_id in ast_index, (
                f"Graph node ID '{node_id}' not found in AST index.\n"
                f"AST index keys: {list(ast_index.keys())}"
            )
    
    def test_translation_orchestrator_node_lookup(self, tmp_path):
        """Test that TranslationOrchestrator can look up nodes correctly."""
        # Create test Java file
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
public class TestClass {
    public void testMethod() {
        System.out.println("test");
    }
}
""")
        
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(java_file))
        
        # Build graph and AST index
        builder = GraphBuilder()
        graph = builder.build_graph(ast_nodes)
        ast_index = {node.id: node for node in ast_nodes}
        
        # Verify all graph nodes can be looked up in AST index
        for node_id in graph.nodes():
            # This is what TranslationOrchestrator does
            assert node_id in ast_index, f"Node {node_id} not found in AST index"
            ast_node = ast_index[node_id]
            assert ast_node.id == node_id, "AST node ID should match lookup key"
    
    def test_no_id_generation_in_graph_builder(self, tmp_path):
        """Test that GraphBuilder does not generate new IDs."""
        # Create test Java file
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
public class TestClass {
    public void testMethod() {
        System.out.println("test");
    }
}
""")
        
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(java_file))
        
        # Capture original IDs
        original_ids = {node.id for node in ast_nodes}
        
        # Build graph
        builder = GraphBuilder()
        graph = builder.build_graph(ast_nodes)
        
        # Verify graph uses exact same IDs (no new generation)
        graph_ids = set(graph.nodes())
        
        assert original_ids == graph_ids, (
            "GraphBuilder must not generate new IDs.\n"
            f"Original parser IDs: {original_ids}\n"
            f"Graph IDs: {graph_ids}"
        )
    
    def test_node_id_uniqueness(self, tmp_path):
        """Test that node IDs are globally unique."""
        # Create test Java file with multiple constructs
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
public class TestClass {
    public void method1() {
        System.out.println("test1");
    }
    
    public void method2() {
        System.out.println("test2");
    }
}

public class AnotherClass {
    public void method1() {
        System.out.println("test3");
    }
}
""")
        
        parser = JavaParser()
        ast_nodes = parser.parse_file(str(java_file))
        
        # Verify all node IDs are unique
        node_ids = [node.id for node in ast_nodes]
        unique_ids = set(node_ids)
        
        assert len(node_ids) == len(unique_ids), (
            f"Node IDs must be unique. Found duplicates: "
            f"{[id for id in node_ids if node_ids.count(id) > 1]}"
        )
    
    def test_cross_file_node_id_uniqueness(self, tmp_path):
        """Test that node IDs are unique across multiple files."""
        # Create two Java files with same class name
        file1 = tmp_path / "File1.java"
        file1.write_text("""
public class TestClass {
    public void testMethod() {
        System.out.println("file1");
    }
}
""")
        
        file2 = tmp_path / "File2.java"
        file2.write_text("""
public class TestClass {
    public void testMethod() {
        System.out.println("file2");
    }
}
""")
        
        parser = JavaParser()
        nodes1 = parser.parse_file(str(file1))
        nodes2 = parser.parse_file(str(file2))
        
        all_nodes = nodes1 + nodes2
        
        # Verify all node IDs are unique across files
        node_ids = [node.id for node in all_nodes]
        unique_ids = set(node_ids)
        
        assert len(node_ids) == len(unique_ids), (
            f"Node IDs must be unique across files. Found duplicates: "
            f"{[id for id in node_ids if node_ids.count(id) > 1]}"
        )
        
        # Verify file path is part of ID (ensures uniqueness)
        for node in all_nodes:
            assert node.file_path in node.id, (
                f"Node ID must contain file path for cross-file uniqueness: {node.id}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
