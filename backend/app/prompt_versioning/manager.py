"""Deterministic Prompt Versioning System for managing LLM prompt templates.

This module provides version control for prompt templates used in the pipeline,
ensuring traceability, rollback capability, and integrity validation.

Architecture:
- Pure service layer (no FastAPI, CLI, or direct LLM calls)
- Deterministic behavior with checksum validation
- JSON-serializable metadata
- Storage abstraction for easy database migration
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import hashlib
import re

from app.core.config import get_settings
from app.core.logging import get_logger
from app.prompt_versioning.schema import PromptBundle

logger = get_logger(__name__)
settings = get_settings()


# ============================================================================
# Exceptions
# ============================================================================

class PromptVersioningError(Exception):
    """Base exception for prompt versioning errors."""
    pass


class PromptNotFoundError(PromptVersioningError):
    """Raised when prompt template is not found."""
    pass


class VersionNotFoundError(PromptVersioningError):
    """Raised when specific version is not found."""
    pass


class DuplicateVersionError(PromptVersioningError):
    """Raised when attempting to register duplicate version."""
    pass


class PromptIntegrityError(PromptVersioningError):
    """Raised when checksum validation fails."""
    pass


class InvalidVersionError(PromptVersioningError):
    """Raised when version format is invalid."""
    pass


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class PromptTemplate:
    """Prompt template with version metadata.
    
    Attributes:
        name: Prompt template name (e.g., 'code_translation')
        version: Semantic version (e.g., '1.0.0')
        content: Prompt template string
        checksum: SHA256 checksum of content
        created_at: ISO timestamp of creation
        metadata: Additional metadata dictionary
    """
    name: str
    version: str
    content: str
    checksum: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation
        """
        return asdict(self)
    
    def validate_checksum(self) -> bool:
        """Validate content matches stored checksum.
        
        Returns:
            True if checksum matches, False otherwise
        """
        computed = hashlib.sha256(self.content.encode('utf-8')).hexdigest()
        return computed == self.checksum


# ============================================================================
# Storage Interface
# ============================================================================

