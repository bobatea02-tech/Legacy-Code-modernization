"""Unit tests for pipeline evaluator module.

Tests cover:
- Token reduction calculations
- Runtime metric accuracy
- Edge cases (zero files, zero token difference)
- Deterministic outputs
- JSON serialization
"""

import pytest
import time
from datetime import datetime

from app.evaluation.evaluator import (
    PipelineEvaluator,
    EvaluationInput,
    EvaluationReport,
    TokenMetrics,
    RuntimeMetrics,
    QualityMetrics
)


class TestPipelineEvaluator:
    """Test suite for PipelineEvaluator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = PipelineEvaluator()
    
    def test_evaluator_initialization(self):
        """Test evaluator initializes correctly."""
        assert self.evaluator is not None
    
    def test_basic_evaluation(self):
        """Test basic evaluation with typical inputs."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-001",
            naive_token_count=10000,
            optimized_token_count=6000,
            start_time=1000.0,
            end_time=1100.0,
            files_processed=10,
            errors_encountered=1,
            phase_metadata={
                "validation": {
                    "total": 10,
                    "passed": 8,
                    "syntax_errors": 1,
                    "dependency_issues": 1
                },
                "phase_runtimes": {
                    "ingestion": 10.0,
                    "parsing": 20.0,
                    "translation": 50.0,
                    "validation": 20.0
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report is not None
        assert report.repo_id == "test-repo-001"
        assert isinstance(report.token_metrics, TokenMetrics)
        assert isinstance(report.runtime_metrics, RuntimeMetrics)
        assert isinstance(report.quality_metrics, QualityMetrics)
        assert isinstance(report.summary_text, str)
        assert isinstance(report.timestamp, str)
    
    def test_token_reduction_calculation(self):
        """Test correct token reduction math."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-002",
            naive_token_count=10000,
            optimized_token_count=6000,
            start_time=1000.0,
            end_time=1100.0,
            files_processed=10
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.token_metrics.naive_token_count == 10000
        assert report.token_metrics.optimized_token_count == 6000
        assert report.token_metrics.token_reduction == 4000
        assert report.token_metrics.reduction_percentage == 40.0
        assert report.token_metrics.tokens_per_file == 600.0
    
    def test_runtime_calculation_accuracy(self):
        """Test runtime calculation accuracy."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-003",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1150.5,
            files_processed=5,
            phase_metadata={
                "phase_runtimes": {
                    "ingestion": 30.0,
                    "parsing": 50.0,
                    "translation": 70.5
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.runtime_metrics.total_runtime_seconds == 150.5
        assert report.runtime_metrics.runtime_per_file == 30.1
        assert report.runtime_metrics.runtime_per_phase == {
            "ingestion": 30.0,
            "parsing": 50.0,
            "translation": 70.5
        }
        assert report.runtime_metrics.timeout_detected is False
    
    def test_edge_case_zero_files(self):
        """Test edge case: zero files processed."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-004",
            naive_token_count=1000,
            optimized_token_count=500,
            start_time=1000.0,
            end_time=1010.0,
            files_processed=0,
            errors_encountered=5
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.token_metrics.tokens_per_file == 0.0
        assert report.runtime_metrics.runtime_per_file == 0.0
        assert report.token_metrics.efficiency_score < 50.0  # Low due to no files processed
    
    def test_edge_case_zero_token_difference(self):
        """Test edge case: zero token difference (no optimization)."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-005",
            naive_token_count=5000,
            optimized_token_count=5000,
            start_time=1000.0,
            end_time=1050.0,
            files_processed=10
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.token_metrics.token_reduction == 0
        assert report.token_metrics.reduction_percentage == 0.0
        assert report.token_metrics.efficiency_score > 0.0  # Still has success component
    
    def test_edge_case_zero_naive_tokens(self):
        """Test edge case: zero naive tokens."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-006",
            naive_token_count=0,
            optimized_token_count=0,
            start_time=1000.0,
            end_time=1010.0,
            files_processed=0
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.token_metrics.token_reduction == 0
        assert report.token_metrics.reduction_percentage == 0.0
        assert report.token_metrics.tokens_per_file == 0.0
    
    def test_deterministic_output(self):
        """Test that same inputs produce identical outputs."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-007",
            naive_token_count=8000,
            optimized_token_count=5000,
            start_time=1000.0,
            end_time=1100.0,
            files_processed=8,
            errors_encountered=2,
            phase_metadata={
                "validation": {
                    "total": 8,
                    "passed": 6,
                    "syntax_errors": 1,
                    "dependency_issues": 1
                }
            }
        )
        
        # Act
        report1 = self.evaluator.evaluate(eval_input)
        report2 = self.evaluator.evaluate(eval_input)
        
        # Assert - all metrics should be identical (except timestamp)
        assert report1.token_metrics.token_reduction == report2.token_metrics.token_reduction
        assert report1.token_metrics.reduction_percentage == report2.token_metrics.reduction_percentage
        assert report1.token_metrics.efficiency_score == report2.token_metrics.efficiency_score
        assert report1.runtime_metrics.total_runtime_seconds == report2.runtime_metrics.total_runtime_seconds
        assert report1.quality_metrics.validation_pass_rate == report2.quality_metrics.validation_pass_rate
    
    def test_json_serialization(self):
        """Test JSON serialization via to_dict()."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-008",
            naive_token_count=7000,
            optimized_token_count=4000,
            start_time=1000.0,
            end_time=1080.0,
            files_processed=7,
            phase_metadata={
                "validation": {
                    "total": 7,
                    "passed": 5,
                    "syntax_errors": 2,
                    "dependency_issues": 0
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        report_dict = report.to_dict()
        
        # Assert
        assert isinstance(report_dict, dict)
        assert "repo_id" in report_dict
        assert "token_metrics" in report_dict
        assert "runtime_metrics" in report_dict
        assert "quality_metrics" in report_dict
        assert "summary_text" in report_dict
        assert "timestamp" in report_dict
        
        # Verify nested dictionaries
        assert isinstance(report_dict["token_metrics"], dict)
        assert isinstance(report_dict["runtime_metrics"], dict)
        assert isinstance(report_dict["quality_metrics"], dict)
        
        # Verify all values are JSON-serializable types
        import json
        json_str = json.dumps(report_dict)
        assert isinstance(json_str, str)
    
    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-009",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1050.0,
            files_processed=10,
            phase_metadata={
                "validation": {
                    "total": 10,
                    "passed": 8,
                    "syntax_errors": 1,
                    "dependency_issues": 2
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.quality_metrics.total_validations == 10
        assert report.quality_metrics.passed_validations == 8
        assert report.quality_metrics.validation_pass_rate == 80.0
        assert report.quality_metrics.dependency_resolution_rate == 80.0  # 8/10
        assert report.quality_metrics.syntax_error_rate == 10.0  # 1/10
    
    def test_quality_metrics_zero_validations(self):
        """Test quality metrics with zero validations."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-010",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1050.0,
            files_processed=5,
            phase_metadata={
                "validation": {
                    "total": 0,
                    "passed": 0,
                    "syntax_errors": 0,
                    "dependency_issues": 0
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.quality_metrics.validation_pass_rate == 0.0
        assert report.quality_metrics.dependency_resolution_rate == 0.0
        assert report.quality_metrics.syntax_error_rate == 0.0
    
    def test_timeout_detection(self):
        """Test timeout detection in runtime metrics."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-011",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1500.0,
            files_processed=5,
            phase_metadata={
                "phase_runtimes": {
                    "ingestion": 50.0,
                    "parsing": 100.0,
                    "translation": 350.0  # Exceeds 300s threshold
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.runtime_metrics.timeout_detected is True
    
    def test_efficiency_score_calculation(self):
        """Test efficiency score calculation with various scenarios."""
        # Scenario 1: High reduction, high success
        eval_input1 = EvaluationInput(
            repo_id="test-repo-012a",
            naive_token_count=10000,
            optimized_token_count=2000,  # 80% reduction
            start_time=1000.0,
            end_time=1100.0,
            files_processed=50,
            errors_encountered=0
        )
        report1 = self.evaluator.evaluate(eval_input1)
        
        # Scenario 2: Low reduction, low success
        eval_input2 = EvaluationInput(
            repo_id="test-repo-012b",
            naive_token_count=10000,
            optimized_token_count=9000,  # 10% reduction
            start_time=1000.0,
            end_time=1100.0,
            files_processed=5,
            errors_encountered=5
        )
        report2 = self.evaluator.evaluate(eval_input2)
        
        # Assert
        assert report1.token_metrics.efficiency_score > report2.token_metrics.efficiency_score
        assert 0 <= report1.token_metrics.efficiency_score <= 100
        assert 0 <= report2.token_metrics.efficiency_score <= 100
    
    def test_summary_text_generation(self):
        """Test summary text generation."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-013",
            naive_token_count=8000,
            optimized_token_count=5000,
            start_time=1000.0,
            end_time=1120.0,
            files_processed=10,
            errors_encountered=2,
            phase_metadata={
                "validation": {
                    "total": 10,
                    "passed": 8,
                    "syntax_errors": 1,
                    "dependency_issues": 1
                }
            }
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert "test-repo-013" in report.summary_text
        assert "Token Efficiency" in report.summary_text
        assert "Runtime Performance" in report.summary_text
        assert "Quality Metrics" in report.summary_text
        assert "3,000" in report.summary_text  # Token reduction
        assert "37.5%" in report.summary_text  # Reduction percentage
    
    def test_timestamp_format(self):
        """Test timestamp is in ISO format."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-014",
            naive_token_count=5000,
            optimized_token_count=3000,
            start_time=1000.0,
            end_time=1050.0,
            files_processed=5
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        # Verify it's parseable as ISO format (accepts both Z and +00:00)
        assert report.timestamp.endswith("+00:00") or report.timestamp.endswith("Z")
        datetime.fromisoformat(report.timestamp.replace("Z", "+00:00"))
    
    def test_negative_token_reduction(self):
        """Test case where optimization increases tokens (edge case)."""
        # Arrange
        eval_input = EvaluationInput(
            repo_id="test-repo-015",
            naive_token_count=5000,
            optimized_token_count=6000,  # Increased tokens
            start_time=1000.0,
            end_time=1050.0,
            files_processed=5
        )
        
        # Act
        report = self.evaluator.evaluate(eval_input)
        
        # Assert
        assert report.token_metrics.token_reduction == -1000
        assert report.token_metrics.reduction_percentage == -20.0
        # Efficiency score should still be calculated
        assert report.token_metrics.efficiency_score >= 0.0


class TestTokenMetrics:
    """Test suite for TokenMetrics dataclass."""
    
    def test_token_metrics_to_dict(self):
        """Test TokenMetrics to_dict() method."""
        # Arrange
        metrics = TokenMetrics(
            naive_token_count=10000,
            optimized_token_count=6000,
            token_reduction=4000,
            reduction_percentage=40.0,
            tokens_per_file=600.0,
            efficiency_score=75.5
        )
        
        # Act
        metrics_dict = metrics.to_dict()
        
        # Assert
        assert metrics_dict["naive_token_count"] == 10000
        assert metrics_dict["optimized_token_count"] == 6000
        assert metrics_dict["token_reduction"] == 4000
        assert metrics_dict["reduction_percentage"] == 40.0
        assert metrics_dict["tokens_per_file"] == 600.0
        assert metrics_dict["efficiency_score"] == 75.5


class TestRuntimeMetrics:
    """Test suite for RuntimeMetrics dataclass."""
    
    def test_runtime_metrics_to_dict(self):
        """Test RuntimeMetrics to_dict() method."""
        # Arrange
        metrics = RuntimeMetrics(
            total_runtime_seconds=120.5,
            runtime_per_file=12.05,
            runtime_per_phase={"parsing": 50.0, "translation": 70.5},
            timeout_detected=False
        )
        
        # Act
        metrics_dict = metrics.to_dict()
        
        # Assert
        assert metrics_dict["total_runtime_seconds"] == 120.5
        assert metrics_dict["runtime_per_file"] == 12.05
        assert metrics_dict["runtime_per_phase"] == {"parsing": 50.0, "translation": 70.5}
        assert metrics_dict["timeout_detected"] is False


class TestQualityMetrics:
    """Test suite for QualityMetrics dataclass."""
    
    def test_quality_metrics_to_dict(self):
        """Test QualityMetrics to_dict() method."""
        # Arrange
        metrics = QualityMetrics(
            validation_pass_rate=80.0,
            dependency_resolution_rate=90.0,
            syntax_error_rate=10.0,
            total_validations=10,
            passed_validations=8
        )
        
        # Act
        metrics_dict = metrics.to_dict()
        
        # Assert
        assert metrics_dict["validation_pass_rate"] == 80.0
        assert metrics_dict["dependency_resolution_rate"] == 90.0
        assert metrics_dict["syntax_error_rate"] == 10.0
        assert metrics_dict["total_validations"] == 10
        assert metrics_dict["passed_validations"] == 8


class TestEvaluationReport:
    """Test suite for EvaluationReport dataclass."""
    
    def test_evaluation_report_to_dict(self):
        """Test EvaluationReport to_dict() method."""
        # Arrange
        token_metrics = TokenMetrics(
            naive_token_count=10000,
            optimized_token_count=6000,
            token_reduction=4000,
            reduction_percentage=40.0,
            tokens_per_file=600.0,
            efficiency_score=75.0
        )
        
        runtime_metrics = RuntimeMetrics(
            total_runtime_seconds=120.0,
            runtime_per_file=12.0,
            runtime_per_phase={"parsing": 50.0},
            timeout_detected=False
        )
        
        quality_metrics = QualityMetrics(
            validation_pass_rate=80.0,
            dependency_resolution_rate=90.0,
            syntax_error_rate=10.0,
            total_validations=10,
            passed_validations=8
        )
        
        report = EvaluationReport(
            repo_id="test-repo",
            token_metrics=token_metrics,
            runtime_metrics=runtime_metrics,
            quality_metrics=quality_metrics,
            summary_text="Test summary",
            timestamp="2024-01-01T00:00:00Z"
        )
        
        # Act
        report_dict = report.to_dict()
        
        # Assert
        assert report_dict["repo_id"] == "test-repo"
        assert isinstance(report_dict["token_metrics"], dict)
        assert isinstance(report_dict["runtime_metrics"], dict)
        assert isinstance(report_dict["quality_metrics"], dict)
        assert report_dict["summary_text"] == "Test summary"
        assert report_dict["timestamp"] == "2024-01-01T00:00:00Z"
