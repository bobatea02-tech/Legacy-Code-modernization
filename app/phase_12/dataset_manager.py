"""Dataset management for Phase-12 real-world validation.

Handles dataset selection, normalization, and deterministic hashing.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import zipfile
import shutil

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DatasetMetadata:
    """Metadata for a real-world dataset."""
    dataset_id: str
    source_url: str
    language: str
    file_count: int
    total_loc: int
    dataset_hash: str
    files: List[Dict[str, str]]  # [{path, hash, size}]


class DatasetManager:
    """Manages real-world dataset selection and normalization."""
    
    def __init__(self, datasets_dir: Path = Path("datasets")):
        """Initialize dataset manager.
        
        Args:
            datasets_dir: Directory for storing datasets
        """
        self.datasets_dir = datasets_dir
        self.datasets_dir.mkdir(exist_ok=True)
    
    def normalize_dataset(self, source_path: Path, dataset_id: str) -> DatasetMetadata:
        """Normalize dataset for deterministic processing.
        
        Steps:
        1. Remove binaries, logs, temp files
        2. Normalize line endings to LF
        3. Sort file list deterministically
        4. Calculate dataset hash
        
        Args:
            source_path: Path to source repository
            dataset_id: Unique dataset identifier
            
        Returns:
            DatasetMetadata with hash and file list
        """
        logger.info(f"Normalizing dataset: {dataset_id}")
        
        target_dir = self.datasets_dir / dataset_id
        target_dir.mkdir(exist_ok=True)
        
        # Copy and normalize files
        normalized_files = []
        
        if source_path.suffix == '.zip':
            normalized_files = self._normalize_from_zip(source_path, target_dir)
        else:
            normalized_files = self._normalize_from_directory(source_path, target_dir)
        
        # Sort files deterministically by path
        normalized_files.sort(key=lambda f: f['path'])
        
        # Calculate dataset hash
        dataset_hash = self._calculate_dataset_hash(normalized_files)
        
        # Count LOC
        total_loc = sum(self._count_loc(target_dir / f['path']) for f in normalized_files)
        
        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            source_url="local",
            language=self._detect_language(normalized_files),
            file_count=len(normalized_files),
            total_loc=total_loc,
            dataset_hash=dataset_hash,
            files=normalized_files
        )
        
        # Save metadata
        metadata_path = target_dir / "dataset_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2, sort_keys=True)
        
        logger.info(
            f"Dataset normalized: {len(normalized_files)} files, "
            f"{total_loc} LOC, hash={dataset_hash[:8]}"
        )
        
        return metadata
    
    def _normalize_from_zip(self, zip_path: Path, target_dir: Path) -> List[Dict[str, str]]:
        """Normalize files from ZIP archive.
        
        Args:
            zip_path: Path to ZIP file
            target_dir: Target directory
            
        Returns:
            List of normalized file metadata
        """
        normalized_files = []
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                
                # Skip unwanted files
                if self._should_skip_file(info.filename):
                    continue
                
                # Extract and normalize
                content = zf.read(info.filename)
                
                try:
                    # Decode and normalize line endings
                    text = content.decode('utf-8')
                    normalized_text = text.replace('\r\n', '\n').replace('\r', '\n')
                    
                    # Write normalized file
                    file_path = target_dir / info.filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(normalized_text, encoding='utf-8')
                    
                    # Calculate file hash
                    file_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
                    
                    normalized_files.append({
                        'path': info.filename,
                        'hash': file_hash,
                        'size': len(normalized_text)
                    })
                    
                except UnicodeDecodeError:
                    logger.warning(f"Skipping binary file: {info.filename}")
                    continue
        
        return normalized_files
    
    def _normalize_from_directory(self, source_dir: Path, target_dir: Path) -> List[Dict[str, str]]:
        """Normalize files from directory.
        
        Args:
            source_dir: Source directory
            target_dir: Target directory
            
        Returns:
            List of normalized file metadata
        """
        normalized_files = []
        
        for file_path in source_dir.rglob('*'):
            if file_path.is_dir():
                continue
            
            rel_path = file_path.relative_to(source_dir)
            
            # Skip unwanted files
            if self._should_skip_file(str(rel_path)):
                continue
            
            try:
                # Read and normalize
                text = file_path.read_text(encoding='utf-8')
                normalized_text = text.replace('\r\n', '\n').replace('\r', '\n')
                
                # Write normalized file
                target_path = target_dir / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(normalized_text, encoding='utf-8')
                
                # Calculate file hash
                file_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
                
                normalized_files.append({
                    'path': str(rel_path).replace('\\', '/'),
                    'hash': file_hash,
                    'size': len(normalized_text)
                })
                
            except (UnicodeDecodeError, PermissionError):
                logger.warning(f"Skipping file: {rel_path}")
                continue
        
        return normalized_files
    
    def _should_skip_file(self, filename: str) -> bool:
        """Check if file should be skipped.
        
        Args:
            filename: File name or path
            
        Returns:
            True if file should be skipped
        """
        skip_patterns = [
            '.class', '.jar', '.war', '.exe', '.dll', '.so',
            '.log', '.tmp', '.temp', '.cache',
            '.git/', '__pycache__/', 'node_modules/',
            '.DS_Store', 'Thumbs.db'
        ]
        
        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in skip_patterns)
    
    def _calculate_dataset_hash(self, files: List[Dict[str, str]]) -> str:
        """Calculate deterministic hash for entire dataset.
        
        Args:
            files: List of file metadata (must be sorted)
            
        Returns:
            SHA-256 hash of dataset
        """
        hasher = hashlib.sha256()
        
        for file_meta in files:
            # Hash path + file hash
            entry = f"{file_meta['path']}:{file_meta['hash']}"
            hasher.update(entry.encode('utf-8'))
        
        return hasher.hexdigest()
    
    def _detect_language(self, files: List[Dict[str, str]]) -> str:
        """Detect primary language from file extensions.
        
        Args:
            files: List of file metadata
            
        Returns:
            Detected language
        """
        extensions = {}
        
        for file_meta in files:
            ext = Path(file_meta['path']).suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Map extensions to languages
        lang_map = {
            '.java': 'java',
            '.cs': 'csharp',
            '.cbl': 'cobol',
            '.cob': 'cobol'
        }
        
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
            if ext in lang_map:
                return lang_map[ext]
        
        return 'unknown'
    
    def _count_loc(self, file_path: Path) -> int:
        """Count lines of code in file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Line count
        """
        try:
            return len(file_path.read_text(encoding='utf-8').splitlines())
        except:
            return 0
    
    def verify_dataset_hash(self, dataset_id: str) -> Tuple[bool, str]:
        """Verify dataset hash matches stored metadata.
        
        Args:
            dataset_id: Dataset identifier
            
        Returns:
            Tuple of (matches, computed_hash)
        """
        dataset_dir = self.datasets_dir / dataset_id
        metadata_path = dataset_dir / "dataset_metadata.json"
        
        if not metadata_path.exists():
            return False, ""
        
        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        stored_hash = metadata['dataset_hash']
        
        # Recalculate hash
        files = metadata['files']
        computed_hash = self._calculate_dataset_hash(files)
        
        matches = stored_hash == computed_hash
        
        if not matches:
            logger.error(
                f"Dataset hash mismatch: stored={stored_hash[:8]}, "
                f"computed={computed_hash[:8]}"
            )
        
        return matches, computed_hash
