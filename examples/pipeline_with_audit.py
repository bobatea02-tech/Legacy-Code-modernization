"""Example: Complete pipeline integration with audit.

This demonstrates how the AuditEngine integrates into the full
Legacy Code Modernization pipeline as the final integrity check
before deployment.
"""

from typing import List, Dict
from app.parsers.base import ASTNode
from app.validation import ValidationEngine, ValidationReport
from app.audit import AuditEngine, AuditReport


class MockPipeline:
    """Mock pipeline for demonstration purposes."""
    
    def __init__(self):
        self.validation_engine = ValidationEngine()
        self.audit_engine = AuditEngine()
        self.validation_reports: List[ValidationReport] = []
        self.documentation: Dict[str, str] = {}
    
    def parse_legacy_code(self) -> List[ASTNode]:
        """Phase 1-2: Parse legacy code into AST nodes."""
        print("Phase 1-2: Parsing legacy code...")
        
        # Mock AST nodes from legacy code
        nodes = [
            ASTNode(
                id="calc_001",
                name="calculate_total",
                node_type="function",
                parameters=["price", "quantity", "tax_rate"],
                return_type="float",
                called_symbols=["multiply", "round"],
                imports=["math"],
                file_path="calculator.java",
                start_line=10,
                end_line=20,
                raw_source="public float calculateTotal(...) { ... }"
            ),
            ASTNode(
                id="proc_001",
                name="process_order",
                node_type="function",
                parameters=["order_id"],
                return_type="bool",
                called_symbols=["validate_order", "save_order"],
                imports=[],
                file_path="processor.java",
                start_line=30,
                end_line=45,
                raw_source="public boolean processOrder(...) { ... }"
            )
        ]
        
        print(f"  ✓ Parsed {len(nodes)} AST nodes")
        return nodes
    
    def translate_code(self, nodes: List[ASTNode]) -> Dict[str, str]:
        """Phase 3-8: Translate legacy code to Python."""
        print("\nPhase 3-8: Translating code to Python...")
        
        # Mock translated code
        translations = {
            "calculate_total": """
def calculate_total(price: float, quantity: int, tax_rate: float) -> float:
    \"\"\"Calculate total price with tax.\"\"\"
    subtotal = multiply(price, quantity)
    tax = subtotal * tax_rate
    return round(subtotal + tax, 2)
""",
            "process_order": """
def process_order(order_id: str) -> bool:
    \"\"\"Process an order by ID.\"\"\"
    if validate_order(order_id):
        return save_order(order_id)
    return False
"""
        }
        
        print(f"  ✓ Translated {len(translations)} functions")
        return translations
    
    def validate_translations(
        self,
        nodes: List[ASTNode],
        translations: Dict[str, str]
    ) -> List[ValidationReport]:
        """Phase 10: Validate translated code."""
        print("\nPhase 10: Validating translations...")
        
        reports = []
        for node in nodes:
            translated_code = translations.get(node.name, "")
            
            report = self.validation_engine.validate_translation(
                original_node=node,
                translated_code=translated_code,
                dependency_graph=None
            )
            
            reports.append(report)
            
            status = "✓" if all([
                report.syntax_valid,
                report.structure_valid,
                report.symbols_preserved,
                report.dependencies_complete
            ]) else "✗"
            
            print(f"  {status} {node.name}: ", end="")
            if status == "✓":
                print("PASSED")
            else:
                print(f"FAILED ({len(report.errors)} errors)")
        
        self.validation_reports = reports
        return reports
    
    def generate_documentation(
        self,
        nodes: List[ASTNode],
        translations: Dict[str, str]
    ) -> Dict[str, str]:
        """Phase 11: Generate documentation."""
        print("\nPhase 11: Generating documentation...")
        
        # Mock documentation generation
        docs = {}
        for node in nodes:
            docs[node.name] = f"""
# {node.name}

## Description
Translated from {node.file_path}

## Function Signature
```python
{translations.get(node.name, '').strip()}
```

## Parameters
{', '.join(node.parameters)}

## Returns
{node.return_type or 'None'}

## Dependencies
{', '.join(node.called_symbols) if node.called_symbols else 'None'}
"""
        
        print(f"  ✓ Generated documentation for {len(docs)} modules")
        self.documentation = docs
        return docs
    
    def run_audit(self) -> AuditReport:
        """Phase 12: Run comprehensive audit."""
        print("\nPhase 12: Running comprehensive audit...")
        print("=" * 60)
        
        audit_report = self.audit_engine.run_audit(
            validation_reports=self.validation_reports,
            documentation=self.documentation
        )
        
        # Display audit results
        print(f"\nAudit Status: {'✓ PASSED' if audit_report.overall_passed else '✗ FAILED'}")
        print(f"Checks: {audit_report.passed_checks}/{audit_report.total_checks} passed")
        print(f"Execution Time: {audit_report.execution_time_ms:.2f}ms")
        print(f"Timestamp: {audit_report.timestamp}")
        
        print("\n--- Check Results ---")
        for check in audit_report.check_results:
            status = "✓" if check.passed else "✗"
            print(f"{status} {check.check_name}")
            
            if not check.passed:
                print(f"  Message: {check.message}")
                if check.details.get("issues"):
                    for issue in check.details["issues"][:2]:
                        print(f"    - {issue}")
            
            if check.warnings:
                for warning in check.warnings[:2]:
                    print(f"  ⚠ {warning}")
        
        print("\n" + "=" * 60)
        print(f"Summary: {audit_report.summary}")
        
        return audit_report
    
    def deploy(self):
        """Phase 13: Deploy to production."""
        print("\nPhase 13: Deploying to production...")
        print("  ✓ Code deployed successfully")
        print("  ✓ Documentation published")
        print("  ✓ Tests registered")
    
    def run_complete_pipeline(self):
        """Run the complete modernization pipeline."""
        print("=" * 60)
        print("Legacy Code Modernization Pipeline")
        print("=" * 60)
        
        try:
            # Phase 1-2: Parse
            nodes = self.parse_legacy_code()
            
            # Phase 3-8: Translate
            translations = self.translate_code(nodes)
            
            # Phase 10: Validate
            validation_reports = self.validate_translations(nodes, translations)
            
            # Check if validation passed
            all_valid = all(
                r.syntax_valid and r.structure_valid and 
                r.symbols_preserved and r.dependencies_complete
                for r in validation_reports
            )
            
            if not all_valid:
                print("\n✗ Validation failed - halting pipeline")
                return False
            
            # Phase 11: Document
            documentation = self.generate_documentation(nodes, translations)
            
            # Phase 12: Audit (NEW)
            audit_report = self.run_audit()
            
            # Check if audit passed
            if not audit_report.overall_passed:
                print("\n✗ Audit failed - halting pipeline before deployment")
                print("\nFailed Checks:")
                for check in audit_report.check_results:
                    if not check.passed:
                        print(f"  - {check.check_name}: {check.message}")
                return False
            
            # Phase 13: Deploy
            self.deploy()
            
            print("\n" + "=" * 60)
            print("✓ Pipeline completed successfully!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"\n✗ Pipeline failed with error: {e}")
            return False


def example_successful_pipeline():
    """Example: Complete pipeline with successful audit."""
    print("\n\n=== Example 1: Successful Pipeline ===\n")
    
    pipeline = MockPipeline()
    success = pipeline.run_complete_pipeline()
    
    if success:
        print("\n✓ All phases completed, code deployed to production")
    else:
        print("\n✗ Pipeline halted due to failures")


def example_failed_validation():
    """Example: Pipeline halts at validation phase."""
    print("\n\n=== Example 2: Failed Validation (Audit Not Reached) ===\n")
    
    # Create pipeline with bad translation
    pipeline = MockPipeline()
    
    # Override with invalid translation
    def bad_translate(nodes):
        return {
            "calculate_total": "def calculate_total(x): pass",  # Incomplete
            "process_order": "def process_order(): return True"  # Wrong params
        }
    
    pipeline.translate_code = bad_translate
    
    success = pipeline.run_complete_pipeline()
    
    if not success:
        print("\n✓ Pipeline correctly halted at validation phase")


def example_failed_audit():
    """Example: Pipeline halts at audit phase."""
    print("\n\n=== Example 3: Failed Audit (Before Deployment) ===\n")
    
    # Create pipeline with audit issues
    pipeline = MockPipeline()
    
    # Override documentation to be empty (will fail audit)
    def bad_docs(nodes, translations):
        return {node.name: "" for node in nodes}  # Empty docs
    
    pipeline.generate_documentation = bad_docs
    
    success = pipeline.run_complete_pipeline()
    
    if not success:
        print("\n✓ Pipeline correctly halted at audit phase before deployment")


def show_pipeline_flow():
    """Show the complete pipeline flow diagram."""
    print("\n\n=== Pipeline Flow with Audit ===\n")
    
    flow = """
+-------------------------------------------------------------+
|                  LEGACY CODE MODERNIZATION                  |
|                      PIPELINE FLOW                          |
+-------------------------------------------------------------+

Phase 1-2: PARSING
    - Parse legacy code (Java, COBOL, etc.)
    - Generate AST nodes
    - Build dependency graph
         |
         v
Phase 3-8: TRANSLATION
    - Context optimization
    - LLM-based translation
    - Generate Python code
         |
         v
Phase 10: VALIDATION [GATE 1]
    - Syntax validation (AST parsing)
    - Structure preservation check
    - Symbol preservation check
    - Dependency completeness check
    - Translation completeness check
         |
         v
    [FAIL] -> HALT PIPELINE [X]
         |
         v
    [PASS] -> Continue
         |
         v
Phase 11: DOCUMENTATION
    - Generate module documentation
    - API reference
    - Usage examples
         |
         v
Phase 12: AUDIT [GATE 2] (NEW)
    - Validation determinism check
    - LLM leakage prevention
    - Configuration compliance
    - Dependency graph integrity
    - Syntax robustness
    - Structure validation
    - Symbol preservation
    - Translation completeness
    - Unit test stub quality
    - Documentation accuracy
    - Report schema consistency
    - Performance validation
    - Pipeline sequence integrity
         |
         v
    [FAIL] -> HALT PIPELINE [X]
         |
         v
    [PASS] -> Continue
         |
         v
Phase 13: DEPLOYMENT
    - Deploy translated code
    - Publish documentation
    - Register unit tests
         |
         v
    [OK] PRODUCTION

Key Points:
- Validation (Phase 10) is the first quality gate
- Audit (Phase 12) is the final integrity gate before deployment
- Both gates must pass for deployment to proceed
- Audit ensures no LLM leakage and validates entire pipeline
"""
    
    print(flow)


if __name__ == "__main__":
    print("Pipeline Integration with Audit Examples\n")
    
    # Show pipeline flow
    show_pipeline_flow()
    
    # Run examples
    example_successful_pipeline()
    example_failed_validation()
    example_failed_audit()
    
    print("\n" + "=" * 60)
    print("✓ All examples completed")
    print("=" * 60)
