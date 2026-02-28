"""Tests for AuditEngine."""

import pytest
from app.validation import ValidationReport
from app.audit import AuditEngine, AuditReport, CheckResult
from app.core.config import get_settings


@pytest.fixture
def audit_engine():
    """Create AuditEngine instance."""
    return AuditEngine()


@pytest.fixture
def valid_report():
    """Create a valid validation report."""
    return ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="""def test_example():
    \"\"\"Test for example.\"\"\"
    # TODO: Set up test data
    result = example()
    assert result is not None
""",
        errors=[]
    )


@pytest.fixture
def invalid_report():
    """Create an invalid validation report."""
    return ValidationReport(
        structure_valid=False,
        symbols_preserved=False,
        syntax_valid=False,
        dependencies_complete=False,
        missing_dependencies=["missing_func"],
        unit_test_stub="def test_example(): pass",
        errors=[
            "Syntax error at line 5: invalid syntax",
            "Missing called symbols: missing_func",
            "Parameter count mismatch: expected 2, got 1"
        ]
    )


def test_audit_engine_initialization(audit_engine):
    """Test AuditEngine initialization."""
    assert audit_engine is not None
    assert audit_engine.config is not None
    assert len(audit_engine._llm_indicators) > 0
    assert len(audit_engine._incomplete_markers) > 0


def test_run_audit_with_valid_reports(audit_engine, valid_report):
    """Test audit with all valid reports."""
    validation_reports = [valid_report, valid_report]
    documentation = {
        "module1": "This is documentation for module1 with function references.",
        "module2": "This is documentation for module2 with class definitions."
    }
    
    report = audit_engine.run_audit(validation_reports, documentation)
    
    assert isinstance(report, AuditReport)
    assert report.total_checks > 0
    assert report.passed_checks >= 0
    assert report.failed_checks >= 0
    assert report.passed_checks + report.failed_checks == report.total_checks
    assert report.execution_time_ms > 0
    assert report.timestamp is not None


def test_run_audit_with_invalid_reports(audit_engine, invalid_report):
    """Test audit with invalid reports."""
    validation_reports = [invalid_report]
    documentation = {"module1": "Documentation"}
    
    report = audit_engine.run_audit(validation_reports, documentation)
    
    assert isinstance(report, AuditReport)
    assert report.total_checks > 0


def test_validation_determinism_check(audit_engine, valid_report):
    """Test validation determinism check."""
    result = audit_engine._check_validation_determinism([valid_report])
    
    assert isinstance(result, CheckResult)
    assert result.check_name == "Validation Determinism"
    assert result.passed is True
    assert "determinism" in result.message.lower()


def test_validation_determinism_with_none_values(audit_engine):
    """Test determinism check catches None values."""
    bad_report = ValidationReport(
        structure_valid=None,  # Should be bool
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test(): pass",
        errors=[]
    )
    
    result = audit_engine._check_validation_determinism([bad_report])
    
    assert result.passed is False
    assert len(result.details["issues"]) > 0


def test_llm_leakage_check_clean(audit_engine, valid_report):
    """Test LLM leakage check with clean data."""
    documentation = {"module1": "Clean documentation without API keys"}
    
    result = audit_engine._check_llm_leakage([valid_report], documentation)
    
    assert isinstance(result, CheckResult)
    assert result.check_name == "LLM Leakage Prevention"
    assert result.passed is True


def test_llm_leakage_check_detects_api_key(audit_engine, valid_report):
    """Test LLM leakage check detects API keys."""
    documentation = {
        "module1": "Documentation with api_key: AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz123456"
    }
    
    result = audit_engine._check_llm_leakage([valid_report], documentation)
    
    assert result.passed is False
    assert len(result.details["issues"]) > 0


def test_llm_leakage_check_detects_llm_terms(audit_engine):
    """Test LLM leakage check detects LLM terms in errors."""
    report_with_llm = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test(): pass",
        errors=["Error calling Gemini API"]
    )
    
    result = audit_engine._check_llm_leakage([report_with_llm], {})
    
    assert result.passed is False


