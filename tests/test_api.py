"""Tests for API layer."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io

from app.api.main import app
from app.ingestion.ingestor import FileMetadata
from app.parsers.base import ASTNode
from app.validation import ValidationReport
from app.audit import AuditReport, CheckResult

client = TestClient(app)


@pytest.fixture
def mock_file_metadata():
    """Create mock file metadata."""
    from pathlib import Path
    return FileMetadata(
        path=Path("/tmp/test.java"),
        language="java",
        size=1000,
        sha256="abc123",
        encoding="utf-8",
        relative_path="src/test.java"
    )


@pytest.fixture
def mock_ast_node():
    """Create mock AST node."""
    return ASTNode(
        id="test_001",
        name="testFunction",
        node_type="function",
        parameters=["param1"],
        return_type="int",
        called_symbols=["helper"],
        imports=["java.util"],
        file_path="test.java",
        start_line=10,
        end_line=20,
        raw_source="public int testFunction(String param1) { return 0; }"
    )


@pytest.fixture
def mock_validation_report():
    """Create mock validation report."""
    return ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test_example(): pass",
        errors=[]
    )


@pytest.fixture
def mock_audit_report():
    """Create mock audit report."""
    return AuditReport(
        overall_passed=True,
        total_checks=13,
        passed_checks=13,
        failed_checks=0,
        check_results=[
            CheckResult(
                check_name="Test Check",
                passed=True,
                message="Check passed",
                details={},
                warnings=[]
            )
        ],
        execution_time_ms=1.5,
        timestamp="2024-01-01 00:00:00",
        summary="All checks passed"
    )


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "components" in data


@patch('app.api.routes.get_ingestion_service')
def test_upload_repo_no_file(mock_get_ingestor):
    """Test upload endpoint with no file."""
    response = client.post("/api/v1/upload_repo")
    assert response.status_code == 400  # Bad request - no file provided


@patch('app.api.routes.get_ingestion_service')
def test_upload_repo_invalid_file_type(mock_get_ingestor):
    """Test upload endpoint with invalid file type."""
    files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
    response = client.post("/api/v1/upload_repo", files=files)
    assert response.status_code == 400
    assert "ZIP" in response.json()["detail"]


@patch('app.api.routes.get_ingestion_service')
@patch('app.api.routes.get_storage')
def test_upload_repo_success(mock_get_storage, mock_get_ingestor, mock_file_metadata):
    """Test successful repository upload."""
    # Mock ingestor
    mock_ingestor = Mock()
    mock_ingestor.ingest_zip.return_value = [mock_file_metadata]
    mock_ingestor.cleanup = Mock()
    mock_get_ingestor.return_value = mock_ingestor
    
    # Mock storage
    mock_storage = Mock()
    mock_storage.store_repository = Mock()
    mock_get_storage.return_value = mock_storage
    
    # Create test ZIP file
    files = {"file": ("test.zip", io.BytesIO(b"PK\x03\x04"), "application/zip")}
    
    response = client.post("/api/v1/upload_repo", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "repository_id" in data
    assert data["file_count"] == 1
    assert len(data["files"]) == 1


@patch('app.api.routes.get_storage')
def test_translate_repository_not_found(mock_get_storage):
    """Test translate endpoint with non-existent repository."""
    mock_storage = Mock()
    mock_storage.has_repository.return_value = False
    mock_get_storage.return_value = mock_storage
    
    response = client.post(
        "/api/v1/translate",
        json={"repository_id": "nonexistent", "target_language": "python"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@patch('app.api.routes.get_storage')
@patch('app.api.routes.get_graph_builder')
@patch('app.api.routes.get_translation_service')
@patch('app.api.routes.get_validation_engine')
@patch('app.api.routes.get_audit_engine')
@patch('app.api.routes.get_parser')
def test_translate_success(
    mock_get_parser,
    mock_get_audit,
    mock_get_validation,
    mock_get_translation,
    mock_get_graph,
    mock_get_storage,
    mock_ast_node,
    mock_validation_report,
    mock_audit_report
):
    """Test successful translation pipeline."""
    # Mock storage
    mock_storage = Mock()
    mock_storage.has_repository.return_value = True
    mock_storage.get_repository.return_value = {
        "file_metadata": [
            Mock(
                language="java",
                path="/tmp/test.java",
                relative_path="test.java"
            )
        ]
    }
    mock_storage.store_graph = Mock()
    mock_storage.store_translations = Mock()
    mock_storage.store_validations = Mock()
    mock_storage.store_documentation = Mock()
    mock_storage.store_audit = Mock()
    mock_get_storage.return_value = mock_storage
    
    # Mock parser
    mock_parser = Mock()
    mock_parser.parse_file.return_value = [mock_ast_node]
    mock_get_parser.return_value = mock_parser
    
    # Mock graph builder
    mock_graph = Mock()
    mock_graph_obj = MagicMock()
    mock_graph_obj.number_of_nodes.return_value = 1
    mock_graph_obj.number_of_edges.return_value = 0
    mock_graph.build_graph.return_value = mock_graph_obj
    mock_graph.export_json.return_value = {"nodes": [], "edges": []}
    mock_get_graph.return_value = mock_graph
    
    # Mock translation service
    mock_translation = Mock()
    mock_trans_result = Mock()
    mock_trans_result.module_name = "test_001"
    mock_trans_result.status = Mock(value="success")
    mock_trans_result.translated_code = "def test(): pass"
    mock_trans_result.dependencies_used = []
    mock_trans_result.token_usage = 100
    mock_trans_result.errors = []
    mock_trans_result.warnings = []
    mock_translation.translate_repository = Mock(return_value=[mock_trans_result])
    mock_translation.get_translation_statistics.return_value = {
        "total_modules": 1,
        "successful": 1,
        "failed": 0
    }
    mock_get_translation.return_value = mock_translation
    
    # Mock validation engine
    mock_validation = Mock()
    mock_validation.validate_translation.return_value = mock_validation_report
    mock_get_validation.return_value = mock_validation
    
    # Mock audit engine
    mock_audit = Mock()
    mock_audit.run_audit.return_value = mock_audit_report
    mock_get_audit.return_value = mock_audit
    
    # Make request
    response = client.post(
        "/api/v1/translate",
        json={"repository_id": "test_repo", "target_language": "python"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["repository_id"] == "test_repo"
    assert len(data["modules"]) == 1
    assert "statistics" in data


@patch('app.api.routes.get_storage')
def test_get_dependency_graph_not_found(mock_get_storage):
    """Test get dependency graph with non-existent repository."""
    mock_storage = Mock()
    mock_storage.has_repository.return_value = False
    mock_get_storage.return_value = mock_storage
    
    response = client.get("/api/v1/dependency_graph/nonexistent")
    
    assert response.status_code == 404


@patch('app.api.routes.get_storage')
@patch('app.api.routes.get_graph_builder')
def test_get_dependency_graph_success(mock_get_graph, mock_get_storage):
    """Test successful dependency graph retrieval."""
    # Mock storage
    mock_storage = Mock()
    mock_storage.has_repository.return_value = True
    mock_storage.get_graph.return_value = {
        "nodes": [
            {
                "id": "node1",
                "name": "test",
                "node_type": "function",
                "file_path": "test.java",
                "start_line": 1,
                "end_line": 10
            }
        ],
        "edges": [
            {
                "source": "node1",
                "target": "node2",
                "edge_type": "calls"
            }
        ]
    }
    mock_get_storage.return_value = mock_storage
    
    response = client.get("/api/v1/dependency_graph/test_repo")
    
    assert response.status_code == 200
    data = response.json()
    assert data["repository_id"] == "test_repo"
    assert len(data["nodes"]) == 1
    assert len(data["edges"]) == 1
    assert "statistics" in data


@patch('app.api.routes.get_storage')
def test_get_report_not_found(mock_get_storage):
    """Test get report with non-existent repository."""
    mock_storage = Mock()
    mock_storage.has_repository.return_value = False
    mock_get_storage.return_value = mock_storage
    
    response = client.get("/api/v1/report/nonexistent")
    
    assert response.status_code == 404


@patch('app.api.routes.get_storage')
def test_get_report_success(mock_get_storage, mock_validation_report):
    """Test successful report retrieval."""
    # Mock storage
    mock_storage = Mock()
    mock_storage.has_repository.return_value = True
    mock_storage.get_validations.return_value = [mock_validation_report]
    mock_storage.get_audit.return_value = {
        "overall_passed": True,
        "total_checks": 13,
        "passed_checks": 13,
        "failed_checks": 0,
        "execution_time_ms": 1.5,
        "check_results": [
            Mock(
                check_name="Test",
                passed=True,
                message="OK",
                warnings=[]
            )
        ]
    }
    mock_storage.get_documentation.return_value = {
        "module1": "# Documentation"
    }
    mock_storage.get_translations.return_value = []
    mock_get_storage.return_value = mock_storage
    
    response = client.get("/api/v1/report/test_repo")
    
    assert response.status_code == 200
    data = response.json()
    assert data["repository_id"] == "test_repo"
    assert "validation_summary" in data
    assert "audit_summary" in data
    assert "documentation" in data
    assert "statistics" in data


def test_api_schema_validation():
    """Test API schema validation."""
    # Test invalid target language
    response = client.post(
        "/api/v1/translate",
        json={"repository_id": "test", "target_language": "invalid"}
    )
    assert response.status_code == 422  # Validation error
    
    # Test missing required field
    response = client.post(
        "/api/v1/translate",
        json={"target_language": "python"}
    )
    assert response.status_code == 422  # Validation error


def test_openapi_docs():
    """Test OpenAPI documentation is accessible."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "paths" in openapi_spec
    assert "/api/v1/upload_repo" in openapi_spec["paths"]
    assert "/api/v1/translate" in openapi_spec["paths"]
