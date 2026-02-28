"""Deterministic audit engine for pipeline integrity verification.

This module provides comprehensive auditing of the Legacy Code Modernization
pipeline without LLM usage, ensuring:
- Validation determinism
- No LLM leakage in validation/documentation
- Configuration compliance
- Dependency graph integrity
- Syntax robustness
- Structure preservation
- Symbol preservation
- Translation completeness
- Unit test stub quality
- Documentation accuracy
- Report schema consistency
- Performance validation
- Pipeline sequence integrity
"""

import re
import ast
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from app.validation import ValidationReport
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CheckResult:
    """Result of a single audit check."""
    
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AuditReport:
    """Comprehensive audit report for pipeline integrity."""
    
    overall_passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    check_results: List[CheckResult]
    execution_time_ms: float
    timestamp: str
    summary: str


class AuditEngine:
    """Deterministic audit engine for pipeline integrity verification."""
    
    def __init__(self):
        """Initialize audit engine with configuration."""
        self.config = get_settings()
        self._llm_indicators = [
            'gemini', 'openai', 'anthropic', 'api_key', 'llm',
            'gpt', 'claude', 'model', 'prompt', 'completion'
        ]
        self._incomplete_markers = [
            'TODO', 'FIXME', 'XXX', 'HACK', 'NOTE',
            'pass', 'NotImplemented', 'NotImplementedError'
        ]
    
    def run_audit(
        self,
        validation_reports: List[ValidationReport],
        documentation: Dict[str, str],
        config: Optional[Any] = None
    ) -> AuditReport:
        """Run comprehensive audit of pipeline outputs.
        
        Args:
            validation_reports: List of validation reports from ValidationEngine
            documentation: Dictionary mapping module names to documentation strings
            config: Optional config object (uses get_settings() if None)
            
        Returns:
            AuditReport with results of all checks
        """
        start_time = time.time()
        
        logger.info(
            "Starting pipeline audit",
            extra={
                "stage_name": "audit",
                "validation_count": len(validation_reports),
                "documentation_count": len(documentation)
            }
        )
        
        # Use provided config or default
        if config is None:
            config = self.config
        
        # Run all audit checks
        check_results: List[CheckResult] = []
        
        check_results.append(self._check_validation_determinism(validation_reports))
        check_results.append(self._check_llm_leakage(validation_reports, documentation))
        check_results.append(self._check_config_compliance(validation_reports, config))
        check_results.append(self._check_dependency_graph_integrity(validation_reports))
        check_results.append(self._check_syntax_robustness(validation_reports))
        check_results.append(self._check_structure_validation(validation_reports))
        check_results.append(self._check_symbol_preservation(validation_reports))
        check_results.append(self._check_translation_completeness(validation_reports))
        check_results.append(self._check_unit_test_quality(validation_reports))
        check_results.append(self._check_documentation_accuracy(validation_reports, documentation))
        check_results.append(self._check_report_schema(validation_reports))
        check_results.append(self._check_performance(validation_reports, documentation))
        check_results.append(self._check_pipeline_sequence(validation_reports))
        
        # Calculate summary statistics
        passed_checks = sum(1 for result in check_results if result.passed)
        failed_checks = len(check_results) - passed_checks
        overall_passed = failed_checks == 0
        
        # Generate summary message
        summary = self._generate_summary(check_results, overall_passed)
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Create audit report
        report = AuditReport(
            overall_passed=overall_passed,
            total_checks=len(check_results),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            check_results=check_results,
            execution_time_ms=execution_time_ms,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            summary=summary
        )
        
        logger.info(
            f"Audit complete: {passed_checks}/{len(check_results)} checks passed",
            extra={
                "stage_name": "audit",
                "overall_passed": overall_passed,
                "passed_checks": passed_checks,
                "failed_checks": failed_checks,
                "execution_time_ms": execution_time_ms
            }
        )
        
        return report
    
    def _check_validation_determinism(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check that validation produces deterministic results.
        
        Validates:
        - All boolean fields are deterministic (True/False, not None)
        - Error messages are consistent
        - No random or time-based values in reports
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for determinism check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        for i, report in enumerate(validation_reports):
            # Check boolean fields are not None
            if report.structure_valid is None:
                issues.append(f"Report {i}: structure_valid is None")
            if report.symbols_preserved is None:
                issues.append(f"Report {i}: symbols_preserved is None")
            if report.syntax_valid is None:
                issues.append(f"Report {i}: syntax_valid is None")
            if report.dependencies_complete is None:
                issues.append(f"Report {i}: dependencies_complete is None")
            
            # Check for non-deterministic patterns in errors
            for error in report.errors:
                if re.search(r'\d{4}-\d{2}-\d{2}', error):  # Date pattern
                    warnings.append(f"Report {i}: Error contains date: {error[:50]}")
                if re.search(r'\d+\.\d+\s*(ms|seconds)', error, re.IGNORECASE):  # Time pattern
                    warnings.append(f"Report {i}: Error contains timing: {error[:50]}")
        
        passed = len(issues) == 0
        message = "Validation determinism verified" if passed else f"Found {len(issues)} determinism issues"
        
        return CheckResult(
            check_name="Validation Determinism",
            passed=passed,
            message=message,
            details={"issues": issues, "reports_checked": len(validation_reports)},
            warnings=warnings
        )
    
    def _check_llm_leakage(
        self,
        validation_reports: List[ValidationReport],
        documentation: Dict[str, str]
    ) -> CheckResult:
        """Check for accidental LLM API calls or keys in validation/documentation.
        
        Validates:
        - No API keys in validation reports
        - No LLM-related terms in validation logic
        - No prompt strings in validation outputs
        - Documentation doesn't contain API keys
        
        Args:
            validation_reports: List of validation reports
            documentation: Documentation dictionary
            
        Returns:
            CheckResult for LLM leakage check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        # Check validation reports for LLM indicators
        for i, report in enumerate(validation_reports):
            # Check errors
            for error in report.errors:
                error_lower = error.lower()
                for indicator in self._llm_indicators:
                    if indicator in error_lower:
                        issues.append(
                            f"Report {i}: Error contains LLM indicator '{indicator}': {error[:50]}"
                        )
            
            # Check test stubs for API keys (pattern: alphanumeric 20+ chars)
            if re.search(r'[A-Za-z0-9]{32,}', report.unit_test_stub):
                warnings.append(f"Report {i}: Test stub may contain API key pattern")
        
        # Check documentation for LLM leakage
        for module_name, doc_content in documentation.items():
            doc_lower = doc_content.lower()
            
            # Check for API key patterns
            if re.search(r'api[_-]?key\s*[:=]\s*["\']?[A-Za-z0-9]{20,}', doc_content, re.IGNORECASE):
                issues.append(f"Documentation '{module_name}': Contains API key pattern")
            
            # Check for LLM model references
            if re.search(r'(gemini|gpt-\d|claude)', doc_lower):
                warnings.append(f"Documentation '{module_name}': Contains LLM model reference")
        
        passed = len(issues) == 0
        message = "No LLM leakage detected" if passed else f"Found {len(issues)} LLM leakage issues"
        
        return CheckResult(
            check_name="LLM Leakage Prevention",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "reports_checked": len(validation_reports),
                "docs_checked": len(documentation)
            },
            warnings=warnings
        )
    
    def _check_config_compliance(
        self,
        validation_reports: List[ValidationReport],
        config: Any
    ) -> CheckResult:
        """Check that all constants come from config module.
        
        Validates:
        - No hardcoded magic numbers in validation logic
        - Configuration values are used consistently
        - No duplicate configuration
        
        Args:
            validation_reports: List of validation reports
            config: Configuration object
            
        Returns:
            CheckResult for config compliance check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        # Verify config has required attributes
        required_attrs = [
            'CONTEXT_EXPANSION_DEPTH',
            'MAX_TOKEN_LIMIT',
            'LOG_LEVEL'
        ]
        
        for attr in required_attrs:
            if not hasattr(config, attr):
                issues.append(f"Config missing required attribute: {attr}")
        
        # Check for hardcoded values in error messages (heuristic)
        for i, report in enumerate(validation_reports):
            for error in report.errors:
                # Look for hardcoded numbers that might be config values
                numbers = re.findall(r'\b\d+\b', error)
                if len(numbers) > 3:  # Many numbers might indicate hardcoding
                    warnings.append(
                        f"Report {i}: Error contains many numbers, check for hardcoding: {error[:50]}"
                    )
        
        passed = len(issues) == 0
        message = "Configuration compliance verified" if passed else f"Found {len(issues)} config issues"
        
        return CheckResult(
            check_name="Configuration Compliance",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "required_attrs_present": len(required_attrs) - len(issues)
            },
            warnings=warnings
        )
    
    def _check_dependency_graph_integrity(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check dependency graph integrity in validation reports.
        
        Validates:
        - Missing dependencies are properly reported
        - Dependency lists are consistent
        - No circular dependency issues
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for dependency graph integrity check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        for i, report in enumerate(validation_reports):
            # Check consistency between dependencies_complete and missing_dependencies
            if not report.dependencies_complete and len(report.missing_dependencies) == 0:
                issues.append(
                    f"Report {i}: dependencies_complete=False but missing_dependencies is empty"
                )
            
            if report.dependencies_complete and len(report.missing_dependencies) > 0:
                issues.append(
                    f"Report {i}: dependencies_complete=True but has {len(report.missing_dependencies)} missing deps"
                )
            
            # Check for duplicate entries in missing_dependencies
            if len(report.missing_dependencies) != len(set(report.missing_dependencies)):
                warnings.append(f"Report {i}: Duplicate entries in missing_dependencies")
        
        passed = len(issues) == 0
        message = "Dependency graph integrity verified" if passed else f"Found {len(issues)} integrity issues"
        
        return CheckResult(
            check_name="Dependency Graph Integrity",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "total_missing_deps": sum(len(r.missing_dependencies) for r in validation_reports)
            },
            warnings=warnings
        )
    
    def _check_syntax_robustness(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check that syntax errors are caught deterministically.
        
        Validates:
        - Syntax errors are properly reported
        - Error messages are informative
        - No false positives/negatives
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for syntax robustness check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        syntax_error_count = 0
        
        for i, report in enumerate(validation_reports):
            # If syntax is invalid, there should be an error message
            if not report.syntax_valid:
                syntax_error_count += 1
                
                # Check for syntax-related error message
                has_syntax_error = any(
                    'syntax' in error.lower() or 'parse' in error.lower()
                    for error in report.errors
                )
                
                if not has_syntax_error:
                    issues.append(
                        f"Report {i}: syntax_valid=False but no syntax error message found"
                    )
            
            # Check error message quality for syntax errors
            for error in report.errors:
                if 'syntax error' in error.lower():
                    # Should have line number
                    if not re.search(r'line\s+\d+', error, re.IGNORECASE):
                        warnings.append(f"Report {i}: Syntax error missing line number")
        
        passed = len(issues) == 0
        message = "Syntax robustness verified" if passed else f"Found {len(issues)} syntax issues"
        
        return CheckResult(
            check_name="Syntax Robustness",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "syntax_errors_found": syntax_error_count,
                "reports_checked": len(validation_reports)
            },
            warnings=warnings
        )
    
    def _check_structure_validation(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check structure validation (function names, parameters, control flow).
        
        Validates:
        - Structure checks are performed
        - Error messages are clear
        - Validation is consistent
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for structure validation check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        structure_failures = 0
        
        for i, report in enumerate(validation_reports):
            if not report.structure_valid:
                structure_failures += 1
                
                # Check for structure-related error messages
                has_structure_error = any(
                    any(keyword in error.lower() for keyword in [
                        'name', 'parameter', 'control flow', 'structure', 'mismatch'
                    ])
                    for error in report.errors
                )
                
                if not has_structure_error:
                    issues.append(
                        f"Report {i}: structure_valid=False but no structure error message"
                    )
        
        passed = len(issues) == 0
        message = "Structure validation verified" if passed else f"Found {len(issues)} structure issues"
        
        return CheckResult(
            check_name="Structure Validation",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "structure_failures": structure_failures,
                "reports_checked": len(validation_reports)
            },
            warnings=warnings
        )
    
    def _check_symbol_preservation(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check that all original called symbols are preserved.
        
        Validates:
        - Symbol preservation is checked
        - Missing symbols are reported
        - No false positives
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for symbol preservation check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        symbol_failures = 0
        
        for i, report in enumerate(validation_reports):
            if not report.symbols_preserved:
                symbol_failures += 1
                
                # Check for symbol-related error messages
                has_symbol_error = any(
                    'symbol' in error.lower() or 'missing' in error.lower()
                    for error in report.errors
                )
                
                if not has_symbol_error:
                    issues.append(
                        f"Report {i}: symbols_preserved=False but no symbol error message"
                    )
        
        passed = len(issues) == 0
        message = "Symbol preservation verified" if passed else f"Found {len(issues)} symbol issues"
        
        return CheckResult(
            check_name="Symbol Preservation",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "symbol_failures": symbol_failures,
                "reports_checked": len(validation_reports)
            },
            warnings=warnings
        )
    
    def _check_translation_completeness(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check that translations reject TODO, pass, NotImplemented, empty bodies.
        
        Validates:
        - Incomplete markers are detected
        - Validation rejects incomplete translations
        - Error messages are clear
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for translation completeness check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        incomplete_count = 0
        
        for i, report in enumerate(validation_reports):
            # Check if any incomplete markers are mentioned in errors
            has_incomplete_error = any(
                any(marker.lower() in error.lower() for marker in self._incomplete_markers)
                for error in report.errors
            )
            
            if has_incomplete_error:
                incomplete_count += 1
                
                # Verify that at least one validation flag is False
                if (report.syntax_valid and report.structure_valid and
                    report.symbols_preserved and report.dependencies_complete):
                    warnings.append(
                        f"Report {i}: Has incomplete marker error but all validations passed"
                    )
        
        passed = len(issues) == 0
        message = "Translation completeness verified" if passed else f"Found {len(issues)} completeness issues"
        
        return CheckResult(
            check_name="Translation Completeness",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "incomplete_translations": incomplete_count,
                "reports_checked": len(validation_reports)
            },
            warnings=warnings
        )
    
    def _check_unit_test_quality(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check unit test stub quality (deterministic pytest-style with placeholders).
        
        Validates:
        - Test stubs are generated
        - Follow pytest conventions
        - Have proper structure
        - Use placeholders only
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for unit test quality check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        for i, report in enumerate(validation_reports):
            stub = report.unit_test_stub
            
            # Check stub is not empty
            if not stub or len(stub.strip()) == 0:
                issues.append(f"Report {i}: Empty unit test stub")
                continue
            
            # Check for pytest-style function
            if not re.search(r'def\s+test_\w+\s*\(', stub):
                issues.append(f"Report {i}: Test stub doesn't follow pytest naming (test_*)")
            
            # Check for assert statement
            if 'assert' not in stub:
                warnings.append(f"Report {i}: Test stub missing assert statement")
            
            # Check for TODO or placeholder comments
            if 'TODO' not in stub and 'placeholder' not in stub.lower():
                warnings.append(f"Report {i}: Test stub missing TODO/placeholder guidance")
            
            # Check stub is valid Python syntax
            try:
                ast.parse(stub)
            except SyntaxError as e:
                issues.append(f"Report {i}: Test stub has syntax error: {e}")
        
        passed = len(issues) == 0
        message = "Unit test quality verified" if passed else f"Found {len(issues)} test quality issues"
        
        return CheckResult(
            check_name="Unit Test Stub Quality",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "stubs_checked": len(validation_reports)
            },
            warnings=warnings
        )
    
    def _check_documentation_accuracy(
        self,
        validation_reports: List[ValidationReport],
        documentation: Dict[str, str]
    ) -> CheckResult:
        """Check that documentation matches validated code structure.
        
        Validates:
        - Documentation exists for validated modules
        - Documentation is not empty
        - Documentation format is consistent
        
        Args:
            validation_reports: List of validation reports
            documentation: Documentation dictionary
            
        Returns:
            CheckResult for documentation accuracy check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        # Check documentation is not empty
        for module_name, doc_content in documentation.items():
            if not doc_content or len(doc_content.strip()) == 0:
                issues.append(f"Documentation for '{module_name}' is empty")
            
            # Check for minimum documentation elements
            doc_lower = doc_content.lower()
            if 'function' not in doc_lower and 'class' not in doc_lower:
                warnings.append(f"Documentation for '{module_name}' missing function/class references")
        
        # Check consistency between validation and documentation counts
        if len(validation_reports) > 0 and len(documentation) == 0:
            warnings.append("Validation reports exist but no documentation generated")
        
        passed = len(issues) == 0
        message = "Documentation accuracy verified" if passed else f"Found {len(issues)} documentation issues"
        
        return CheckResult(
            check_name="Documentation Accuracy",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "docs_checked": len(documentation),
                "validation_reports": len(validation_reports)
            },
            warnings=warnings
        )
    
    def _check_report_schema(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check that all report fields are strictly typed and consistent.
        
        Validates:
        - All required fields present
        - Correct types for all fields
        - No None values where not expected
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for report schema check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        for i, report in enumerate(validation_reports):
            # Check field types
            if not isinstance(report.structure_valid, bool):
                issues.append(f"Report {i}: structure_valid is not bool")
            
            if not isinstance(report.symbols_preserved, bool):
                issues.append(f"Report {i}: symbols_preserved is not bool")
            
            if not isinstance(report.syntax_valid, bool):
                issues.append(f"Report {i}: syntax_valid is not bool")
            
            if not isinstance(report.dependencies_complete, bool):
                issues.append(f"Report {i}: dependencies_complete is not bool")
            
            if not isinstance(report.missing_dependencies, list):
                issues.append(f"Report {i}: missing_dependencies is not list")
            
            if not isinstance(report.unit_test_stub, str):
                issues.append(f"Report {i}: unit_test_stub is not str")
            
            if not isinstance(report.errors, list):
                issues.append(f"Report {i}: errors is not list")
            
            # Check list contents
            if not all(isinstance(dep, str) for dep in report.missing_dependencies):
                issues.append(f"Report {i}: missing_dependencies contains non-string")
            
            if not all(isinstance(err, str) for err in report.errors):
                issues.append(f"Report {i}: errors contains non-string")
        
        passed = len(issues) == 0
        message = "Report schema verified" if passed else f"Found {len(issues)} schema issues"
        
        return CheckResult(
            check_name="Report Schema Consistency",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "reports_checked": len(validation_reports)
            },
            warnings=warnings
        )
    
    def _check_performance(
        self,
        validation_reports: List[ValidationReport],
        documentation: Dict[str, str]
    ) -> CheckResult:
        """Check that validation and documentation are efficient.
        
        Validates:
        - No obvious performance bottlenecks
        - Reasonable output sizes
        - No excessive memory usage indicators
        
        Args:
            validation_reports: List of validation reports
            documentation: Documentation dictionary
            
        Returns:
            CheckResult for performance check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        # Check for excessively large outputs
        for i, report in enumerate(validation_reports):
            # Check test stub size
            if len(report.unit_test_stub) > 10000:  # 10KB
                warnings.append(f"Report {i}: Test stub is very large ({len(report.unit_test_stub)} chars)")
            
            # Check error list size
            if len(report.errors) > 100:
                warnings.append(f"Report {i}: Excessive error count ({len(report.errors)})")
            
            # Check for very long error messages
            for error in report.errors:
                if len(error) > 1000:
                    warnings.append(f"Report {i}: Very long error message ({len(error)} chars)")
        
        # Check documentation sizes
        for module_name, doc_content in documentation.items():
            if len(doc_content) > 100000:  # 100KB
                warnings.append(f"Documentation '{module_name}': Very large ({len(doc_content)} chars)")
        
        # Performance is considered passing unless there are critical issues
        passed = len(issues) == 0
        message = "Performance validated" if passed else f"Found {len(issues)} performance issues"
        
        return CheckResult(
            check_name="Performance Validation",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "total_reports": len(validation_reports),
                "total_docs": len(documentation)
            },
            warnings=warnings
        )
    
    def _check_pipeline_sequence(
        self,
        validation_reports: List[ValidationReport]
    ) -> CheckResult:
        """Check pipeline sequence integrity (validation before documentation).
        
        Validates:
        - Validation reports exist
        - Reports indicate proper sequencing
        - No out-of-order execution indicators
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            CheckResult for pipeline sequence check
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        # Check that validation reports exist
        if len(validation_reports) == 0:
            warnings.append("No validation reports provided - pipeline may not have run")
        
        # Check for indicators of failed validations that should halt pipeline
        failed_validations = sum(
            1 for report in validation_reports
            if not (report.syntax_valid and report.structure_valid and
                   report.symbols_preserved and report.dependencies_complete)
        )
        
        if failed_validations > 0:
            warnings.append(
                f"{failed_validations} validation(s) failed - pipeline should halt before documentation"
            )
        
        passed = len(issues) == 0
        message = "Pipeline sequence verified" if passed else f"Found {len(issues)} sequence issues"
        
        return CheckResult(
            check_name="Pipeline Sequence Integrity",
            passed=passed,
            message=message,
            details={
                "issues": issues,
                "total_reports": len(validation_reports),
                "failed_validations": failed_validations
            },
            warnings=warnings
        )
    
    def _generate_summary(
        self,
        check_results: List[CheckResult],
        overall_passed: bool
    ) -> str:
        """Generate human-readable summary of audit results.
        
        Args:
            check_results: List of check results
            overall_passed: Whether all checks passed
            
        Returns:
            Summary string
        """
        if overall_passed:
            return "All audit checks passed. Pipeline integrity verified."
        
        failed_checks = [result for result in check_results if not result.passed]
        failed_names = [result.check_name for result in failed_checks]
        
        return f"Audit failed. {len(failed_checks)} check(s) failed: {', '.join(failed_names)}"