class PromptStorage:
    """Abstract storage interface for prompt templates.
    
    This interface allows easy swapping between in-memory and database storage.
    """
    
    def __init__(self) -> None:
        """Initialize storage."""
        # name -> version -> PromptTemplate dict
        self._prompts: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # name -> active_version
        self._active_versions: Dict[str, str] = {}
    
    def store_prompt(self, prompt: PromptTemplate) -> None:
        """Store prompt template.
        
        Args:
            prompt: PromptTemplate to store
        """
        if prompt.name not in self._prompts:
            self._prompts[prompt.name] = {}
        
        self._prompts[prompt.name][prompt.version] = prompt.to_dict()
        
        # Do NOT automatically set as active - let manager handle this
    
    def get_prompt(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get specific prompt version.
        
        Args:
            name: Prompt name
            version: Version string
            
        Returns:
            Prompt dictionary or None if not found
        """
        if name in self._prompts and version in self._prompts[name]:
            return self._prompts[name][version]
        return None
    
    def get_versions(self, name: str) -> List[str]:
        """Get all versions for a prompt.
        
        Args:
            name: Prompt name
            
        Returns:
            List of version strings
        """
        if name in self._prompts:
            return list(self._prompts[name].keys())
        return []
    
    def prompt_exists(self, name: str) -> bool:
        """Check if prompt exists.
        
        Args:
            name: Prompt name
            
        Returns:
            True if prompt exists
        """
        return name in self._prompts
    
    def version_exists(self, name: str, version: str) -> bool:
        """Check if specific version exists.
        
        Args:
            name: Prompt name
            version: Version string
            
        Returns:
            True if version exists
        """
        return name in self._prompts and version in self._prompts[name]
    
    def set_active_version(self, name: str, version: str) -> None:
        """Set active version for a prompt.
        
        Args:
            name: Prompt name
            version: Version to set as active
        """
        self._active_versions[name] = version
    
    def get_active_version(self, name: str) -> Optional[str]:
        """Get active version for a prompt.
        
        Args:
            name: Prompt name
            
        Returns:
            Active version string or None
        """
        return self._active_versions.get(name)


# ============================================================================
# Prompt Version Manager
# ============================================================================

class PromptVersionManager:
    """Manages prompt template versions with integrity validation.
    
    This class provides version control for LLM prompt templates, ensuring
    traceability, rollback capability, and content integrity.
    """
    
    def __init__(self, storage: Optional[PromptStorage] = None) -> None:
        """Initialize prompt version manager.
        
        Args:
            storage: Storage backend (defaults to in-memory)
        """
        self.storage = storage if storage is not None else PromptStorage()
        logger.info("PromptVersionManager initialized")
    
    def register_prompt(
        self,
        name: str,
        version: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        """Register a new prompt template version.
        
        Args:
            name: Prompt template name
            version: Semantic version (e.g., '1.0.0')
            content: Prompt template string
            metadata: Optional metadata dictionary
            
        Returns:
            Registered PromptTemplate
            
        Raises:
            InvalidVersionError: If version format is invalid
            DuplicateVersionError: If version already exists
        """
        # Validate version format
        if not self._is_valid_version(version):
            raise InvalidVersionError(
                f"Invalid version format: {version}. Expected semantic version (e.g., '1.0.0')"
            )
        
        # Check for duplicate version
        if self.storage.version_exists(name, version):
            raise DuplicateVersionError(
                f"Version {version} already exists for prompt '{name}'"
            )
        
        # Compute checksum
        checksum = self._compute_checksum(content)
        
        # Create timestamp (deterministic mode uses checksum as timestamp)
        if settings.DETERMINISTIC_MODE:
            created_at = f"deterministic-{checksum[:16]}"
        else:
            created_at = datetime.now(timezone.utc).isoformat()
        
        # Create prompt template
        prompt = PromptTemplate(
            name=name,
            version=version,
            content=content,
            checksum=checksum,
            created_at=created_at,
            metadata=metadata or {}
        )
        
        # Store prompt
        self.storage.store_prompt(prompt)
        
        logger.info(
            f"Registered prompt '{name}' version {version}",
            extra={
                "prompt_name": name,
                "version": version,
                "checksum": checksum[:8]
            }
        )
        
        return prompt
    
    def get_prompt(self, name: str, version: str) -> PromptTemplate:
        """Retrieve specific prompt version with integrity validation.
        
        Args:
            name: Prompt template name
            version: Version string
            
        Returns:
            PromptTemplate instance
            
        Raises:
            PromptNotFoundError: If prompt doesn't exist
            VersionNotFoundError: If version doesn't exist
            PromptIntegrityError: If checksum validation fails
        """
        if not self.storage.prompt_exists(name):
            raise PromptNotFoundError(f"Prompt '{name}' not found")
        
        prompt_dict = self.storage.get_prompt(name, version)
        if prompt_dict is None:
            raise VersionNotFoundError(
                f"Version {version} not found for prompt '{name}'"
            )
        
        # Reconstruct PromptTemplate
        prompt = PromptTemplate(**prompt_dict)
        
        # Validate checksum
        if not prompt.validate_checksum():
            raise PromptIntegrityError(
                f"Checksum mismatch for prompt '{name}' version {version}"
            )
        
        logger.debug(
            f"Retrieved prompt '{name}' version {version}",
            extra={"prompt_name": name, "version": version}
        )
        
        return prompt
    
    def get_prompt_bundle(self, name: str, version: Optional[str] = None) -> PromptBundle:
        """Retrieve prompt as structured PromptBundle.
        
        Args:
            name: Prompt template name
            version: Version string (uses latest if None)
            
        Returns:
            PromptBundle with system and user prompts separated
            
        Raises:
            PromptNotFoundError: If prompt doesn't exist
            VersionNotFoundError: If version doesn't exist
        """
        if version is None:
            prompt = self.get_latest(name)
        else:
            prompt = self.get_prompt(name, version)
        
        # Parse content to separate system and user prompts
        # Format: "SYSTEM:\n<system_prompt>\n\nUSER:\n<user_prompt>"
        content = prompt.content
        
        if "SYSTEM:" in content and "USER:" in content:
            parts = content.split("USER:", 1)
            system_part = parts[0].replace("SYSTEM:", "").strip()
            user_part = parts[1].strip()
        else:
            # Fallback: treat entire content as user prompt
            system_part = ""
            user_part = content
        
        return PromptBundle(
            system_prompt=system_part,
            user_prompt=user_part,
            version=prompt.version,
            metadata=prompt.metadata
        )
    
    def get_latest(self, name: str) -> PromptTemplate:
        """Retrieve latest (active) version of prompt.
        
        Args:
            name: Prompt template name
            
        Returns:
            PromptTemplate instance
            
        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        if not self.storage.prompt_exists(name):
            raise PromptNotFoundError(f"Prompt '{name}' not found")
        
        # Get active version
        active_version = self.storage.get_active_version(name)
        
        if active_version is None:
            # Fallback to highest semantic version
            versions = self.list_versions(name)
            if not versions:
                raise PromptNotFoundError(f"No versions found for prompt '{name}'")
            active_version = self._get_highest_version(versions)
        
        return self.get_prompt(name, active_version)
    
    def list_versions(self, name: str) -> List[str]:
        """List all versions for a prompt.
        
        Args:
            name: Prompt template name
            
        Returns:
            List of version strings sorted by semantic version
            
        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        if not self.storage.prompt_exists(name):
            raise PromptNotFoundError(f"Prompt '{name}' not found")
        
        versions = self.storage.get_versions(name)
        
        # Sort by semantic version
        return sorted(versions, key=self._version_sort_key)
    
    def set_active_version(self, name: str, version: str) -> None:
        """Set active version for a prompt (rollback support).
        
        Args:
            name: Prompt template name
            version: Version to set as active
            
        Raises:
            PromptNotFoundError: If prompt doesn't exist
            VersionNotFoundError: If version doesn't exist
        """
        if not self.storage.prompt_exists(name):
            raise PromptNotFoundError(f"Prompt '{name}' not found")
        
        if not self.storage.version_exists(name, version):
            raise VersionNotFoundError(
                f"Version {version} not found for prompt '{name}'"
            )
        
        self.storage.set_active_version(name, version)
        
        logger.info(
            f"Set active version for prompt '{name}' to {version}",
            extra={"prompt_name": name, "version": version}
        )
    
    def get_active_version(self, name: str) -> str:
        """Get active version for a prompt.
        
        Args:
            name: Prompt template name
            
        Returns:
            Active version string
            
        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        if not self.storage.prompt_exists(name):
            raise PromptNotFoundError(f"Prompt '{name}' not found")
        
        active_version = self.storage.get_active_version(name)
        
        if active_version is None:
            # Fallback to highest version
            versions = self.list_versions(name)
            if versions:
                active_version = self._get_highest_version(versions)
            else:
                raise PromptNotFoundError(f"No versions found for prompt '{name}'")
        
        return active_version
    
    def list_prompts(self) -> List[str]:
        """List all registered prompt names.
        
        Returns:
            List of prompt names
        """
        return list(self.storage._prompts.keys())
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _compute_checksum(self, content: str) -> str:
        """Compute SHA256 checksum of content.
        
        Args:
            content: Content string
            
        Returns:
            Hexadecimal checksum string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _is_valid_version(self, version: str) -> bool:
        """Validate semantic version format.
        
        Args:
            version: Version string
            
        Returns:
            True if valid semantic version
        """
        # Semantic versioning pattern: MAJOR.MINOR.PATCH
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def _version_sort_key(self, version: str) -> tuple:
        """Generate sort key for semantic version.
        
        Args:
            version: Version string (e.g., '1.2.3')
            
        Returns:
            Tuple of integers for sorting
        """
        try:
            parts = version.split('.')
            return tuple(int(p) for p in parts)
        except (ValueError, AttributeError):
            return (0, 0, 0)
    
    def _get_highest_version(self, versions: List[str]) -> str:
        """Get highest semantic version from list.
        
        Args:
            versions: List of version strings
            
        Returns:
            Highest version string
        """
        if not versions:
            raise ValueError("Empty version list")
        
        return max(versions, key=self._version_sort_key)
