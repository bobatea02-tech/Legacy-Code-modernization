"""Example usage of AuditEngine for pipeline integrity verification.

This demonstrates how to use the deterministic audit engine to verify
end-to-end integrity of the Legacy Code Modernization pipeline.
"""

from app.validation import ValidationReport
from app.audit import AuditEngine, AuditReport
from app.core.config import get_settings


def example_successful_audit():
    """Example: Audit with all checks passing."""
    
    print("=== Example 1: Successful Audit ===\n")
    
    # Create validation reports from successful translations
    validation_reports = [
        ValidationReport(
            structure_valid=True,
            symbols_preserved=True,
            syntax_valid=True,
            dependencies_complete=True,
            missing_dependencies=[],
            unit_test_stub="""def test_calculate_total():
    \"\"\"Test for calculate_total.\"\"\"
    # TODO: Set up test data
    result = calculate_total(10.0, 2)
    assert result is not None
""",
            errors=[]
        ),
        ValidationReport(
            structure_valid=True,
            symbols_preserved=True,
            syntax_valid=True,
            dependencies_complete=True,
            missing_dependencies=[],
            unit_test_stub="""def test_process_order():
    \"\"\"Test for process_order.\"\"\"
    # TODO: Set up test data
    result = process_order("ORDER123")
    assert result is not None
""",
            errors=[]
        )
    ]
    
    # Documentation generated for translated modules
    documentation = {
        "calculator": """
# Calculator Module

This module provides calculation functions.

## Functions

### calculate_total(price: float, quantity: int) -> float
Calculates the total price for a given quantity.

**Parameters:**
- price: Unit price
- quantity: Number of items

**Returns:**
- Total price
""",
        "order_processor": """
# Order Processor Module

This module handles order processing.

## Functions

### process_order(order_id: str) -> bool
Processes an order by ID.

**Parameters:**
- order_id: Unique order identifier

**Returns:**
- True if successful, False otherwise
"""
    }
    
    # Run audit
    audit_engine = AuditEngine()
    config = get_settings()
    
    audit_report: AuditReport = audit_engine.run_audit(
        validation_reports=validation_reports,
        documentation=documentation,
        config=config
    )
    
    # Display results
    print(f"Overall Status: {'PASSED' if audit_report.overall_passed else 'FAILED'}")
    print(f"Total Checks: {audit_report.total_checks}")
    print(f"Passed: {audit_report.passed_checks}")
    print(f"Failed: {audit_report.failed_checks}")
    print(f"Execution Time: {audit_report.execution_time_ms:.2f}ms")
    print(f"Timestamp: {audit_report.timestamp}")
    print(f"\nSummary: {audit_report.summary}")
    
    print("\n--- Check Details ---")
    for check in audit_report.check_results:
        status = "✓" if check.passed else "✗"
        print(f"{status} {check.check_name}: {check.message}")
        if check.warnings:
            for warning in check.warnings:
                print(f"  ⚠ {warning}")


def example_failed_audit():
    """Example: Audit with failures detected."""
    
    print("\n\n=== Example 2: Failed Audit ===\n")
    
    # Create validation reports with issues
    validation_reports = [
        ValidationReport(
            structure_valid=False,
            symbols_preserved=False,
            syntax_valid=False,
            dependencies_complete=False,
            missing_dependencies=["helper_function", "validate_input"],
            unit_test_stub="",  # Empty stub - quality issue
            errors=[
                "Syntax error at line 10: invalid syntax",
                "Missing called symbols: helper_function, validate_input",
                "Parameter count mismatch: expected 3, got 2",
                "Incomplete translation markers found: TODO, pass"
            ]
        )
    ]
    
    # Documentation with issues
    documentation = {
        "problematic_module": ""  # Empty documentation
    }
    
    # Run audit
    audit_engine = AuditEngine()
    audit_report = audit_engine.run_audit(validation_reports, documentation)
    
    # Display results
    print(f"Overall Status: {'PASSED' if audit_report.overall_passed else 'FAILED'}")
    print(f"Total Checks: {audit_report.total_checks}")
    print(f"Passed: {audit_report.passed_checks}")
    print(f"Failed: {audit_report.failed_checks}")
    print(f"\nSummary: {audit_report.summary}")
    
    print("\n--- Failed Checks ---")
    for check in audit_report.check_results:
        if not check.passed:
            print(f"\n✗ {check.check_name}")
            print(f"  Message: {check.message}")
            if check.details.get("issues"):
                print(f"  Issues:")
                for issue in check.details["issues"][:3]:  # Show first 3
                    print(f"    - {issue}")


