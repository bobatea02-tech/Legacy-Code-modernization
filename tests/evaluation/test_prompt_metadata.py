"""Tests for prompt metadata tracking in EvaluationReport.

Tests verify that prompt_metadata field includes:
- version
- checksum
- model_name
"""

import pytest
from app.evaluation.evaluator import (
    PipelineEvaluator,
    EvaluationInput,
    EvaluationReport
)


class TestPromptMetadataTracking:
    """Test suite for prompt metadata tracking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = PipelineEvaluator()
    
    def test_prompt_metadata_included_in_report(self):
        """Test that prompt_metadata is included in evaluation report."""
        # Arrange
        prompt_metadata = {
            "code_translation": {
                "version": "1.0.0",
                "checksum": "abc12345",
                "model_name": "gemini-pro"
            }
        }
        
        eval_input = EvaluationInput(
            repo_id="test-repo",
            naive_token_count=10000,
            optimized_token_count=6000,
            start_time=1000.0,
            end_time=1100.0,
            files_processed=10,
            phase_metadata={
                "prompt_metadata": prompt_metadata
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.prompt_metadata is not None
        assert "code_translation" in report.prompt_metadata
        assert report.prompt_metadata["code_translation"]["version"] == "1.0.0"
        assert report.prompt_metadata["code_translation"]["checksum"] == "abc12345"
        assert report.prompt_metadata["code_translation"]["model_name"] == "gemini-pro"
    
    def test_prompt_metadata_in_to_dict(self):
        """Test that prompt_metadata is included in to_dict() output."""
        # Arrange
        prompt_metadata = {
            "code_translation": {
                "version": "2.0.0",
                "checksum": "def67890",
                "model_name": "gemini-1.5-pro"
            }
        }
        
        eval_input = EvaluationInput(
            repo_id="test-repo",
            naive_token_count=8000,
            optimized_token_count=5000,
            start_time=1000.0,
            end_time=1080.0,
            files_processed=8,
            phase_metadata={
                "prompt_metadata": prompt_metadata
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        report_dict = report.to_dict()
        
        # Assert
        assert "prompt_metadata" in report_dict
        assert isinstance(report_dict["prompt_metadata"], dict)
        assert "code_translation" in report_dict["prompt_metadata"]
        assert report_dict["prompt_metadata"]["code_translation"]["version"] == "2.0.0"
        assert report_dict["prompt_metadata"]["code_translation"]["checksum"] == "def67890"
        assert report_dict["prompt_metadata"]["code_translation"]["model_name"] == "gemini-1.5-pro"
    
    def test_prompt_metadata_json_serializable(self):
        """Test that prompt_metadata is JSON serializable."""
        # Arrange
        prompt_metadata = {
            "code_translation": {
                "version": "1.5.0",
                "checksum": "xyz98765",
                "model_name": "gemini-pro"
            },
            "documentation": {
                "version": "1.0.0",
                "checksum": "abc11111",
                "model_name": "gemini-pro"
            }
        }
        
        eval_input = EvaluationInput(
            repo_id="test-repo",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1050.0,
            files_processed=5,
            phase_metadata={
                "prompt_metadata": prompt_metadata
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        report_dict = report.to_dict()
        
        # Assert - verify JSON serializable
        import json
        json_str = json.dumps(report_dict)
        assert isinstance(json_str, str)
        
        # Verify can be deserialized
        deserialized = json.loads(json_str)
        assert "prompt_metadata" in deserialized
        assert deserialized["prompt_metadata"]["code_translation"]["version"] == "1.5.0"
    
    def test_empty_prompt_metadata(self):
        """Test evaluation with empty prompt_metadata."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1050.0,
            files_processed=5,
            phase_metadata={}
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.prompt_metadata == {}
        assert isinstance(report.prompt_metadata, dict)
    
    def test_legacy_prompt_versions_still_works(self):
        """Test that legacy prompt_versions field still works."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1050.0,
            files_processed=5,
            phase_metadata={
                "prompt_versions": {
                    "code_translation": "1.0.0"
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.prompt_versions is not None
        assert "code_translation" in report.prompt_versions
        assert report.prompt_versions["code_translation"] == "1.0.0"
    
    def test_both_prompt_versions_and_metadata(self):
        """Test that both prompt_versions and prompt_metadata can coexist."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1050.0,
            files_processed=5,
            phase_metadata={
                "prompt_versions": {
                    "code_translation": "1.0.0"
                },
                "prompt_metadata": {
                    "code_translation": {
                        "version": "1.0.0",
                        "checksum": "abc123",
                        "model_name": "gemini-pro"
                    }
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        report_dict = report.to_dict()
        
        # Assert
        assert "prompt_versions" in report_dict
        assert "prompt_metadata" in report_dict
        assert report_dict["prompt_versions"]["code_translation"] == "1.0.0"
        assert report_dict["prompt_metadata"]["code_translation"]["version"] == "1.0.0"
        assert report_dict["prompt_metadata"]["code_translation"]["checksum"] == "abc123"
        assert report_dict["prompt_metadata"]["code_translation"]["model_name"] == "gemini-pro"
