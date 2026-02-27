"""Tests for repository ingestion module."""

import tempfile
import zipfile
from pathlib import Path

import pytest

from app.ingestion.ingestor import (
    ArchiveSizeExceededError,
    FileCountExceededError,
    FileSizeExceededError,
    IngestionConfig,
    PathTraversalError,
    RepositoryIngestor,
)


@pytest.fixture
def sample_java_file():
    """Sample Java source code."""
    return """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
""".strip()


@pytest.fixture
def sample_c_file():
    """Sample C source code."""
    return """
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
""".strip()


@pytest.fixture
def create_test_zip(tmp_path, sample_java_file, sample_c_file):
    """Create a test ZIP file with sample source files."""
    def _create_zip(include_traversal=False, large_file=False):
        zip_path = tmp_path / "test_repo.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add Java file
            zf.writestr("src/HelloWorld.java", sample_java_file)
            
            # Add C file
            zf.writestr("src/main.c", sample_c_file)
            
            # Add file in subdirectory
            zf.writestr("src/utils/Helper.java", "public class Helper {}")
            
            # Add files that should be ignored
            zf.writestr("node_modules/package.json", "{}")
            zf.writestr(".git/config", "")
            zf.writestr("build/output.class", "binary")
            zf.writestr(".hidden", "hidden")
            
            # Add path traversal attempt if requested
            if include_traversal:
                zf.writestr("../../../etc/passwd", "malicious")
            
            # Add large file if requested
            if large_file:
                large_content = "x" * (11 * 1024 * 1024)  # 11MB
                zf.writestr("src/Large.java", large_content)
        
        return zip_path
    
    return _create_zip


def test_basic_ingestion(create_test_zip):
    """Test basic ZIP ingestion with valid files."""
    zip_path = create_test_zip()
    
    with RepositoryIngestor() as ingestor:
        files = ingestor.ingest_zip(str(zip_path))
        
        # Should have 3 valid source files (2 Java, 1 C)
        assert len(files) == 3
        
        # Check files are sorted by relative path
        relative_paths = [f.relative_path for f in files]
        assert relative_paths == sorted(relative_paths)
        
        # Verify metadata fields
        for file_meta in files:
            assert file_meta.path.exists()
            assert file_meta.language in ['java', 'c']
            assert file_meta.size > 0
            assert len(file_meta.sha256) == 64  # SHA256 hex length
            assert file_meta.encoding
            assert file_meta.relative_path


def test_language_detection(create_test_zip):
    """Test language detection from file extensions."""
    zip_path = create_test_zip()
    
    with RepositoryIngestor() as ingestor:
        files = ingestor.ingest_zip(str(zip_path))
        
        java_files = [f for f in files if f.language == 'java']
        c_files = [f for f in files if f.language == 'c']
        
        assert len(java_files) == 2
        assert len(c_files) == 1


def test_ignored_directories(create_test_zip):
    """Test that ignored directories are skipped."""
    zip_path = create_test_zip()
    
    with RepositoryIngestor() as ingestor:
        files = ingestor.ingest_zip(str(zip_path))
        
        # Verify no files from ignored directories
        for file_meta in files:
            path_parts = Path(file_meta.relative_path).parts
            assert 'node_modules' not in path_parts
            assert '.git' not in path_parts
            assert 'build' not in path_parts


def test_hidden_files_ignored(create_test_zip):
    """Test that hidden files are ignored."""
    zip_path = create_test_zip()
    
    with RepositoryIngestor() as ingestor:
        files = ingestor.ingest_zip(str(zip_path))
        
        # Verify no hidden files
        for file_meta in files:
            filename = Path(file_meta.relative_path).name
            assert not filename.startswith('.')


def test_path_traversal_protection(create_test_zip):
    """Test protection against path traversal attacks."""
    zip_path = create_test_zip(include_traversal=True)
    
    with RepositoryIngestor() as ingestor:
        with pytest.raises(PathTraversalError):
            ingestor.ingest_zip(str(zip_path))


def test_file_size_limit(create_test_zip):
    """Test that files exceeding size limit are skipped."""
    zip_path = create_test_zip(large_file=True)
    
    with RepositoryIngestor() as ingestor:
        files = ingestor.ingest_zip(str(zip_path))
        
        # Large file should be skipped, only 3 normal files
        assert len(files) == 3


def test_custom_config():
    """Test custom configuration."""
    config = IngestionConfig()
    config.MAX_FILE_SIZE_MB = 1
    config.MAX_FILE_COUNT = 5
    
    ingestor = RepositoryIngestor(config=config)
    assert ingestor.config.MAX_FILE_SIZE_MB == 1
    assert ingestor.config.MAX_FILE_COUNT == 5


def test_sha256_deterministic(create_test_zip):
    """Test that SHA256 hashes are deterministic."""
    zip_path = create_test_zip()
    
    with RepositoryIngestor() as ingestor:
        files1 = ingestor.ingest_zip(str(zip_path))
    
    with RepositoryIngestor() as ingestor:
        files2 = ingestor.ingest_zip(str(zip_path))
    
    # Same files should have same hashes
    hashes1 = {f.relative_path: f.sha256 for f in files1}
    hashes2 = {f.relative_path: f.sha256 for f in files2}
    
    assert hashes1 == hashes2


def test_cleanup(create_test_zip):
    """Test that temporary directory is cleaned up."""
    zip_path = create_test_zip()
    
    ingestor = RepositoryIngestor()
    files = ingestor.ingest_zip(str(zip_path))
    
    temp_dir = ingestor.temp_dir
    assert temp_dir.exists()
    
    ingestor.cleanup()
    assert not temp_dir.exists()


def test_context_manager_cleanup(create_test_zip):
    """Test cleanup via context manager."""
    zip_path = create_test_zip()
    temp_dir = None
    
    with RepositoryIngestor() as ingestor:
        files = ingestor.ingest_zip(str(zip_path))
        temp_dir = ingestor.temp_dir
        assert temp_dir.exists()
    
    # Should be cleaned up after context exit
    assert not temp_dir.exists()
