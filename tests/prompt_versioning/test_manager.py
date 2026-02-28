"""Unit tests for Prompt Version Manager.

Tests cover:
- Register new prompt version
- Prevent duplicate version
- Retrieve specific version
- Retrieve latest version
- Rollback works
- Checksum mismatch detection
- Deterministic behavior
"""

import pytest
import hashlib
from datetime import datetime

from app.prompt_versioning import (
    PromptVersionManager,
    PromptTemplate,
    PromptStorage,
    PromptNotFoundError,
    VersionNotFoundError,
    DuplicateVersionError,
    PromptIntegrityError,
    InvalidVersionError
)


class TestPromptVersionManager:
    """Test suite for PromptVersionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = PromptVersionManager()
        self.sample_prompt = "Translate the following {language} code to Python:\n\n{code}"
    
    def test_manager_initialization(self):
        """Test manager initializes correctly."""
        assert self.manager is not None
        assert isinstance(self.manager.storage, PromptStorage)
    
    def test_register_new_prompt_version(self):
        """Test registering a new prompt version."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        metadata = {"author": "test", "purpose": "translation"}
        
        # Act
        prompt = self.manager.register_prompt(name, version, content, metadata)
        
        # Assert
        assert prompt.name == name
        assert prompt.version == version
        assert prompt.content == content
        assert prompt.metadata == metadata
        assert len(prompt.checksum) == 64  # SHA256 hex length
        assert prompt.created_at is not None
    
    def test_prevent_duplicate_version(self):
        """Test that duplicate versions are prevented."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        
        # Register first time
        self.manager.register_prompt(name, version, content)
        
        # Act & Assert
        with pytest.raises(DuplicateVersionError) as exc_info:
            self.manager.register_prompt(name, version, content)
        
        assert "already exists" in str(exc_info.value)
    
    def test_retrieve_specific_version(self):
        """Test retrieving a specific version."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        
        self.manager.register_prompt(name, version, content)
        
        # Act
        retrieved = self.manager.get_prompt(name, version)
        
        # Assert
        assert retrieved.name == name
        assert retrieved.version == version
        assert retrieved.content == content
    
    def test_retrieve_latest_version(self):
        """Test retrieving the latest version."""
        # Arrange
        name = "code_translation"
        
        self.manager.register_prompt(name, "1.0.0", "Version 1.0.0")
        self.manager.register_prompt(name, "1.1.0", "Version 1.1.0")
        self.manager.register_prompt(name, "2.0.0", "Version 2.0.0")
        
        # Act
        latest = self.manager.get_latest(name)
        
        # Assert
        assert latest.version == "2.0.0"
        assert latest.content == "Version 2.0.0"
    
    def test_rollback_works(self):
        """Test rollback to older version."""
        # Arrange
        name = "code_translation"
        
        self.manager.register_prompt(name, "1.0.0", "Version 1.0.0")
        self.manager.register_prompt(name, "2.0.0", "Version 2.0.0")
        self.manager.register_prompt(name, "3.0.0", "Version 3.0.0")
        
        # Act - Rollback to 1.0.0
        self.manager.set_active_version(name, "1.0.0")
        latest = self.manager.get_latest(name)
        
        # Assert
        assert latest.version == "1.0.0"
        assert latest.content == "Version 1.0.0"
    
    def test_checksum_validation(self):
        """Test checksum validation on retrieval."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        
        prompt = self.manager.register_prompt(name, version, content)
        
        # Act - Validate checksum
        is_valid = prompt.validate_checksum()
        
        # Assert
        assert is_valid is True
        
        # Verify checksum matches expected
        expected_checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
        assert prompt.checksum == expected_checksum
    
    def test_checksum_mismatch_detection(self):
        """Test detection of checksum mismatch."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        
        prompt = self.manager.register_prompt(name, version, content)
        
        # Act - Corrupt the content
        prompt.content = "Corrupted content"
        
        # Assert
        assert prompt.validate_checksum() is False
    
    def test_deterministic_behavior(self):
        """Test that same inputs produce identical outputs."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        
        # Act - Register twice in different managers
        manager1 = PromptVersionManager()
        prompt1 = manager1.register_prompt(name, version, content)
        
        manager2 = PromptVersionManager()
        prompt2 = manager2.register_prompt(name, version, content)
        
        # Assert - Checksums should be identical
        assert prompt1.checksum == prompt2.checksum
        assert prompt1.content == prompt2.content
    
    def test_list_versions(self):
        """Test listing all versions for a prompt."""
        # Arrange
        name = "code_translation"
        
        self.manager.register_prompt(name, "1.0.0", "Version 1")
        self.manager.register_prompt(name, "1.1.0", "Version 2")
        self.manager.register_prompt(name, "2.0.0", "Version 3")
        
        # Act
        versions = self.manager.list_versions(name)
        
        # Assert
        assert len(versions) == 3
        assert "1.0.0" in versions
        assert "1.1.0" in versions
        assert "2.0.0" in versions
        # Should be sorted
        assert versions == ["1.0.0", "1.1.0", "2.0.0"]
    
    def test_prompt_not_found_error(self):
        """Test error when prompt doesn't exist."""
        # Act & Assert
        with pytest.raises(PromptNotFoundError) as exc_info:
            self.manager.get_prompt("nonexistent", "1.0.0")
        
        assert "not found" in str(exc_info.value)
    
    def test_version_not_found_error(self):
        """Test error when version doesn't exist."""
        # Arrange
        name = "code_translation"
        self.manager.register_prompt(name, "1.0.0", "Content")
        
        # Act & Assert
        with pytest.raises(VersionNotFoundError) as exc_info:
            self.manager.get_prompt(name, "2.0.0")
        
        assert "not found" in str(exc_info.value)
    
    def test_invalid_version_format(self):
        """Test error on invalid version format."""
        # Arrange
        name = "code_translation"
        content = self.sample_prompt
        
        # Act & Assert - Invalid formats
        with pytest.raises(InvalidVersionError):
            self.manager.register_prompt(name, "1.0", content)
        
        with pytest.raises(InvalidVersionError):
            self.manager.register_prompt(name, "v1.0.0", content)
        
        with pytest.raises(InvalidVersionError):
            self.manager.register_prompt(name, "1.0.0-beta", content)
    
    def test_valid_version_formats(self):
        """Test valid version formats are accepted."""
        # Arrange
        name = "code_translation"
        
        # Act & Assert - Valid formats
        prompt1 = self.manager.register_prompt(name, "1.0.0", "Content 1")
        prompt2 = self.manager.register_prompt(name, "10.20.30", "Content 2")
        prompt3 = self.manager.register_prompt(name, "0.0.1", "Content 3")
        
        assert prompt1.version == "1.0.0"
        assert prompt2.version == "10.20.30"
        assert prompt3.version == "0.0.1"
    
    def test_to_dict_serialization(self):
        """Test PromptTemplate to_dict() serialization."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        metadata = {"author": "test"}
        
        prompt = self.manager.register_prompt(name, version, content, metadata)
        
        # Act
        prompt_dict = prompt.to_dict()
        
        # Assert
        assert isinstance(prompt_dict, dict)
        assert prompt_dict["name"] == name
        assert prompt_dict["version"] == version
        assert prompt_dict["content"] == content
        assert prompt_dict["metadata"] == metadata
        assert "checksum" in prompt_dict
        assert "created_at" in prompt_dict
    
    def test_get_active_version(self):
        """Test getting active version."""
        # Arrange
        name = "code_translation"
        
        self.manager.register_prompt(name, "1.0.0", "Version 1")
        self.manager.register_prompt(name, "2.0.0", "Version 2")
        self.manager.set_active_version(name, "1.0.0")
        
        # Act
        active_version = self.manager.get_active_version(name)
        
        # Assert
        assert active_version == "1.0.0"
    
    def test_list_prompts(self):
        """Test listing all registered prompts."""
        # Arrange
        self.manager.register_prompt("prompt1", "1.0.0", "Content 1")
        self.manager.register_prompt("prompt2", "1.0.0", "Content 2")
        self.manager.register_prompt("prompt3", "1.0.0", "Content 3")
        
        # Act
        prompts = self.manager.list_prompts()
        
        # Assert
        assert len(prompts) == 3
        assert "prompt1" in prompts
        assert "prompt2" in prompts
        assert "prompt3" in prompts
    
    def test_multiple_versions_same_prompt(self):
        """Test registering multiple versions of same prompt."""
        # Arrange
        name = "code_translation"
        
        # Act
        v1 = self.manager.register_prompt(name, "1.0.0", "Version 1.0.0")
        v2 = self.manager.register_prompt(name, "1.1.0", "Version 1.1.0")
        v3 = self.manager.register_prompt(name, "2.0.0", "Version 2.0.0")
        
        # Assert
        assert v1.version == "1.0.0"
        assert v2.version == "1.1.0"
        assert v3.version == "2.0.0"
        
        # All should be retrievable
        retrieved_v1 = self.manager.get_prompt(name, "1.0.0")
        retrieved_v2 = self.manager.get_prompt(name, "1.1.0")
        retrieved_v3 = self.manager.get_prompt(name, "2.0.0")
        
        assert retrieved_v1.content == "Version 1.0.0"
        assert retrieved_v2.content == "Version 1.1.0"
        assert retrieved_v3.content == "Version 2.0.0"
    
    def test_version_sorting(self):
        """Test versions are sorted correctly."""
        # Arrange
        name = "code_translation"
        
        # Register in random order
        self.manager.register_prompt(name, "2.0.0", "V2")
        self.manager.register_prompt(name, "1.1.0", "V1.1")
        self.manager.register_prompt(name, "1.0.0", "V1")
        self.manager.register_prompt(name, "10.0.0", "V10")
        self.manager.register_prompt(name, "1.2.0", "V1.2")
        
        # Act
        versions = self.manager.list_versions(name)
        
        # Assert - Should be sorted semantically
        assert versions == ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "10.0.0"]
    
    def test_metadata_preservation(self):
        """Test metadata is preserved correctly."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        metadata = {
            "author": "John Doe",
            "purpose": "Code translation",
            "tags": ["translation", "llm"],
            "model": "gemini-pro"
        }
        
        # Act
        prompt = self.manager.register_prompt(name, version, content, metadata)
        retrieved = self.manager.get_prompt(name, version)
        
        # Assert
        assert retrieved.metadata == metadata
        assert retrieved.metadata["author"] == "John Doe"
        assert retrieved.metadata["tags"] == ["translation", "llm"]
    
    def test_empty_metadata(self):
        """Test prompt with no metadata."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        
        # Act
        prompt = self.manager.register_prompt(name, version, content)
        
        # Assert
        assert prompt.metadata == {}
    
    def test_timestamp_format(self):
        """Test timestamp is in ISO format."""
        # Arrange
        name = "code_translation"
        version = "1.0.0"
        content = self.sample_prompt
        
        # Act
        prompt = self.manager.register_prompt(name, version, content)
        
        # Assert
        # Should be parseable as ISO format
        assert prompt.created_at.endswith("+00:00") or prompt.created_at.endswith("Z")
        datetime.fromisoformat(prompt.created_at.replace("Z", "+00:00"))


class TestPromptStorage:
    """Test suite for PromptStorage class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.storage = PromptStorage()
    
    def test_storage_initialization(self):
        """Test storage initializes correctly."""
        assert self.storage is not None
        assert isinstance(self.storage._prompts, dict)
        assert isinstance(self.storage._active_versions, dict)
    
    def test_store_and_retrieve_prompt(self):
        """Test storing and retrieving prompt."""
        # Arrange
        prompt = PromptTemplate(
            name="test",
            version="1.0.0",
            content="Test content",
            checksum="abc123",
            created_at="2024-01-01T00:00:00+00:00",
            metadata={}
        )
        
        # Act
        self.storage.store_prompt(prompt)
        retrieved = self.storage.get_prompt("test", "1.0.0")
        
        # Assert
        assert retrieved is not None
        assert retrieved["name"] == "test"
        assert retrieved["version"] == "1.0.0"
    
    def test_prompt_exists(self):
        """Test prompt existence check."""
        # Arrange
        prompt = PromptTemplate(
            name="test",
            version="1.0.0",
            content="Test",
            checksum="abc",
            created_at="2024-01-01T00:00:00+00:00"
        )
        
        # Act
        self.storage.store_prompt(prompt)
        
        # Assert
        assert self.storage.prompt_exists("test") is True
        assert self.storage.prompt_exists("nonexistent") is False
    
    def test_version_exists(self):
        """Test version existence check."""
        # Arrange
        prompt = PromptTemplate(
            name="test",
            version="1.0.0",
            content="Test",
            checksum="abc",
            created_at="2024-01-01T00:00:00+00:00"
        )
        
        # Act
        self.storage.store_prompt(prompt)
        
        # Assert
        assert self.storage.version_exists("test", "1.0.0") is True
        assert self.storage.version_exists("test", "2.0.0") is False
    
    def test_active_version_management(self):
        """Test active version setting and retrieval."""
        # Arrange
        prompt = PromptTemplate(
            name="test",
            version="1.0.0",
            content="Test",
            checksum="abc",
            created_at="2024-01-01T00:00:00+00:00"
        )
        
        # Act
        self.storage.store_prompt(prompt)
        self.storage.set_active_version("test", "1.0.0")
        active = self.storage.get_active_version("test")
        
        # Assert
        assert active == "1.0.0"


