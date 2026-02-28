"""Simple API tests without complex mocking."""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


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
    assert data["components"]["api"] == "operational"
    assert data["components"]["validation"] == "operational"
    assert data["components"]["audit"] == "operational"


def test_openapi_docs():
    """Test OpenAPI documentation is accessible."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "paths" in openapi_spec
    assert "/api/v1/upload_repo" in openapi_spec["paths"]
    assert "/api/v1/translate" in openapi_spec["paths"]
    assert "/api/v1/dependency_graph/{repository_id}" in openapi_spec["paths"]
    assert "/api/v1/report/{repository_id}" in openapi_spec["paths"]


def test_upload_repo_no_file():
    """Test upload endpoint with no file."""
    response = client.post("/api/v1/upload_repo")
    assert response.status_code == 400
    assert "No file provided" in response.json()["detail"]


def test_upload_repo_invalid_file_type():
    """Test upload endpoint with invalid file type."""
    import io
    files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
    response = client.post("/api/v1/upload_repo", files=files)
    assert response.status_code == 400
    assert "ZIP" in response.json()["detail"]


def test_translate_repository_not_found():
    """Test translate endpoint with non-existent repository."""
    response = client.post(
        "/api/v1/translate",
        json={"repository_id": "nonexistent", "target_language": "python"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_dependency_graph_not_found():
    """Test get dependency graph with non-existent repository."""
    response = client.get("/api/v1/dependency_graph/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_report_not_found():
    """Test get report with non-existent repository."""
    response = client.get("/api/v1/report/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_schema_validation_invalid_language():
    """Test API schema validation with invalid target language."""
    response = client.post(
        "/api/v1/translate",
        json={"repository_id": "test", "target_language": "invalid"}
    )
    assert response.status_code == 422  # Validation error


def test_api_schema_validation_missing_field():
    """Test API schema validation with missing required field."""
    response = client.post(
        "/api/v1/translate",
        json={"target_language": "python"}
    )
    assert response.status_code == 422  # Validation error


def test_api_schemas_are_documented():
    """Test that all schemas are properly documented in OpenAPI."""
    response = client.get("/api/openapi.json")
    openapi_spec = response.json()
    
    # Check components/schemas exist
    assert "components" in openapi_spec
    assert "schemas" in openapi_spec["components"]
    
    schemas = openapi_spec["components"]["schemas"]
    
    # Check key schemas are defined
    assert "UploadRepoResponse" in schemas
    assert "TranslateRequest" in schemas
    assert "TranslateResponse" in schemas
    assert "DependencyGraphResponse" in schemas
    assert "ReportResponse" in schemas
    assert "ErrorResponse" in schemas


def test_api_endpoints_have_tags():
    """Test that all endpoints have proper tags."""
    response = client.get("/api/openapi.json")
    openapi_spec = response.json()
    
    # Check paths have tags
    for path, methods in openapi_spec["paths"].items():
        for method, details in methods.items():
            if method != "parameters":
                assert "tags" in details, f"{method.upper()} {path} missing tags"


def test_api_endpoints_have_descriptions():
    """Test that all endpoints have descriptions."""
    response = client.get("/api/openapi.json")
    openapi_spec = response.json()
    
    # Check paths have descriptions
    for path, methods in openapi_spec["paths"].items():
        for method, details in methods.items():
            if method != "parameters":
                assert "summary" in details, f"{method.upper()} {path} missing summary"
                assert "description" in details, f"{method.upper()} {path} missing description"
