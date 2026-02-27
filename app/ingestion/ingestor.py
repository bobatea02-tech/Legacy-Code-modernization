"""Repository ingestion module with security and validation.

This module handles safe extraction and processing of repository archives:
- ZIP file extraction with path traversal protection
- Size and file count limits enforcement
- Language detection and file filtering
- Encoding normalization
- SHA256 hashing for reproducibility
"""

import hashlib
import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

import chardet

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FileMetadata:
    """Metadata for an ingested source file."""
    
    path: Path  # Absolute path to extracted file
    language: str  # Detected language (java, c, cobol)
    size: int  # File size in bytes
    sha256: str  # SHA256 hash of file content
    encoding: str  # Detected/normalized encoding
    relative_path: str  # Path relative to repository root


class IngestionConfig:
    """Configuration for repository ingestion limits and rules."""
    
    # Size limits
    MAX_ARCHIVE_SIZE_MB: int = 500
    MAX_FILE_SIZE_MB: int = 10
    MAX_FILE_COUNT: int = 10000
    
    # Supported languages with their extensions
    LANGUAGE_EXTENSIONS: dict = {
        '.java': 'java',
        '.c': 'c',
        '.h': 'c',
        '.cbl': 'cobol',
        '.cob': 'cobol',
        '.cpy': 'cobol',
    }
    
    # Directories to ignore
    IGNORED_DIRS: Set[str] = {
        'node_modules',
        'target',
        '.git',
        'dist',
        'build',
        '__pycache__',
        '.idea',
        '.vscode',
        'vendor',
        'venv',
        '.env',
    }
    
    # File patterns to ignore
    IGNORED_PATTERNS: Set[str] = {
        '.class',
        '.jar',
        '.war',
        '.ear',
        '.zip',
        '.tar',
        '.gz',
        '.exe',
        '.dll',
        '.so',
        '.dylib',
        '.o',
        '.a',
        '.pyc',
        '.pyo',
    }


class IngestionError(Exception):
    """Base exception for ingestion errors."""
    pass


class ArchiveSizeExceededError(IngestionError):
    """Raised when archive size exceeds limit."""
    pass


class FileSizeExceededError(IngestionError):
    """Raised when individual file size exceeds limit."""
    pass


class FileCountExceededError(IngestionError):
    """Raised when file count exceeds limit."""
    pass


class PathTraversalError(IngestionError):
    """Raised when path traversal attack is detected."""
    pass


