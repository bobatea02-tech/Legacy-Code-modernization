"""Tests for TranslationOrchestrator."""

import pytest
import networkx as nx
from unittest.mock import AsyncMock, MagicMock, patch

from app.translation.orchestrator import (
    TranslationOrchestrator,
    TranslationResult,
    TranslationStatus,
    TranslationStore
)
from app.parsers.base import ASTNode
from app.llm.client import LLMClient
from app.validation.validator import ValidationEngine, ValidationReport


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = None) -> str:
        """Mock generate method."""
        return f"def translated_function():\n    pass"
    
    async def embed(self, text: str) -> list:
        """Mock embed method."""
        return [0.1, 0.2, 0.3]


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    return MockLLMClient()


@pytest.fixture
def mock_validator():
    """Create mock validator."""
    validator = MagicMock(spec=ValidationEngine)
    # Mock validate_translation to return a passing ValidationReport
    validator.validate_translation.return_value = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="",
        errors=[]
    )
    return validator


@pytest.fixture
def simple_graph():
    """Create simple dependency graph for testing."""
    graph = nx.DiGraph()
    graph.add_node("file.py:funcA:1", name="funcA", node_type="function")
    graph.add_node("file.py:funcB:10", name="funcB", node_type="function")
    graph.add_edge("file.py:funcB:10", "file.py:funcA:1")  # funcB depends on funcA
    return graph


@pytest.fixture
def simple_ast_index():
    """Create simple AST index for testing."""
    return {
        "file.py:funcA:1": ASTNode(
            id="1",
            name="funcA",
            node_type="function",
            parameters=[],
            return_type="int",
            file_path="file.py",
            start_line=1,
            end_line=5,
            raw_source="function funcA() { return 42; }",
            called_symbols=[],
            imports=[]
        ),
        "file.py:funcB:10": ASTNode(
            id="2",
            name="funcB",
            node_type="function",
            parameters=[],
            return_type="int",
            file_path="file.py",
            start_line=10,
            end_line=15,
            raw_source="function funcB() { return funcA() + 1; }",
            called_symbols=["funcA"],
            imports=[]
        )
    }


class TestTranslationStore:
    """Tests for TranslationStore."""
    
    def test_store_and_get(self):
        """Test storing and retrieving translation results."""
        store = TranslationStore()
        result = TranslationResult(
            module_name="test_module",
            status=TranslationStatus.SUCCESS,
            translated_code="def test(): pass",
            source_hash="abc123"
        )
        
        store.store(result)
        retrieved = store.get("test_module")
        
        assert retrieved is not None
        assert retrieved.module_name == "test_module"
        assert retrieved.status == TranslationStatus.SUCCESS
    
    def test_get_by_hash(self):
        """Test retrieving by source hash."""
        store = TranslationStore()
        result = TranslationResult(
            module_name="test_module",
            status=TranslationStatus.SUCCESS,
            source_hash="abc123"
        )
        
        store.store(result)
        retrieved = store.get_by_hash("abc123")
        
        assert retrieved is not None
        assert retrieved.module_name == "test_module"
    
    def test_has(self):
        """Test checking if module exists."""
        store = TranslationStore()
        result = TranslationResult(
            module_name="test_module",
            status=TranslationStatus.SUCCESS
        )
        
        assert not store.has("test_module")
        store.store(result)
        assert store.has("test_module")
    
    def test_clear(self):
        """Test clearing store."""
        store = TranslationStore()
        result = TranslationResult(
            module_name="test_module",
            status=TranslationStatus.SUCCESS
        )
        
        store.store(result)
        assert store.has("test_module")
        
        store.clear()
        assert not store.has("test_module")


