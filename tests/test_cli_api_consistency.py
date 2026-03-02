"""Test CLI and API consistency.

Verifies that CLI and API produce identical results when using the same
PipelineService backend.
"""

import pytest
from pathlib import Path
import tempfile
import zipfile
import asyncio

from app.pipeline.service import PipelineService


@pytest.fixture
def sample_zip_file():
    """Create a sample ZIP file for testing."""
    # Create temporary ZIP with sample Java file
    temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    temp_zip_path = temp_zip.name
    temp_zip.close()
    
    with zipfile.ZipFile(temp_zip_path, 'w') as zf:
        # Add a simple Java file
        java_content = """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int subtract(int a, int b) {
        return a - b;
    }
}
"""
        zf.writestr("Calculator.java", java_content)
    
    yield temp_zip_path
    
    # Cleanup
    Path(temp_zip_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_validation_pipeline_consistency(sample_zip_file):
    """Test that validation pipeline produces consistent results.
    
    Both CLI and API use PipelineService.execute_validation_pipeline(),
    so results should be identical.
    """
    # Simulate CLI execution
    cli_pipeline = PipelineService()
    cli_result = await cli_pipeline.execute_validation_pipeline(
        repo_path=sample_zip_file,
        source_language="java"
    )
    
    # Simulate API execution
    api_pipeline = PipelineService()
    api_result = await api_pipeline.execute_validation_pipeline(
        repo_path=sample_zip_file,
        source_language="java"
    )
    
    # Verify results are identical
    assert cli_result["status"] == api_result["status"]
    assert cli_result["file_count"] == api_result["file_count"]
    assert cli_result["ast_node_count"] == api_result["ast_node_count"]
    assert cli_result["graph_node_count"] == api_result["graph_node_count"]
    assert cli_result["graph_edge_count"] == api_result["graph_edge_count"]
    assert cli_result["is_dag"] == api_result["is_dag"]
    assert cli_result["circular_dependencies"] == api_result["circular_dependencies"]
    
    # Verify successful validation
    assert cli_result["status"] == "success"
    assert cli_result["is_dag"] is True
    assert cli_result["circular_dependencies"] == 0


@pytest.mark.asyncio
async def test_optimization_pipeline_consistency(sample_zip_file):
    """Test that optimization pipeline produces consistent results.
    
    Both CLI and API use PipelineService.execute_optimization_pipeline(),
    so results should be identical.
    """
    # Simulate CLI execution
    cli_pipeline = PipelineService()
    cli_result = await cli_pipeline.execute_optimization_pipeline(
        repo_path=sample_zip_file,
        source_language="java",
        expansion_depth=2
    )
    
    # Simulate API execution
    api_pipeline = PipelineService()
    api_result = await api_pipeline.execute_optimization_pipeline(
        repo_path=sample_zip_file,
        source_language="java",
        expansion_depth=2
    )
    
    # Verify results are identical
    assert cli_result["status"] == api_result["status"]
    assert cli_result["file_count"] == api_result["file_count"]
    assert cli_result["ast_node_count"] == api_result["ast_node_count"]
    assert cli_result["graph_node_count"] == api_result["graph_node_count"]
    assert cli_result["graph_edge_count"] == api_result["graph_edge_count"]
    assert cli_result["expansion_depth"] == api_result["expansion_depth"]
    assert len(cli_result["sample_optimizations"]) == len(api_result["sample_optimizations"])
    
    # Verify successful optimization
    assert cli_result["status"] == "success"
    assert cli_result["expansion_depth"] == 2
    assert len(cli_result["sample_optimizations"]) > 0


@pytest.mark.asyncio
async def test_translation_pipeline_consistency(sample_zip_file):
    """Test that translation pipeline produces consistent results.
    
    Both CLI and API use PipelineService.execute_full_pipeline(),
    so results should be identical.
    """
    # Simulate CLI execution
    cli_pipeline = PipelineService()
    cli_result = await cli_pipeline.execute_full_pipeline(
        repo_path=sample_zip_file,
        source_language="java",
        target_language="python",
        repository_id="test_cli"
    )
    
    # Simulate API execution
    api_pipeline = PipelineService()
    api_result = await api_pipeline.execute_full_pipeline(
        repo_path=sample_zip_file,
        source_language="java",
        target_language="python",
        repository_id="test_api"
    )
    
    # Verify results are structurally identical (excluding repo_id)
    assert cli_result.success == api_result.success
    assert cli_result.file_count == api_result.file_count
    assert cli_result.ast_node_count == api_result.ast_node_count
    assert cli_result.graph_node_count == api_result.graph_node_count
    assert cli_result.graph_edge_count == api_result.graph_edge_count
    assert len(cli_result.translation_results) == len(api_result.translation_results)
    assert len(cli_result.validation_reports) == len(api_result.validation_reports)
    
    # Verify successful execution
    assert cli_result.success is True
    assert len(cli_result.translation_results) > 0


def test_no_orchestration_in_cli():
    """Verify CLI contains no business logic orchestration.
    
    CLI should only call PipelineService methods.
    """
    import inspect
    from app.cli import cli
    
    source = inspect.getsource(cli)
    
    # Should not contain direct instantiation of business logic classes
    assert "GraphBuilder()" not in source
    assert "ContextOptimizer()" not in source
    assert "TranslationOrchestrator()" not in source
    assert "ValidationEngine()" not in source
    
    # Should use PipelineService
    assert "PipelineService()" in source
    assert "execute_validation_pipeline" in source
    assert "execute_optimization_pipeline" in source
    assert "execute_full_pipeline" in source


def test_no_orchestration_in_api():
    """Verify API contains no business logic orchestration.
    
    API routes should only call PipelineService methods.
    """
    import inspect
    from app.api import routes
    
    source = inspect.getsource(routes)
    
    # Should use PipelineService
    assert "get_pipeline_service" in source
    assert "execute_validation_pipeline" in source
    assert "execute_optimization_pipeline" in source
    assert "execute_full_pipeline" in source


def test_pipeline_service_is_single_orchestrator():
    """Verify PipelineService is the only orchestrator.
    
    All business logic coordination should happen in PipelineService.
    """
    import inspect
    from app.pipeline import service
    
    source = inspect.getsource(service.PipelineService)
    
    # Should contain orchestration logic
    assert "GraphBuilder()" in source
    assert "ContextOptimizer()" in source
    assert "ValidationEngine()" in source
    assert "TranslationOrchestrator" in source
    
    # Should have all pipeline methods
    assert "execute_full_pipeline" in source
    assert "execute_validation_pipeline" in source
    assert "execute_optimization_pipeline" in source