class TestPromptTemplate:
    """Test suite for PromptTemplate dataclass."""
    
    def test_prompt_template_creation(self):
        """Test creating PromptTemplate."""
        # Arrange & Act
        prompt = PromptTemplate(
            name="test",
            version="1.0.0",
            content="Test content",
            checksum="abc123",
            created_at="2024-01-01T00:00:00+00:00",
            metadata={"key": "value"}
        )
        
        # Assert
        assert prompt.name == "test"
        assert prompt.version == "1.0.0"
        assert prompt.content == "Test content"
        assert prompt.checksum == "abc123"
        assert prompt.metadata == {"key": "value"}
    
    def test_validate_checksum_correct(self):
        """Test checksum validation with correct checksum."""
        # Arrange
        content = "Test content"
        checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        prompt = PromptTemplate(
            name="test",
            version="1.0.0",
            content=content,
            checksum=checksum,
            created_at="2024-01-01T00:00:00+00:00"
        )
        
        # Act & Assert
        assert prompt.validate_checksum() is True
    
    def test_validate_checksum_incorrect(self):
        """Test checksum validation with incorrect checksum."""
        # Arrange
        prompt = PromptTemplate(
            name="test",
            version="1.0.0",
            content="Test content",
            checksum="wrong_checksum",
            created_at="2024-01-01T00:00:00+00:00"
        )
        
        # Act & Assert
        assert prompt.validate_checksum() is False