class TestTranslationOrchestrator:
    """Tests for TranslationOrchestrator."""
    
    @pytest.mark.asyncio
    async def test_translate_repository_simple(
        self,
        mock_llm_client,
        mock_validator,
        simple_graph,
        simple_ast_index
    ):
        """Test translating simple repository."""
        orchestrator = TranslationOrchestrator(
            llm_client=mock_llm_client,
            validator=mock_validator
        )
        
        results = await orchestrator.translate_repository(
            dependency_graph=simple_graph,
            ast_index=simple_ast_index
        )
        
        assert len(results) == 2
        assert all(r.status == TranslationStatus.SUCCESS for r in results)
        
        # Check that funcA is translated after funcB (funcB depends on funcA)
        # In topological sort, for edge B->A, B comes before A
        module_names = [r.module_name for r in results]
        assert module_names.index("file.py:funcB:10") < module_names.index("file.py:funcA:1")
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(
        self,
        mock_llm_client,
        mock_validator,
        simple_ast_index
    ):
        """Test that circular dependencies are detected."""
        # Create graph with cycle
        graph = nx.DiGraph()
        graph.add_node("file.py:funcA:1")
        graph.add_node("file.py:funcB:10")
        graph.add_edge("file.py:funcA:1", "file.py:funcB:10")
        graph.add_edge("file.py:funcB:10", "file.py:funcA:1")  # Creates cycle
        
        orchestrator = TranslationOrchestrator(
            llm_client=mock_llm_client,
            validator=mock_validator
        )
        
        with pytest.raises(ValueError, match="Circular dependencies detected"):
            await orchestrator.translate_repository(
                dependency_graph=graph,
                ast_index=simple_ast_index
            )
    
    @pytest.mark.asyncio
    async def test_caching(
        self,
        mock_llm_client,
        mock_validator,
        simple_graph,
        simple_ast_index
    ):
        """Test that caching works correctly."""
        orchestrator = TranslationOrchestrator(
            llm_client=mock_llm_client,
            validator=mock_validator
        )
        
        # First translation
        results1 = await orchestrator.translate_repository(
            dependency_graph=simple_graph,
            ast_index=simple_ast_index
        )
        
        # Second translation (should use cache)
        results2 = await orchestrator.translate_repository(
            dependency_graph=simple_graph,
            ast_index=simple_ast_index
        )
        
        # Check that second run used cache
        assert any(r.status == TranslationStatus.SKIPPED for r in results2)
    
    @pytest.mark.asyncio
    async def test_validation_failure(
        self,
        mock_llm_client,
        simple_graph,
        simple_ast_index
    ):
        """Test handling of validation failures."""
        # Create validator that returns errors
        validator = MagicMock(spec=ValidationEngine)
        validator.validate_translation.return_value = ValidationReport(
            structure_valid=False,
            symbols_preserved=False,
            syntax_valid=False,
            dependencies_complete=False,
            missing_dependencies=["missing_func"],
            unit_test_stub="",
            errors=["Syntax error at line 1"]
        )
        
        orchestrator = TranslationOrchestrator(
            llm_client=mock_llm_client,
            validator=validator
        )
        
        results = await orchestrator.translate_repository(
            dependency_graph=simple_graph,
            ast_index=simple_ast_index
        )
        
        # Check that validation errors are captured
        assert any(r.status == TranslationStatus.FAILED for r in results)
        assert any(len(r.errors) > 0 for r in results)
    
    def test_get_translation_statistics(self, mock_llm_client, mock_validator):
        """Test statistics calculation."""
        orchestrator = TranslationOrchestrator(
            llm_client=mock_llm_client,
            validator=mock_validator
        )
        
        results = [
            TranslationResult(
                module_name="mod1",
                status=TranslationStatus.SUCCESS,
                token_usage=100
            ),
            TranslationResult(
                module_name="mod2",
                status=TranslationStatus.FAILED,
                token_usage=50,
                errors=["error1"]
            ),
            TranslationResult(
                module_name="mod3",
                status=TranslationStatus.SKIPPED,
                token_usage=0
            )
        ]
        
        stats = orchestrator.get_translation_statistics(results)
        
        assert stats["total_modules"] == 3
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["skipped"] == 1
        assert stats["total_tokens"] == 150
        assert stats["total_errors"] == 1
        assert stats["success_rate"] == pytest.approx(33.33, rel=0.1)
