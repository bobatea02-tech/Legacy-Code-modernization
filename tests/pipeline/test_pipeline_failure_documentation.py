"""Test pipeline documentation generation with failures.

This test verifies that:
1. Documentation can be generated even when evaluation_report is None
2. Pipeline phases can fail gracefully without breaking documentation
3. Documentation generator handles optional evaluation_report correctly
"""

import pytest
from app.documentation.generator import DocumentationGenerator
from app.translation.orchestrator import TranslationResult, TranslationStatus
from app.validation.validator import ValidationReport


class TestPipelineFailureDocumentation:
    """Test suite for documentation generation with pipeline failures."""
    
    def test_documentation_without_evaluation_report(self):
        """Test that documentation can be generated without evaluation report."""
        generator = DocumentationGenerator()
        
        # Create mock translation result
        translation_result = TranslationResult(
            module_name="test_module",
            status=TranslationStatus.SUCCESS,
            translated_code="def test():\n    pass",
            dependencies_used=["dep1", "dep2"],
            token_usage=100
        )
        
        # Create mock validation report (no module_name field)
        validation_report = ValidationReport(
            syntax_valid=True,
            structure_valid=True,
            symbols_preserved=True,
            dependencies_complete=True,
            missing_dependencies=[],
            unit_test_stub="",
            errors=[]
        )
        
        # Generate documentation WITHOUT evaluation_report (None)
        documentation = generator.generate_documentation(
            translation_results=[translation_result],
            validation_reports=[validation_report],
            evaluation_report=None  # This should not cause an error
        )
        
        assert "test_module" in documentation
        assert len(documentation["test_module"]) > 0
        assert "Translation Summary" in documentation["test_module"]
        assert "Validation Status" in documentation["test_module"]
        # Should NOT contain evaluation metrics section
        assert "Evaluation Metrics" not in documentation["test_module"]
    
    def test_documentation_with_evaluation_report(self):
        """Test that documentation includes evaluation metrics when provided."""
        generator = DocumentationGenerator()
        
        # Create mock translation result
        translation_result = TranslationResult(
            module_name="test_module",
            status=TranslationStatus.SUCCESS,
            translated_code="def test():\n    pass",
            dependencies_used=["dep1", "dep2"],
            token_usage=100
        )
        
        # Create mock validation report
        validation_report = ValidationReport(
            syntax_valid=True,
            structure_valid=True,
            symbols_preserved=True,
            dependencies_complete=True,
            missing_dependencies=[],
            unit_test_stub="",
            errors=[]
        )
        
        # Create mock evaluation report
        evaluation_report = {
            "token_metrics": {
                "efficiency_score": 85,
                "reduction_percentage": 42.5,
                "naive_tokens": 1000,
                "optimized_tokens": 575
            },
            "performance_metrics": {
                "total_runtime": 10.5,
                "throughput": 5.2
            }
        }
        
        # Generate documentation WITH evaluation_report
        documentation = generator.generate_documentation(
            translation_results=[translation_result],
            validation_reports=[validation_report],
            evaluation_report=evaluation_report
        )
        
        assert "test_module" in documentation
        assert "Evaluation Metrics" in documentation["test_module"]
        assert "Token Efficiency" in documentation["test_module"]
    
    def test_documentation_with_failed_translation(self):
        """Test documentation generation when translation fails."""
        generator = DocumentationGenerator()
        
        # Create failed translation result
        translation_result = TranslationResult(
            module_name="failed_module",
            status=TranslationStatus.FAILED,
            translated_code="",
            dependencies_used=[],
            token_usage=0,
            errors=["Translation failed: LLM timeout"]
        )
        
        # No validation report for failed translation
        validation_reports = []
        
        # Generate documentation for failed translation
        documentation = generator.generate_documentation(
            translation_results=[translation_result],
            validation_reports=validation_reports,
            evaluation_report=None
        )
        
        # Should still generate documentation for failed module
        # (though it may be empty if no translated_code)
        assert isinstance(documentation, dict)
    
    def test_documentation_with_validation_errors(self):
        """Test documentation includes validation errors."""
        generator = DocumentationGenerator()
        
        # Create translation result
        translation_result = TranslationResult(
            module_name="test_module",
            status=TranslationStatus.SUCCESS,
            translated_code="def test():\n    pass",
            dependencies_used=["dep1"],
            token_usage=100
        )
        
        # Create validation report with errors
        validation_report = ValidationReport(
            syntax_valid=False,
            structure_valid=True,
            symbols_preserved=False,
            dependencies_complete=False,
            missing_dependencies=["missing_dep"],
            unit_test_stub="",
            errors=["Syntax error on line 5", "Symbol 'foo' not found"]
        )
        
        # Generate documentation
        documentation = generator.generate_documentation(
            translation_results=[translation_result],
            validation_reports=[validation_report],
            evaluation_report=None
        )
        
        assert "test_module" in documentation
        assert "Validation Errors" in documentation["test_module"]
        assert "Missing Dependencies" in documentation["test_module"]
        assert "missing_dep" in documentation["test_module"]
    
    def test_documentation_empty_results(self):
        """Test documentation generation with empty results."""
        generator = DocumentationGenerator()
        
        # Generate documentation with empty inputs
        documentation = generator.generate_documentation(
            translation_results=[],
            validation_reports=[],
            evaluation_report=None
        )
        
        assert isinstance(documentation, dict)
        assert len(documentation) == 0
    
    def test_documentation_mismatched_counts(self):
        """Test documentation when translation and validation counts don't match."""
        generator = DocumentationGenerator()
        
        # Create 2 translation results
        translation_results = [
            TranslationResult(
                module_name="module1",
                status=TranslationStatus.SUCCESS,
                translated_code="def test1():\n    pass",
                dependencies_used=[],
                token_usage=50
            ),
            TranslationResult(
                module_name="module2",
                status=TranslationStatus.SUCCESS,
                translated_code="def test2():\n    pass",
                dependencies_used=[],
                token_usage=50
            )
        ]
        
        # Create only 1 validation report
        validation_reports = [
            ValidationReport(
                syntax_valid=True,
                structure_valid=True,
                symbols_preserved=True,
                dependencies_complete=True,
                missing_dependencies=[],
                unit_test_stub="",
                errors=[]
            )
        ]
        
        # Should handle mismatched counts gracefully
        documentation = generator.generate_documentation(
            translation_results=translation_results,
            validation_reports=validation_reports,
            evaluation_report=None
        )
        
        assert len(documentation) == 2  # Both modules should have documentation
        assert "module1" in documentation
        assert "module2" in documentation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
