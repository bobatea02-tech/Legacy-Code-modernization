"""Tests for Phase-12 validation components."""

import pytest
import hashlib
from pathlib import Path
from app.phase_12.dataset_manager import DatasetManager
from app.phase_12.validator import Phase12Validator, FailureCause


class TestDatasetManager:
    """Tests for DatasetManager."""
    
    def test_calculate_dataset_hash_deterministic(self, tmp_path):
        """Test dataset hash is deterministic."""
        manager = DatasetManager(tmp_path)
        
        files = [
            {'path': 'file1.java', 'hash': 'abc123', 'size': 100},
            {'path': 'file2.java', 'hash': 'def456', 'size': 200}
        ]
        
        hash1 = manager._calculate_dataset_hash(files)
        hash2 = manager._calculate_dataset_hash(files)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256
    
    def test_should_skip_file(self):
        """Test file skip logic."""
        manager = DatasetManager()
        
        assert manager._should_skip_file('test.class')
        assert manager._should_skip_file('app.jar')
        assert manager._should_skip_file('.git/config')
        assert manager._should_skip_file('__pycache__/module.pyc')
        assert not manager._should_skip_file('Main.java')
        assert not manager._should_skip_file('src/util/Helper.java')
    
    def test_detect_language(self):
        """Test language detection."""
        manager = DatasetManager()
        
        files_java = [
            {'path': 'Main.java', 'hash': 'x', 'size': 100},
            {'path': 'Helper.java', 'hash': 'y', 'size': 100}
        ]
        
        files_cobol = [
            {'path': 'main.cbl', 'hash': 'x', 'size': 100},
            {'path': 'payment.cbl', 'hash': 'y', 'size': 100}
        ]
        
        assert manager._detect_language(files_java) == 'java'
        assert manager._detect_language(files_cobol) == 'cobol'


class TestPhase12Validator:
    """Tests for Phase12Validator."""
    
    def test_categorize_failure(self):
        """Test failure categorization."""
        validator = Phase12Validator()
        
        assert validator._categorize_failure(['JSON parse error']) == FailureCause.SCHEMA_PARSE_FAILURE
        assert validator._categorize_failure(['API timeout']) == FailureCause.PROVIDER_API_ERROR
        assert validator._categorize_failure(['Missing dependency context']) == FailureCause.MISSING_CONTEXT
        assert validator._categorize_failure(['Unsupported feature']) == FailureCause.UNSUPPORTED_FEATURE
        assert validator._categorize_failure(['Unknown error']) == FailureCause.PROMPT_MISUNDERSTANDING
    
    def test_calculate_result_hash_deterministic(self):
        """Test result hash is deterministic."""
        from app.translation.orchestrator import TranslationResult, TranslationStatus
        from app.pipeline.service import PipelineResult
        
        validator = Phase12Validator()
        
        result = PipelineResult(success=True)
        result.translation_results = [
            TranslationResult(
                module_name="module1",
                status=TranslationStatus.SUCCESS,
                translated_code="def foo(): pass"
            ),
            TranslationResult(
                module_name="module2",
                status=TranslationStatus.SUCCESS,
                translated_code="def bar(): pass"
            )
        ]
        
        hash1 = validator._calculate_result_hash(result)
        hash2 = validator._calculate_result_hash(result)
        
        assert hash1 == hash2
        assert len(hash1) == 64


@pytest.mark.asyncio
async def test_phase_12_integration(tmp_path):
    """Integration test for Phase-12 validation (requires LLM)."""
    # This test requires actual LLM access and sample repos
    # Skip in CI/CD without credentials
    pytest.skip("Integration test requires LLM credentials")