class RepositoryIngestor:
    """Handles safe extraction and processing of repository archives."""
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        """Initialize ingestor with configuration.
        
        Args:
            config: Optional custom configuration (uses defaults if None)
        """
        self.config = config or IngestionConfig()
        self.temp_dir: Optional[Path] = None
        logger.info("RepositoryIngestor initialized")
    
    def ingest_zip(self, zip_path: str) -> List[FileMetadata]:
        """Ingest a ZIP archive and return file metadata.
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            Sorted list of FileMetadata for all valid source files
            
        Raises:
            IngestionError: On validation or extraction failures
        """
        zip_file_path = Path(zip_path)
        
        if not zip_file_path.exists():
            raise IngestionError(f"ZIP file not found: {zip_path}")
        
        if not zip_file_path.is_file():
            raise IngestionError(f"Path is not a file: {zip_path}")
        
        logger.info(f"Starting ingestion of: {zip_path}")
        
        # Validate archive size
        self._validate_archive_size(zip_file_path)
        
        # Create temporary extraction directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="repo_ingest_"))
        logger.debug(f"Created temp directory: {self.temp_dir}")
        
        try:
            # Extract archive safely
            self._extract_archive(zip_file_path, self.temp_dir)
            
            # Process extracted files
            file_metadata = self._process_files(self.temp_dir)
            
            # Sort for deterministic output
            file_metadata.sort(key=lambda f: f.relative_path)
            
            logger.info(f"Ingestion complete: {len(file_metadata)} files processed")
            return file_metadata
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            raise
    
    def _validate_archive_size(self, zip_path: Path) -> None:
        """Validate archive size is within limits.
        
        Args:
            zip_path: Path to ZIP file
            
        Raises:
            ArchiveSizeExceededError: If archive exceeds size limit
        """
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        max_size = self.config.MAX_ARCHIVE_SIZE_MB
        
        if size_mb > max_size:
            raise ArchiveSizeExceededError(
                f"Archive size {size_mb:.2f}MB exceeds limit of {max_size}MB"
            )
        
        logger.debug(f"Archive size: {size_mb:.2f}MB (within limit)")
    
    def _extract_archive(self, zip_path: Path, extract_to: Path) -> None:
        """Safely extract ZIP archive with path traversal protection.
        
        Args:
            zip_path: Path to ZIP file
            extract_to: Destination directory
            
        Raises:
            PathTraversalError: If path traversal is detected
            IngestionError: On extraction failures
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Validate all paths before extraction (Zip Slip protection)
                for member in zf.namelist():
                    self._validate_member_path(member, extract_to)
                
                # Extract all files
                zf.extractall(extract_to)
                logger.debug(f"Extracted {len(zf.namelist())} entries")
                
        except zipfile.BadZipFile as e:
            raise IngestionError(f"Invalid ZIP file: {e}")
        except PathTraversalError:
            # Re-raise PathTraversalError as-is
            raise
        except Exception as e:
            raise IngestionError(f"Extraction failed: {e}")
    
    def _validate_member_path(self, member_name: str, extract_to: Path) -> None:
        """Validate ZIP member path to prevent path traversal attacks.
        
        Args:
            member_name: Name of ZIP member
            extract_to: Extraction destination
            
        Raises:
            PathTraversalError: If path traversal is detected
        """
        # Resolve the full path and ensure it's within extraction directory
        member_path = (extract_to / member_name).resolve()
        extract_path = extract_to.resolve()
        
        # Check if resolved path is within extraction directory
        try:
            member_path.relative_to(extract_path)
        except ValueError:
            raise PathTraversalError(
                f"Path traversal detected in ZIP member: {member_name}"
            )
    
    def _process_files(self, root_dir: Path) -> List[FileMetadata]:
        """Process all files in extracted directory.
        
        Args:
            root_dir: Root directory of extracted files
            
        Returns:
            List of FileMetadata for valid source files
            
        Raises:
            FileCountExceededError: If file count exceeds limit
        """
        file_metadata: List[FileMetadata] = []
        file_count = 0
        
        for file_path in self._walk_directory(root_dir):
            file_count += 1
            
            # Check file count limit
            if file_count > self.config.MAX_FILE_COUNT:
                raise FileCountExceededError(
                    f"File count exceeds limit of {self.config.MAX_FILE_COUNT}"
                )
            
            # Skip if not a supported source file
            if not self._is_supported_file(file_path):
                continue
            
            # Validate file size
            try:
                self._validate_file_size(file_path)
            except FileSizeExceededError as e:
                logger.warning(f"Skipping large file: {file_path.name} - {e}")
                continue
            
            # Process file
            try:
                metadata = self._create_file_metadata(file_path, root_dir)
                file_metadata.append(metadata)
                logger.debug(f"Processed: {metadata.relative_path}")
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")
                continue
        
        return file_metadata
    
    def _walk_directory(self, root_dir: Path):
        """Walk directory tree, yielding file paths while respecting ignore rules.
        
        Args:
            root_dir: Root directory to walk
            
        Yields:
            Path objects for files
        """
        for dirpath, dirnames, filenames in os.walk(root_dir):
            current_dir = Path(dirpath)
            
            # Filter out ignored directories (modifies in-place)
            dirnames[:] = [
                d for d in dirnames
                if d not in self.config.IGNORED_DIRS and not d.startswith('.')
            ]
            
            # Yield file paths
            for filename in filenames:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                file_path = current_dir / filename
                yield file_path
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file is a supported source file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file should be processed
        """
        # Check extension
        ext = file_path.suffix.lower()
        
        # Skip ignored patterns
        if ext in self.config.IGNORED_PATTERNS:
            return False
        
        # Check if supported language
        return ext in self.config.LANGUAGE_EXTENSIONS
    
    def _validate_file_size(self, file_path: Path) -> None:
        """Validate file size is within limits.
        
        Args:
            file_path: Path to file
            
        Raises:
            FileSizeExceededError: If file exceeds size limit
        """
        size_mb = file_path.stat().st_size / (1024 * 1024)
        max_size = self.config.MAX_FILE_SIZE_MB
        
        if size_mb > max_size:
            raise FileSizeExceededError(
                f"File size {size_mb:.2f}MB exceeds limit of {max_size}MB"
            )
    
    def _create_file_metadata(
        self,
        file_path: Path,
        root_dir: Path
    ) -> FileMetadata:
        """Create metadata for a source file.
        
        Args:
            file_path: Path to file
            root_dir: Root directory for relative path calculation
            
        Returns:
            FileMetadata instance
        """
        # Read file content
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        # Detect encoding
        detected = chardet.detect(raw_content)
        encoding = detected['encoding'] or 'utf-8'
        
        # Normalize to UTF-8
        try:
            content = raw_content.decode(encoding)
            normalized_content = content.encode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError) as e:
            logger.warning(f"Encoding issue in {file_path}: {e}, using utf-8 with errors='replace'")
            content = raw_content.decode('utf-8', errors='replace')
            normalized_content = content.encode('utf-8')
            encoding = 'utf-8'
        
        # Compute SHA256 hash
        sha256_hash = hashlib.sha256(normalized_content).hexdigest()
        
        # Detect language
        ext = file_path.suffix.lower()
        language = self.config.LANGUAGE_EXTENSIONS.get(ext, 'unknown')
        
        # Calculate relative path (cross-platform)
        relative_path = file_path.relative_to(root_dir).as_posix()
        
        return FileMetadata(
            path=file_path,
            language=language,
            size=len(normalized_content),
            sha256=sha256_hash,
            encoding=encoding,
            relative_path=relative_path,
        )
    
    def cleanup(self) -> None:
        """Clean up temporary extraction directory."""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
            self.temp_dir = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
        return False