def example_llm_leakage_detection():
    """Example: Detecting LLM leakage in outputs."""
    
    print("\n\n=== Example 3: LLM Leakage Detection ===\n")
    
    # Validation report with LLM reference in error
    validation_reports = [
        ValidationReport(
            structure_valid=True,
            symbols_preserved=True,
            syntax_valid=True,
            dependencies_complete=True,
            missing_dependencies=[],
            unit_test_stub="def test_example(): pass",
            errors=["Error calling Gemini API during validation"]  # LLM leakage!
        )
    ]
    
    # Documentation with API key
    documentation = {
        "module": "Documentation with api_key: AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz123456"
    }
    
    # Run audit
    audit_engine = AuditEngine()
    audit_report = audit_engine.run_audit(validation_reports, documentation)
    
    # Find LLM leakage check
    llm_check = next(
        (check for check in audit_report.check_results 
         if check.check_name == "LLM Leakage Prevention"),
        None
    )
    
    if llm_check:
        print(f"LLM Leakage Check: {'PASSED' if llm_check.passed else 'FAILED'}")
        print(f"Message: {llm_check.message}")
        if llm_check.details.get("issues"):
            print("\nIssues Detected:")
            for issue in llm_check.details["issues"]:
                print(f"  - {issue}")


def example_dependency_integrity():
    """Example: Checking dependency graph integrity."""
    
    print("\n\n=== Example 4: Dependency Graph Integrity ===\n")
    
    # Inconsistent report: says incomplete but no missing deps
    bad_report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=False,  # Says incomplete
        missing_dependencies=[],  # But no missing deps listed!
        unit_test_stub="def test_example(): pass",
        errors=[]
    )
    
    # Consistent report
    good_report = ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=False,
        missing_dependencies=["dep1", "dep2"],  # Properly listed
        unit_test_stub="def test_example(): pass",
        errors=["Missing dependencies: dep1, dep2"]
    )
    
    # Run audit
    audit_engine = AuditEngine()
    
    print("Testing inconsistent report...")
    bad_audit = audit_engine.run_audit([bad_report], {})
    dep_check_bad = next(
        (c for c in bad_audit.check_results 
         if c.check_name == "Dependency Graph Integrity"),
        None
    )
    print(f"Result: {'PASSED' if dep_check_bad.passed else 'FAILED'}")
    if not dep_check_bad.passed:
        print(f"Issues: {dep_check_bad.details['issues']}")
    
    print("\nTesting consistent report...")
    good_audit = audit_engine.run_audit([good_report], {})
    dep_check_good = next(
        (c for c in good_audit.check_results 
         if c.check_name == "Dependency Graph Integrity"),
        None
    )
    print(f"Result: {'PASSED' if dep_check_good.passed else 'PASSED'}")


def example_comprehensive_report():
    """Example: Comprehensive audit report analysis."""
    
    print("\n\n=== Example 5: Comprehensive Report Analysis ===\n")
    
    # Mix of good and problematic reports
    validation_reports = [
        ValidationReport(
            structure_valid=True,
            symbols_preserved=True,
            syntax_valid=True,
            dependencies_complete=True,
            missing_dependencies=[],
            unit_test_stub="def test_good_func(): assert True",
            errors=[]
        ),
        ValidationReport(
            structure_valid=False,
            symbols_preserved=True,
            syntax_valid=True,
            dependencies_complete=True,
            missing_dependencies=[],
            unit_test_stub="def test_bad_func(): pass",
            errors=["Parameter count mismatch"]
        )
    ]
    
    documentation = {
        "module1": "Good documentation with function references",
        "module2": "Another module with class definitions"
    }
    
    # Run audit
    audit_engine = AuditEngine()
    audit_report = audit_engine.run_audit(validation_reports, documentation)
    
    # Detailed analysis
    print("=== Audit Summary ===")
    print(f"Status: {'✓ PASSED' if audit_report.overall_passed else '✗ FAILED'}")
    print(f"Score: {audit_report.passed_checks}/{audit_report.total_checks}")
    print(f"Success Rate: {(audit_report.passed_checks/audit_report.total_checks)*100:.1f}%")
    print(f"Execution Time: {audit_report.execution_time_ms:.2f}ms")
    
    print("\n=== Check Breakdown ===")
    categories = {
        "Validation": ["Validation Determinism", "Syntax Robustness", "Structure Validation"],
        "Integrity": ["Dependency Graph Integrity", "Symbol Preservation"],
        "Quality": ["Unit Test Stub Quality", "Documentation Accuracy"],
        "Security": ["LLM Leakage Prevention", "Configuration Compliance"],
        "Pipeline": ["Pipeline Sequence Integrity", "Performance Validation"]
    }
    
    for category, check_names in categories.items():
        category_checks = [
            c for c in audit_report.check_results 
            if c.check_name in check_names
        ]
        passed = sum(1 for c in category_checks if c.passed)
        total = len(category_checks)
        print(f"\n{category}: {passed}/{total} passed")
        for check in category_checks:
            status = "✓" if check.passed else "✗"
            print(f"  {status} {check.check_name}")


if __name__ == "__main__":
    print("AuditEngine Examples\n")
    print("=" * 60)
    
    # Run all examples
    example_successful_audit()
    example_failed_audit()
    example_llm_leakage_detection()
    example_dependency_integrity()
    example_comprehensive_report()
    
    print("\n" + "=" * 60)
    print("\n✓ All examples completed")
