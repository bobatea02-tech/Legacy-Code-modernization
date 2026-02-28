"""Tests for CLI module."""

import pytest
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import zipfile

from app.cli.cli import app


runner = CliRunner()


@pytest.fixture
def sample_java_zip(tmp_path):
    """Create a sample Java ZIP file for testing."""
    # Create temporary directory with Java file
    java_dir = tmp_path / "sample"
    java_dir.mkdir()
    
    java_file = java_dir / "Calculator.java"
    java_file.write_text("""
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
""")
    
    # Create ZIP file
    zip_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(java_file, arcname="Calculator.java")
    
    return zip_path


def test_cli_help():
    """Test CLI help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Legacy Code Modernization Engine" in result.stdout


def test_ingest_command_help():
    """Test ingest command help."""
    result = runner.invoke(app, ["ingest", "--help"])
    assert result.exit_code == 0
    assert "Ingest repository" in result.stdout


def test_optimize_command_help():
    """Test optimize command help."""
    result = runner.invoke(app, ["optimize", "--help"])
    assert result.exit_code == 0
    assert "AST parsing" in result.stdout


def test_translate_command_help():
    """Test translate command help."""
    result = runner.invoke(app, ["translate", "--help"])
    assert result.exit_code == 0
    assert "translation pipeline" in result.stdout


def test_validate_command_help():
    """Test validate command help."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Validate repository" in result.stdout


def test_ingest_nonexistent_path():
    """Test ingest with nonexistent path."""
    result = runner.invoke(app, ["ingest", "/nonexistent/path.zip"])
    assert result.exit_code == 1
    assert "does not exist" in result.stdout


def test_ingest_command(sample_java_zip):
    """Test ingest command with sample ZIP."""
    result = runner.invoke(app, ["ingest", str(sample_java_zip)])
    
    # Should succeed
    assert result.exit_code == 0
    assert "Ingestion complete" in result.stdout
    assert "Files processed:" in result.stdout


def test_ingest_command_verbose(sample_java_zip):
    """Test ingest command with verbose flag."""
    result = runner.invoke(app, ["ingest", str(sample_java_zip), "--verbose"])
    
    # Should succeed and show file details
    assert result.exit_code == 0
    assert "File Details:" in result.stdout
    assert "Calculator.java" in result.stdout


def test_optimize_command(sample_java_zip):
    """Test optimize command with sample ZIP."""
    result = runner.invoke(app, ["optimize", str(sample_java_zip), "--language", "java"])
    
    # Should succeed
    assert result.exit_code == 0
    assert "Optimization Complete" in result.stdout
    assert "AST Nodes:" in result.stdout


def test_validate_command(sample_java_zip):
    """Test validate command with sample ZIP."""
    result = runner.invoke(app, ["validate", str(sample_java_zip), "--language", "java"])
    
    # Should succeed
    assert result.exit_code == 0
    assert "Validation Complete" in result.stdout
    assert "AST Nodes:" in result.stdout


def test_cli_error_handling():
    """Test CLI error handling with invalid input."""
    # Test with non-ZIP file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"not a zip file")
        temp_path = f.name
    
    result = runner.invoke(app, ["ingest", temp_path])
    assert result.exit_code == 1
    
    # Cleanup
    Path(temp_path).unlink()


def test_cli_commands_exist():
    """Test that all required commands exist."""
    result = runner.invoke(app, ["--help"])
    
    assert "ingest" in result.stdout
    assert "optimize" in result.stdout
    assert "translate" in result.stdout
    assert "validate" in result.stdout