def test_config_compliance_check(audit_engine, valid_report):
    """Test configuration compliance check."""
    config = get_settings()
    
    result = audit_engine._check_config_compliance([valid_report], config)
    
    assert isinstance(result, CheckResult)
    assert result.check_name == "Configuration Compliance"
    assert result.passed is True


def test_dependency_graph_integrity_check(audit_engine):
    """Test dependency graph integrity check."""
    # Inconsistent report: dependencies_complete=False but no missing deps
    bad_report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=False,
        missing_dependencies=[],  # Should have entries
        unit_test_stub="def test(): pass",
        errors=[]
    )
    
    result = audit_engine._check_dependency_graph_integrity([bad_report])
    
    assert result.passed is False
    assert len(result.details["issues"]) > 0


def test_dependency_graph_integrity_valid(audit_engine):
    """Test dependency graph integrity with valid data."""
    good_report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=False,
        missing_dependencies=["func1", "func2"],
        unit_test_stub="def test(): pass",
        errors=["Missing dependencies: func1, func2"]
    )
    
    result = audit_engine._check_dependency_graph_integrity([good_report])
    
    assert result.passed is True


def test_syntax_robustness_check(audit_engine):
    """Test syntax robustness check."""
    report_with_syntax_error = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=False,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test(): pass",
        errors=["Syntax error at line 10: invalid syntax"]
    )
    
    result = audit_engine._check_syntax_robustness([report_with_syntax_error])
    
    assert result.passed is True
    assert result.details["syntax_errors_found"] == 1


def test_syntax_robustness_missing_error(audit_engine):
    """Test syntax robustness detects missing error messages."""
    bad_report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=False,  # Invalid but no error message
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test(): pass",
        errors=[]
    )
    
    result = audit_engine._check_syntax_robustness([bad_report])
    
    assert result.passed is False


def test_structure_validation_check(audit_engine):
    """Test structure validation check."""
    report_with_structure_error = ValidationReport(
        structure_valid=False,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test(): pass",
        errors=["Parameter count mismatch: expected 2, got 1"]
    )
    
    result = audit_engine._check_structure_validation([report_with_structure_error])
    
    assert result.passed is True
    assert result.details["structure_failures"] == 1


def test_symbol_preservation_check(audit_engine):
    """Test symbol preservation check."""
    report_with_missing_symbols = ValidationReport(
        structure_valid=True,
        symbols_preserved=False,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test(): pass",
        errors=["Missing called symbols: func1, func2"]
    )
    
    result = audit_engine._check_symbol_preservation([report_with_missing_symbols])
    
    assert result.passed is True
    assert result.details["symbol_failures"] == 1


def test_translation_completeness_check(audit_engine):
    """Test translation completeness check."""
    report_with_todo = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test(): pass",
        errors=["Incomplete translation markers found: TODO"]
    )
    
    result = audit_engine._check_translation_completeness([report_with_todo])
    
    assert result.passed is True
    assert result.details["incomplete_translations"] == 1


def test_unit_test_quality_check(audit_engine, valid_report):
    """Test unit test quality check."""
    result = audit_engine._check_unit_test_quality([valid_report])
    
    assert isinstance(result, CheckResult)
    assert result.check_name == "Unit Test Stub Quality"
    assert result.passed is True


def test_unit_test_quality_empty_stub(audit_engine):
    """Test unit test quality detects empty stubs."""
    bad_report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="",  # Empty
        errors=[]
    )
    
    result = audit_engine._check_unit_test_quality([bad_report])
    
    assert result.passed is False


def test_unit_test_quality_bad_naming(audit_engine):
    """Test unit test quality detects bad naming."""
    bad_report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def example(): pass",  # Doesn't start with test_
        errors=[]
    )
    
    result = audit_engine._check_unit_test_quality([bad_report])
    
    assert result.passed is False


def test_documentation_accuracy_check(audit_engine, valid_report):
    """Test documentation accuracy check."""
    documentation = {
        "module1": "Documentation with function and class references"
    }
    
    result = audit_engine._check_documentation_accuracy([valid_report], documentation)
    
    assert isinstance(result, CheckResult)
    assert result.check_name == "Documentation Accuracy"
    assert result.passed is True


