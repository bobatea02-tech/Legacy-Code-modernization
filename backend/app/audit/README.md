# Audit Engine

Deterministic audit engine for end-to-end pipeline integrity verification in the Legacy Code Modernization Engine.

## Overview

The AuditEngine provides comprehensive validation of the entire pipeline without using LLMs. It performs 13 distinct checks to ensure validation determinism, prevent LLM leakage, verify configuration compliance, and validate overall pipeline integrity.

## Key Features

- **No LLM Usage**: Pure deterministic auditing using pattern matching and schema validation
- **13 Comprehensive Checks**: Covers all aspects of pipeline integrity
- **Detailed Reporting**: Structured reports with pass/fail status, issues, and warnings
- **Performance Tracking**: Measures audit execution time
- **Type-Safe**: Fully typed with dataclasses for all reports
- **Zero Side Effects**: Read-only auditing, no code modification

## Architecture

### Core Classes

#### `AuditReport`
Main audit report dataclass:
- `overall_passed`: Boolean indicating if all checks passed
- `total_checks`: Total number of checks performed
- `passed_checks`: Number of checks that passed
- `failed_checks`: Number of checks that failed
- `check_results`: List of individual CheckResult objects
- `execution_time_ms`: Audit execution time in milliseconds
- `timestamp`: ISO timestamp of audit execution
- `summary`: Human-readable summary message

#### `CheckResult`
Individual check result dataclass:
- `check_name`: Name of the check
- `passed`: Boolean pass/fail status
- `message`: Summary message
- `details`: Dictionary with check-specific details
- `warnings`: List of non-critical warnings

#### `AuditEngine`
Main audit engine class:
- Reads configuration from `get_settings()`
- No global state
- Type-hinted methods
- Modular private methods for each check

## The 13 Audit Checks

### 1. Validation Determinism
**Purpose**: Ensure validation produces identical results for identical inputs

**Validates**:
- All boolean fields are True/False (not None)
- No random or time-based values in reports
- Error messages are consistent

**Fails if**: Any boolean field is None or non-deterministic patterns detected

### 2. LLM Leakage Prevention
**Purpose**: Detect accidental LLM API calls or keys in validation/documentation

**Validates**:
- No API keys in validation reports or documentation
- No LLM-related terms (gemini, openai, gpt, claude, etc.)
- No prompt strings in validation outputs

**Fails if**: API key patterns or LLM indicators found

### 3. Configuration Compliance
**Purpose**: Ensure all constants come from config module

**Validates**:
- Required config attributes present (CONTEXT_EXPANSION_DEPTH, MAX_TOKEN_LIMIT, LOG_LEVEL)
- No hardcoded magic numbers
- Configuration values used consistently

**Fails if**: Required config attributes missing

### 4. Dependency Graph Integrity
**Purpose**: Validate cross-file symbol reports accurately

**Validates**:
- Consistency between `dependencies_complete` and `missing_dependencies`
- No duplicate entries in missing dependencies
- Proper dependency reporting

**Fails if**: Inconsistent dependency reporting (e.g., incomplete=False but has missing deps)

### 5. Syntax Robustness
**Purpose**: Ensure all syntax errors caught deterministically

**Validates**:
- Syntax errors properly reported
- Error messages are informative with line numbers
- No false positives/negatives

**Fails if**: `syntax_valid=False` but no syntax error message

### 6. Structure Validation
**Purpose**: Validate function names, parameters, control flow

**Validates**:
- Structure checks performed
- Error messages clear and specific
- Validation consistent

**Fails if**: `structure_valid=False` but no structure error message

### 7. Symbol Preservation
**Purpose**: Ensure all original called symbols present

**Validates**:
- Symbol preservation checked
- Missing symbols reported
- No false positives

**Fails if**: `symbols_preserved=False` but no symbol error message

### 8. Translation Completeness
**Purpose**: Reject translations with TODO, pass, NotImplemented, empty bodies

**Validates**:
- Incomplete markers detected (TODO, FIXME, pass, NotImplemented)
- Validation rejects incomplete translations
- Error messages clear

**Fails if**: Critical issues detected (currently informational)

### 9. Unit Test Stub Quality
**Purpose**: Ensure deterministic pytest-style stubs with placeholders

**Validates**:
- Test stubs generated and non-empty
- Follow pytest conventions (test_* naming)
- Have proper structure (assert statements)
- Use placeholders only (TODO comments)
- Valid Python syntax

**Fails if**: Empty stub, bad naming, or syntax errors

### 10. Documentation Accuracy
**Purpose**: Ensure documentation matches validated code structure

**Validates**:
- Documentation exists and non-empty
- Contains function/class references
- Format is consistent

**Fails if**: Empty documentation

### 11. Report Schema Consistency
**Purpose**: Ensure all fields strictly typed and consistent

**Validates**:
- All required fields present
- Correct types (bool, list, str)
- No None values where not expected
- List contents are correct types

**Fails if**: Type mismatches detected

### 12. Performance Validation
**Purpose**: Ensure validation and documentation efficient

**Validates**:
- No excessively large outputs
- Reasonable error counts
- No excessive memory usage indicators

**Fails if**: Critical performance issues (currently warnings only)

### 13. Pipeline Sequence Integrity
**Purpose**: Validate fixed order, failure in validation halts pipeline

**Validates**:
- Validation reports exist
- Reports indicate proper sequencing
- Failed validations noted

**Fails if**: Critical sequence violations (currently warnings only)

## Usage

### Basic Audit

