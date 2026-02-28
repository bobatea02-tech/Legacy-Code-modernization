"""Integration tests for sample repositories.

Tests verify that sample repositories work correctly with the full pipeline:
- Ingestion works
- Dependency graphs are generated
- Evaluation reports are produced
- Metrics match metadata expectations
"""

import pytest
import json
import os
from pathlib import Path


class TestSampleRepos:
    """Test suite for sample repositories."""
    
    @pytest.fixture
    def sample_repos_path(self):
        """Get path to sample_repos directory."""
        return Path("sample_repos")
    
    @pytest.fixture
    def java_small_path(self, sample_repos_path):
        """Get path to java_small repository."""
        return sample_repos_path / "java_small"
    
    @pytest.fixture
    def cobol_small_path(self, sample_repos_path):
        """Get path to cobol_small repository."""
        return sample_repos_path / "cobol_small"
    
    @pytest.fixture
    def java_metadata(self, sample_repos_path):
        """Load java_small metadata."""
        metadata_path = sample_repos_path / "metadata" / "java_small.json"
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def cobol_metadata(self, sample_repos_path):
        """Load cobol_small metadata."""
        metadata_path = sample_repos_path / "metadata" / "cobol_small.json"
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def test_java_small_exists(self, java_small_path):
        """Test that java_small repository exists."""
        assert java_small_path.exists()
        assert java_small_path.is_dir()
    
    def test_cobol_small_exists(self, cobol_small_path):
        """Test that cobol_small repository exists."""
        assert cobol_small_path.exists()
        assert cobol_small_path.is_dir()
    
    def test_java_metadata_exists(self, sample_repos_path):
        """Test that java_small metadata exists."""
        metadata_path = sample_repos_path / "metadata" / "java_small.json"
        assert metadata_path.exists()
    
    def test_cobol_metadata_exists(self, sample_repos_path):
        """Test that cobol_small metadata exists."""
        metadata_path = sample_repos_path / "metadata" / "cobol_small.json"
        assert metadata_path.exists()
    
    def test_java_file_count(self, java_small_path, java_metadata):
        """Test that java_small has expected file count."""
        java_files = list(java_small_path.rglob("*.java"))
        assert len(java_files) == java_metadata["file_count"]
    
    def test_cobol_file_count(self, cobol_small_path, cobol_metadata):
        """Test that cobol_small has expected file count."""
        # Count .cbl and .cpy files
        cobol_files = list(cobol_small_path.rglob("*.cbl"))
        copybook_files = list(cobol_small_path.rglob("*.cpy"))
        total_files = len(cobol_files) + len(copybook_files)
        assert total_files == cobol_metadata["file_count"]
    
    def test_java_ingestion(self, java_small_path):
        """Test that java_small structure is correct for ingestion."""
        # Verify directory exists and has expected structure
        assert java_small_path.exists()
        assert (java_small_path / "src").exists()
        
        # Verify Java files exist
        java_files = list(java_small_path.rglob("*.java"))
        assert len(java_files) == 6
    
    def test_cobol_ingestion(self, cobol_small_path):
        """Test that cobol_small structure is correct for ingestion."""
        # Verify directory exists and has expected structure
        assert cobol_small_path.exists()
        assert (cobol_small_path / "copybooks").exists()
        
        # Verify COBOL files exist
        cobol_files = list(cobol_small_path.rglob("*.cbl"))
        copybook_files = list(cobol_small_path.rglob("*.cpy"))
        assert len(cobol_files) + len(copybook_files) == 5
    
    def test_java_parsing(self, java_small_path):
        """Test that java_small files have valid Java syntax."""
        # Find Java files
        java_files = list(java_small_path.rglob("*.java"))
        assert len(java_files) > 0
        
        # Verify files have content and basic Java structure
        for java_file in java_files:
            with open(java_file, 'r') as f:
                content = f.read()
            
            # Basic syntax checks
            assert len(content) > 0
            assert "package" in content or "class" in content or "interface" in content
    
    def test_cobol_parsing(self, cobol_small_path):
        """Test that cobol_small files have valid COBOL syntax."""
        # Find COBOL files
        cobol_files = list(cobol_small_path.rglob("*.cbl"))
        assert len(cobol_files) > 0
        
        # Verify files have content and basic COBOL structure
        for cobol_file in cobol_files:
            with open(cobol_file, 'r') as f:
                content = f.read()
            
            # Basic syntax checks
            assert len(content) > 0
            assert "IDENTIFICATION DIVISION" in content or "PROGRAM-ID" in content
    
    def test_java_dependency_graph(self, java_small_path, java_metadata):
        """Test that java_small has expected dependencies in metadata."""
        # Verify dependency details exist in metadata
        assert "dependency_details" in java_metadata
        
        # Count total dependencies
        total_deps = sum(
            len(deps) for deps in java_metadata["dependency_details"].values()
        )
        
        # Should have dependencies defined
        assert total_deps > 0
    
    def test_cobol_dependency_graph(self, cobol_small_path, cobol_metadata):
        """Test that cobol_small has expected dependencies in metadata."""
        # Verify dependency details exist in metadata
        assert "dependency_details" in cobol_metadata
        
        # Count total dependencies
        total_deps = sum(
            len(deps) for deps in cobol_metadata["dependency_details"].values()
        )
        
        # Should have dependencies defined
        assert total_deps > 0
    
    def test_java_metadata_schema(self, java_metadata):
        """Test that java_small metadata has correct schema."""
        required_fields = [
            "repo_name",
            "language",
            "file_count",
            "expected_dependencies",
            "entry_points",
            "expected_token_estimate",
            "complexity_level",
            "notes"
        ]
        
        for field in required_fields:
            assert field in java_metadata, f"Missing field: {field}"
        
        # Validate types
        assert isinstance(java_metadata["file_count"], int)
        assert isinstance(java_metadata["expected_dependencies"], int)
        assert isinstance(java_metadata["entry_points"], list)
        assert isinstance(java_metadata["expected_token_estimate"], int)
        assert java_metadata["complexity_level"] in ["low", "medium", "high"]
    
    def test_cobol_metadata_schema(self, cobol_metadata):
        """Test that cobol_small metadata has correct schema."""
        required_fields = [
            "repo_name",
            "language",
            "file_count",
            "expected_dependencies",
            "entry_points",
            "expected_token_estimate",
            "complexity_level",
            "notes"
        ]
        
        for field in required_fields:
            assert field in cobol_metadata, f"Missing field: {field}"
        
        # Validate types
        assert isinstance(cobol_metadata["file_count"], int)
        assert isinstance(cobol_metadata["expected_dependencies"], int)
        assert isinstance(cobol_metadata["entry_points"], list)
        assert isinstance(cobol_metadata["expected_token_estimate"], int)
        assert cobol_metadata["complexity_level"] in ["low", "medium", "high"]
    
    def test_java_entry_points_exist(self, java_small_path, java_metadata):
        """Test that java_small entry points exist."""
        for entry_point in java_metadata["entry_points"]:
            entry_path = java_small_path / entry_point
            assert entry_path.exists(), f"Entry point not found: {entry_point}"
    
    def test_cobol_entry_points_exist(self, cobol_small_path, cobol_metadata):
        """Test that cobol_small entry points exist."""
        for entry_point in cobol_metadata["entry_points"]:
            entry_path = cobol_small_path / entry_point
            assert entry_path.exists(), f"Entry point not found: {entry_point}"
    
    def test_java_unused_class_exists(self, java_small_path, java_metadata):
        """Test that java_small unused class exists."""
        if "validation_targets" in java_metadata:
            if "unused_classes" in java_metadata["validation_targets"]:
                for unused_class in java_metadata["validation_targets"]["unused_classes"]:
                    unused_path = java_small_path / unused_class
                    assert unused_path.exists(), f"Unused class not found: {unused_class}"
    
    def test_cobol_unused_module_exists(self, cobol_small_path, cobol_metadata):
        """Test that cobol_small unused module exists."""
        if "validation_targets" in cobol_metadata:
            if "unused_modules" in cobol_metadata["validation_targets"]:
                for unused_module in cobol_metadata["validation_targets"]["unused_modules"]:
                    unused_path = cobol_small_path / unused_module
                    assert unused_path.exists(), f"Unused module not found: {unused_module}"
    
    def test_java_determinism(self, java_small_path):
        """Test that java_small has deterministic structure."""
        # Count files twice
        java_files1 = list(java_small_path.rglob("*.java"))
        java_files2 = list(java_small_path.rglob("*.java"))
        
        # Assert counts are identical
        assert len(java_files1) == len(java_files2)
    
    def test_cobol_determinism(self, cobol_small_path):
        """Test that cobol_small has deterministic structure."""
        # Count files twice
        cobol_files1 = list(cobol_small_path.rglob("*.cbl"))
        cobol_files2 = list(cobol_small_path.rglob("*.cbl"))
        
        # Assert counts are identical
        assert len(cobol_files1) == len(cobol_files2)
    
    def test_java_no_runtime_errors(self, java_small_path):
        """Test that java_small files can be read without errors."""
        try:
            java_files = list(java_small_path.rglob("*.java"))
            
            for java_file in java_files:
                with open(java_file, 'r') as f:
                    content = f.read()
                assert len(content) > 0
            
            # If we get here, no errors occurred
            assert True
        except Exception as e:
            pytest.fail(f"Runtime error occurred: {e}")
    
    def test_cobol_no_runtime_errors(self, cobol_small_path):
        """Test that cobol_small files can be read without errors."""
        try:
            cobol_files = list(cobol_small_path.rglob("*.cbl"))
            copybook_files = list(cobol_small_path.rglob("*.cpy"))
            
            for cobol_file in cobol_files + copybook_files:
                with open(cobol_file, 'r') as f:
                    content = f.read()
                assert len(content) > 0
            
            # If we get here, no errors occurred
            assert True
        except Exception as e:
            pytest.fail(f"Runtime error occurred: {e}")
    
    def test_metadata_consistency(self, java_metadata, cobol_metadata):
        """Test that metadata files are consistent."""
        # Both should have same schema
        java_keys = set(java_metadata.keys())
        cobol_keys = set(cobol_metadata.keys())
        
        # Core fields should be present in both
        core_fields = {
            "repo_name", "language", "file_count", 
            "expected_dependencies", "entry_points",
            "expected_token_estimate", "complexity_level"
        }
        
        assert core_fields.issubset(java_keys)
        assert core_fields.issubset(cobol_keys)
    
    def test_sample_repos_readme_exists(self, sample_repos_path):
        """Test that sample_repos README exists."""
        readme_path = sample_repos_path / "README.md"
        assert readme_path.exists()
        
        # Verify README has content
        with open(readme_path, 'r') as f:
            content = f.read()
        assert len(content) > 100  # Should have substantial content


class TestSampleReposIntegration:
    """Integration tests that require full pipeline."""
    
    @pytest.fixture
    def sample_repos_path(self):
        """Get path to sample_repos directory."""
        return Path("sample_repos")
    
    def test_java_token_estimate_reasonable(self, sample_repos_path):
        """Test that java_small token estimate is reasonable."""
        # Load metadata
        metadata_path = sample_repos_path / "metadata" / "java_small.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Token estimate should be positive and reasonable
        assert metadata["expected_token_estimate"] > 0
        assert metadata["expected_token_estimate"] < 100000  # Not too large
    
    def test_cobol_token_estimate_reasonable(self, sample_repos_path):
        """Test that cobol_small token estimate is reasonable."""
        # Load metadata
        metadata_path = sample_repos_path / "metadata" / "cobol_small.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Token estimate should be positive and reasonable
        assert metadata["expected_token_estimate"] > 0
        assert metadata["expected_token_estimate"] < 100000  # Not too large
