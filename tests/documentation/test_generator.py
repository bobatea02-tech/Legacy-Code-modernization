"""Unit tests for DocumentationGenerator.

Tests cover:
- Documentation generation from translation results
- Validation report integration
- Evaluation report integration
- JSON serialization
- Immutability of inputs
"""

import pytest
from dataclasses import dataclass
from typing import List

from app.documentation.generator import DocumentationGenerator, DocumentationReport


@dataclass
class MockTranslationResult:
    """Mock TranslationResult for testing."""
    module_name: str
    status: str
    translated_code: str
    dependencies_used: List[str]
    token_usage: int
    errors: List[str]
    warnings: List[str]


@dataclass
class MockValidationReport:
    """Mock ValidationReport for testing."""
    structure_valid: bool
    symbols_preserved: bool
    syntax_valid: bool
    dependencies_complete: bool
    missing_dependencies: List[str]
    errors: List[str]


class TestDocumentationGenerator:
    """Test suite for DocumentationGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = DocumentationGenerator()
    
    def test_generator_initialization(self):
        """Test generator initializes correctly."""
        assert self.generator is not None
    
    def test_generate_documentation_basic(self):
        """Test basic documentation generation."""
        # Arrange
        translation_results = [
            MockTranslationResult(
                module_name="test_module",
                status="success",
                translated_code="def test(): pass",
                dependencies_used=["dep1"],
                token_usage=100,
                errors=[],
                warnings=[]
            )
        ]
        
        validation_reports = [
            MockValidationReport(
                structure_valid=True,
                symbols_preserved=True,
                syntax_valid=True,
                dependencies_complete=True,
                missing_dependencies=[],
                errors=[]
            )
        ]
        
        # Act
        docs = self.generator.generate_documentation(
            translation_results,
            validation_reports
        )
        
        # Assert
        assert "test_module" in docs
        assert isinstance(docs["test_module"], str)
        assert "test_module" in docs["test_module"]
        assert "Translation Summary" in docs["test_module"]
    
    def test_generate_documentation_with_evaluation(self):
        """Test documentation generation with evaluation report."""
        # Arrange
        translation_results = [
            MockTranslationResult(
                module_name="test_module",
                status="success",
                translated_code="def test(): pass",
                dependencies_used=[],
                token_usage=50,
                errors=[],
                warnings=[]
            )
        ]
        
        validation_reports = [
            MockValidationReport(
                structure_valid=True,
                symbols_preserved=True,
                syntax_valid=True,
                dependencies_complete=True,
                missing_dependencies=[],
                errors=[]
            )
        ]
        
        evaluation_report = {
            "token_metrics": {
                "reduction_percentage": 40.0,
                "efficiency_score": 75.0
            },
            "quality_metrics": {
                "validation_pass_rate": 100.0,
                "syntax_error_rate": 0.0
            }
        }
        
        # Act
        docs = self.generator.generate_documentation(
            translation_results,
            validation_reports,
            evaluation_report
        )
        
        # Assert
        assert "test_module" in docs
        assert "Evaluation Metrics" in docs["test_module"]
        assert "Token Efficiency" in docs["test_module"]
        assert "40.0%" in docs["test_module"]
    
    def test_generate_report_structure(self):
        """Test DocumentationReport structure."""
        # Arrange
        translation_result = MockTranslationResult(
            module_name="test_module",
            status="success",
            translated_code="def test(): pass",
            dependencies_used=["dep1", "dep2"],
            token_usage=100,
            errors=[],
            warnings=[]
        )
        
        validation_report = MockValidationReport(
            structure_valid=True,
            symbols_preserved=True,
            syntax_valid=True,
            dependencies_complete=True,
            missing_dependencies=[],
            errors=[]
        )
        
        evaluation_report = {
            "token_metrics": {"reduction_percentage": 30.0},
            "prompt_metadata": {
                "code_translation": {
                    "version": "1.0.0",
                    "checksum": "abc123",
                    "model_name": "gemini-pro"
                }
            }
        }
        
        # Act
        report = self.generator.generate_report(
            translation_result,
            validation_report,
            evaluation_report
        )
        
        # Assert
        assert isinstance(report, DocumentationReport)
        assert report.module_name == "test_module"
        assert isinstance(report.translation_summary, dict)
        assert isinstance(report.validation_status, dict)
        assert isinstance(report.evaluation_metrics, dict)
        assert isinstance(report.prompt_metadata, dict)
        assert report.timestamp != ""
    
    def test_report_json_serialization(self):
        """Test DocumentationReport JSON serialization."""
        # Arrange
        translation_result = MockTranslationResult(
            module_name="test_module",
            status="success",
            translated_code="def test(): pass",
            dependencies_used=[],
            token_usage=50,
            errors=[],
            warnings=[]
        )
        
        validation_report = MockValidationReport(
            structure_valid=True,
            symbols_preserved=True,
            syntax_valid=True,
            dependencies_complete=True,
            missing_dependencies=[],
            errors=[]
        )
        
        # Act
        report = self.generator.generate_report(
            translation_result,
            validation_report
        )
        report_dict = report.to_dict()
        
        # Assert
        assert isinstance(report_dict, dict)
        assert "module_name" in report_dict
        assert "translation_summary" in report_dict
        assert "validation_status" in report_dict
        assert "evaluation_metrics" in report_dict
        assert "prompt_metadata" in report_dict
        assert "timestamp" in report_dict
        
        # Verify JSON serializable
        import json
        json_str = json.dumps(report_dict)
        assert isinstance(json_str, str)
    
    def test_documentation_with_validation_errors(self):
        """Test documentation includes validation errors."""
        # Arrange
        translation_results = [
            MockTranslationResult(
                module_name="test_module",
                status="success",
                translated_code="def test(): pass",
                dependencies_used=[],
                token_usage=50,
                errors=[],
                warnings=[]
            )
        ]
        
        validation_reports = [
            MockValidationReport(
                structure_valid=False,
                symbols_preserved=False,
                syntax_valid=True,
                dependencies_complete=False,
                missing_dependencies=["dep1", "dep2"],
                errors=["Structure error", "Symbol error"]
            )
        ]
        
        # Act
        docs = self.generator.generate_documentation(
            translation_results,
            validation_reports
        )
        
        # Assert
        assert "test_module" in docs
        assert "Validation Errors" in docs["test_module"]
        assert "Structure error" in docs["test_module"]
        assert "Missing Dependencies" in docs["test_module"]
        assert "dep1" in docs["test_module"]
    
    def test_documentation_with_warnings(self):
        """Test documentation includes translation warnings."""
        # Arrange
        translation_results = [
            MockTranslationResult(
                module_name="test_module",
                status="success",
                translated_code="def test(): pass",
                dependencies_used=[],
                token_usage=50,
                errors=[],
                warnings=["Warning 1", "Warning 2"]
            )
        ]
        
        validation_reports = [
            MockValidationReport(
                structure_valid=True,
                symbols_preserved=True,
                syntax_valid=True,
                dependencies_complete=True,
                missing_dependencies=[],
                errors=[]
            )
        ]
        
        # Act
        docs = self.generator.generate_documentation(
            translation_results,
            validation_reports
        )
        
        # Assert
        assert "test_module" in docs
        assert "Warnings" in docs["test_module"]
        assert "Warning 1" in docs["test_module"]
    
    def test_multiple_modules_documentation(self):
        """Test documentation generation for multiple modules."""
        # Arrange
        translation_results = [
            MockTranslationResult(
                module_name="module1",
                status="success",
                translated_code="def test1(): pass",
                dependencies_used=[],
                token_usage=50,
                errors=[],
                warnings=[]
            ),
            MockTranslationResult(
                module_name="module2",
                status="success",
                translated_code="def test2(): pass",
                dependencies_used=[],
                token_usage=60,
                errors=[],
                warnings=[]
            )
        ]
        
        validation_reports = [
            MockValidationReport(
                structure_valid=True,
                symbols_preserved=True,
                syntax_valid=True,
                dependencies_complete=True,
                missing_dependencies=[],
                errors=[]
            ),
            MockValidationReport(
                structure_valid=True,
                symbols_preserved=True,
                syntax_valid=True,
                dependencies_complete=True,
                missing_dependencies=[],
                errors=[]
            )
        ]
        
        # Act
        docs = self.generator.generate_documentation(
            translation_results,
            validation_reports
        )
        
        # Assert
        assert len(docs) == 2
        assert "module1" in docs
        assert "module2" in docs
    
    def test_immutability_of_inputs(self):
        """Test that generator does not mutate input objects."""
        # Arrange
        translation_results = [
            MockTranslationResult(
                module_name="test_module",
                status="success",
                translated_code="def test(): pass",
                dependencies_used=["dep1"],
                token_usage=100,
                errors=[],
                warnings=[]
            )
        ]
        
        validation_reports = [
            MockValidationReport(
                structure_valid=True,
                symbols_preserved=True,
                syntax_valid=True,
                dependencies_complete=True,
                missing_dependencies=[],
                errors=[]
            )
        ]
        
        # Store original values
        original_module_name = translation_results[0].module_name
        original_code = translation_results[0].translated_code
        original_structure_valid = validation_reports[0].structure_valid
        
        # Act
        self.generator.generate_documentation(
            translation_results,
            validation_reports
        )
        
        # Assert - inputs should be unchanged
        assert translation_results[0].module_name == original_module_name
        assert translation_results[0].translated_code == original_code
        assert validation_reports[0].structure_valid == original_structure_valid
    
    def test_empty_translation_results(self):
        """Test documentation generation with empty results."""
        # Arrange
        translation_results = []
        validation_reports = []
        
        # Act
        docs = self.generator.generate_documentation(
            translation_results,
            validation_reports
        )
        
        # Assert
        assert isinstance(docs, dict)
        assert len(docs) == 0
    
    def test_code_preview_truncation(self):
        """Test that long code is truncated in documentation."""
        # Arrange
        long_code = "def test(): pass\n" * 100  # Very long code
        
        translation_results = [
            MockTranslationResult(
                module_name="test_module",
                status="success",
                translated_code=long_code,
                dependencies_used=[],
                token_usage=1000,
                errors=[],
                warnings=[]
            )
        ]
        
        validation_reports = [
            MockValidationReport(
                structure_valid=True,
                symbols_preserved=True,
                syntax_valid=True,
                dependencies_complete=True,
                missing_dependencies=[],
                errors=[]
            )
        ]
        
        # Act
        docs = self.generator.generate_documentation(
            translation_results,
            validation_reports
        )
        
        # Assert
        assert "test_module" in docs
        # Code should be truncated with "..."
        assert "..." in docs["test_module"]
        # Full code should not be in documentation
        assert len(docs["test_module"]) < len(long_code)