```python
from app.validation import ValidationReport
from app.audit import AuditEngine, AuditReport

# Create validation reports
validation_reports = [
    ValidationReport(
        structure_valid=True,
        symbols_preserved=True,
        syntax_valid=True,
        dependencies_complete=True,
        missing_dependencies=[],
        unit_test_stub="def test_example(): assert True",
        errors=[]
    )
]

# Create documentation
documentation = {
    "module1": "Documentation with function references"
}

# Run audit
audit_engine = AuditEngine()
audit_report: AuditReport = audit_engine.run_audit(
    validation_reports=validation_reports,
    documentation=documentation
)

# Check results
if audit_report.overall_passed:
    print("✓ Pipeline integrity verified")
else:
    print(f"✗ Audit failed: {audit_report.summary}")
    for check in audit_report.check_results:
        if not check.passed:
            print(f"  - {check.check_name}: {check.message}")
```

### Detailed Analysis

```python
# Run audit
audit_report = audit_engine.run_audit(validation_reports, documentation)

# Overall statistics
print(f"Score: {audit_report.passed_checks}/{audit_report.total_checks}")
print(f"Success Rate: {(audit_report.passed_checks/audit_report.total_checks)*100:.1f}%")
print(f"Execution Time: {audit_report.execution_time_ms:.2f}ms")

# Check individual results
for check in audit_report.check_results:
    status = "✓" if check.passed else "✗"
    print(f"{status} {check.check_name}: {check.message}")
    
    # Show warnings
    if check.warnings:
        for warning in check.warnings:
            print(f"  ⚠ {warning}")
    
    # Show issues
    if check.details.get("issues"):
        for issue in check.details["issues"]:
            print(f"  ✗ {issue}")
```

### Integration with Pipeline

```python
from app.core.pipeline import Pipeline
from app.audit import AuditEngine

# After validation and documentation phases
validation_reports = pipeline.get_validation_reports()
documentation = pipeline.get_documentation()

# Run audit before deployment
audit_engine = AuditEngine()
audit_report = audit_engine.run_audit(validation_reports, documentation)

if not audit_report.overall_passed:
    # Halt pipeline
    raise RuntimeError(f"Pipeline audit failed: {audit_report.summary}")

# Continue to deployment
pipeline.deploy()
```

## Configuration

The AuditEngine reads from `app.core.config`:

```python
CONTEXT_EXPANSION_DEPTH: int = 3  # Required for validation
MAX_TOKEN_LIMIT: int = 100000     # Required for validation
LOG_LEVEL: str = "INFO"           # Required for logging
```

## Testing

Run audit tests:
```bash
pytest tests/test_audit.py -v
```

Run examples:
```bash
python examples/audit_usage.py
```

## Integration Points

### Input
- `List[ValidationReport]`: From ValidationEngine
- `Dict[str, str]`: Documentation mapping module names to content
- `Optional[Config]`: Configuration object (uses get_settings() if None)

### Output
- `AuditReport`: Comprehensive audit results
- Used before production deployment
- Determines if pipeline can proceed

## Design Constraints

### What AuditEngine Does NOT Do
- ❌ Call LLM APIs
- ❌ Modify code or reports
- ❌ Access filesystem
- ❌ Execute code
- ❌ Use prompt strings
- ❌ Generate new content

### What AuditEngine DOES
- ✅ Read validation reports
- ✅ Analyze documentation
- ✅ Pattern matching for issues
- ✅ Schema validation
- ✅ Type checking
- ✅ Generate audit reports
- ✅ Log audit progress

## Error Handling

All audit checks are defensive:
- Catch exceptions and log warnings
- Continue auditing even if one check fails
- Accumulate all issues in report
- Never raise exceptions to caller
- Always return complete AuditReport

## Performance

- O(n) for most checks (n = number of reports)
- O(n*m) for pattern matching (m = average content size)
- Minimal memory footprint
- Typical execution: < 5ms for 10 reports
- No caching or state between runs

## Security Considerations

The AuditEngine specifically checks for:
- **API Key Leakage**: Pattern matching for API keys in outputs
- **LLM References**: Detection of LLM-related terms
- **Configuration Exposure**: Verification of config usage
- **Incomplete Translations**: Detection of TODO/placeholder markers

## Best Practices

1. **Run After Validation**: Always run audit after validation phase completes
2. **Before Deployment**: Use as final gate before production deployment
3. **Log Results**: Always log audit results for traceability
4. **Fail Fast**: Halt pipeline if audit fails
5. **Review Warnings**: Even passing audits may have warnings to address
6. **Regular Updates**: Update LLM indicators list as new services emerge

## Troubleshooting

### Common Issues

**Issue**: Audit fails with "LLM Leakage Prevention"
- **Cause**: API keys or LLM terms in outputs
- **Solution**: Review validation and documentation generation code

**Issue**: Audit fails with "Dependency Graph Integrity"
- **Cause**: Inconsistent dependency reporting
- **Solution**: Fix ValidationEngine dependency checking logic

**Issue**: Audit fails with "Unit Test Stub Quality"
- **Cause**: Empty or malformed test stubs
- **Solution**: Review test stub generation in ValidationEngine

**Issue**: Audit fails with "Report Schema Consistency"
- **Cause**: Type mismatches in ValidationReport
- **Solution**: Ensure ValidationReport fields have correct types

## Future Enhancements

Potential improvements (not in current scope):
- Configurable check thresholds
- Custom check plugins
- Historical audit tracking
- Trend analysis
- Integration with CI/CD pipelines
- Automated remediation suggestions
- Performance benchmarking
- Security vulnerability scanning