def test_documentation_accuracy_empty_docs(audit_engine, valid_report):
    """Test documentation accuracy detects empty docs."""
    documentation = {"module1": ""}
    
    result = audit_engine._check_documentation_accuracy([valid_report], documentation)
    
    assert result.passed is False


def test_report_schema_check(audit_engine, valid_report):
    """Test report schema check."""
    result = audit_engine._check_report_schema([valid_report])
    
    assert isinstance(result, CheckResult)
    assert result.check_name == "Report Schema Consistency"
    assert result.passed is True


def test_report_schema_wrong_types(audit_engine):
    """Test report schema detects wrong types."""
    # Create report with wrong types (bypassing dataclass validation)
    bad_report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies="not a list",  # Should be list
        unit_test_stub="def test(): pass",
        errors=[]
    )
    
    result = audit_engine._check_report_schema([bad_report])
    
    assert result.passed is False


def test_performance_check(audit_engine, valid_report):
    """Test performance check."""
    documentation = {"module1": "Normal sized documentation"}
    
    result = audit_engine._check_performance([valid_report], documentation)
    
    assert isinstance(result, CheckResult)
    assert result.check_name == "Performance Validation"
    assert result.passed is True


def test_pipeline_sequence_check(audit_engine, valid_report):
    """Test pipeline sequence check."""
    result = audit_engine._check_pipeline_sequence([valid_report])
    
    assert isinstance(result, CheckResult)
    assert result.check_name == "Pipeline Sequence Integrity"
    assert result.passed is True


def test_pipeline_sequence_empty_reports(audit_engine):
    """Test pipeline sequence with no reports."""
    result = audit_engine._check_pipeline_sequence([])
    
    assert result.passed is True
    assert len(result.warnings) > 0


def test_audit_report_structure(audit_engine, valid_report):
    """Test AuditReport structure."""
    report = audit_engine.run_audit([valid_report], {"module1": "docs"})
    
    assert hasattr(report, 'overall_passed')
    assert hasattr(report, 'total_checks')
    assert hasattr(report, 'passed_checks')
    assert hasattr(report, 'failed_checks')
    assert hasattr(report, 'check_results')
    assert hasattr(report, 'execution_time_ms')
    assert hasattr(report, 'timestamp')
    assert hasattr(report, 'summary')
    
    assert isinstance(report.check_results, list)
    assert all(isinstance(r, CheckResult) for r in report.check_results)


def test_check_result_structure():
    """Test CheckResult structure."""
    result = CheckResult(
        check_name="Test Check",
        passed=True,
        message="Test message",
        details={"key": "value"},
        warnings=["warning1"]
    )
    
    assert result.check_name == "Test Check"
    assert result.passed is True
    assert result.message == "Test message"
    assert result.details == {"key": "value"}
    assert result.warnings == ["warning1"]


def test_full_audit_integration(audit_engine):
    """Test full audit integration with mixed reports."""
    reports = [
        ValidationReport(
            structure_valid=True,
            symbols_preserved=True,
            syntax_valid=True,
            dependencies_complete=True,
            missing_dependencies=[],
            unit_test_stub="def test_func1(): assert True",
            errors=[]
        ),
        ValidationReport(
            structure_valid=False,
            symbols_preserved=False,
            syntax_valid=False,
            dependencies_complete=False,
            missing_dependencies=["dep1"],
            unit_test_stub="def test_func2(): pass",
            errors=["Syntax error", "Missing symbols"]
        )
    ]
    
    documentation = {
        "module1": "Documentation for module1 with function references",
        "module2": "Documentation for module2 with class definitions"
    }
    
    audit_report = audit_engine.run_audit(reports, documentation)
    
    assert audit_report.total_checks == 13  # All checks
    assert audit_report.passed_checks + audit_report.failed_checks == audit_report.total_checks
    assert len(audit_report.check_results) == 13
    assert audit_report.summary is not None
    assert len(audit_report.summary) > 0
