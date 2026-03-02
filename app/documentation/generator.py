"""Documentation generator for translated code.

This module provides deterministic documentation generation without LLM usage,
consuming TranslationResult, ValidationReport, and EvaluationReport.

Architecture:
- Pure service layer (no FastAPI, CLI, or LLM calls)
- Deterministic outputs for testing
- JSON-serializable reports
- Immutable inputs
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DocumentationReport:
    """Documentation report for a translated module.
    
    Attributes:
        module_name: Name of the module
        translation_summary: Summary of translation results
        validation_status: Validation status summary
        evaluation_metrics: Key evaluation metrics
        prompt_metadata: Prompt version and checksum information
        timestamp: Report generation timestamp (ISO format)
    """
    module_name: str
    translation_summary: Dict[str, Any]
    validation_status: Dict[str, Any]
    evaluation_metrics: Dict[str, Any]
    prompt_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the report
        """
        return asdict(self)


class DocumentationGenerator:
    """Generator for deterministic documentation from pipeline outputs.
    
    This class generates structured documentation by consuming translation,
    validation, and evaluation results without calling LLMs.
    """
    
    def __init__(self) -> None:
        """Initialize documentation generator."""
        logger.info("DocumentationGenerator initialized")
    
    def generate_documentation(
        self,
        translation_results: List,
        validation_reports: List,
        evaluation_report: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Generate documentation for all translated modules.
        
        Args:
            translation_results: List of TranslationResult objects
            validation_reports: List of ValidationReport objects
            evaluation_report: Optional evaluation report dictionary
            
        Returns:
            Dictionary mapping module_name to documentation string
        """
        logger.info(
            f"Generating documentation for {len(translation_results)} modules",
            extra={"module_count": len(translation_results)}
        )
        
        documentation = {}
        
        for i, trans_result in enumerate(translation_results):
            if trans_result.translated_code:
                # Get corresponding validation report
                validation_report = None
                if i < len(validation_reports):
                    validation_report = validation_reports[i]
                
                # Generate documentation
                doc_content = self._generate_module_documentation(
                    trans_result,
                    validation_report,
                    evaluation_report
                )
                
                documentation[trans_result.module_name] = doc_content
        
        logger.info(
            f"Documentation generated for {len(documentation)} modules",
            extra={"doc_count": len(documentation)}
        )
        
        return documentation
    
    def generate_report(
        self,
        translation_result,
        validation_report,
        evaluation_report: Optional[Dict[str, Any]] = None
    ) -> DocumentationReport:
        """Generate structured documentation report for a single module.
        
        Args:
            translation_result: TranslationResult object
            validation_report: ValidationReport object
            evaluation_report: Optional evaluation report dictionary
            
        Returns:
            DocumentationReport with structured metadata
        """
        # Extract translation summary
        translation_summary = {
            "status": translation_result.status.value if hasattr(translation_result.status, 'value') else str(translation_result.status),
            "dependencies_used": translation_result.dependencies_used,
            "token_usage": translation_result.token_usage,
            "has_code": bool(translation_result.translated_code),
            "errors": translation_result.errors,
            "warnings": translation_result.warnings
        }
        
        # Extract validation status
        validation_status = {
            "structure_valid": validation_report.structure_valid,
            "symbols_preserved": validation_report.symbols_preserved,
            "syntax_valid": validation_report.syntax_valid,
            "dependencies_complete": validation_report.dependencies_complete,
            "missing_dependencies": validation_report.missing_dependencies,
            "error_count": len(validation_report.errors)
        }
        
        # Extract evaluation metrics
        evaluation_metrics = {}
        if evaluation_report:
            if "token_metrics" in evaluation_report:
                evaluation_metrics["token_efficiency"] = {
                    "reduction_percentage": evaluation_report["token_metrics"].get("reduction_percentage", 0),
                    "efficiency_score": evaluation_report["token_metrics"].get("efficiency_score", 0)
                }
            if "quality_metrics" in evaluation_report:
                evaluation_metrics["quality"] = {
                    "validation_pass_rate": evaluation_report["quality_metrics"].get("validation_pass_rate", 0),
                    "syntax_error_rate": evaluation_report["quality_metrics"].get("syntax_error_rate", 0)
                }
        
        # Extract prompt metadata
        prompt_metadata = {}
        if evaluation_report and "prompt_metadata" in evaluation_report:
            prompt_metadata = evaluation_report["prompt_metadata"]
        elif evaluation_report and "prompt_versions" in evaluation_report:
            # Fallback to old format
            prompt_metadata = {"versions": evaluation_report["prompt_versions"]}
        
        # Create report
        report = DocumentationReport(
            module_name=translation_result.module_name,
            translation_summary=translation_summary,
            validation_status=validation_status,
            evaluation_metrics=evaluation_metrics,
            prompt_metadata=prompt_metadata,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        logger.debug(
            f"Generated documentation report for {translation_result.module_name}",
            extra={"module_name": translation_result.module_name}
        )
        
        return report
    
    def _generate_module_documentation(
        self,
        translation_result,
        validation_report,
        evaluation_report: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate documentation string for a module.
        
        Args:
            translation_result: TranslationResult object
            validation_report: ValidationReport object
            evaluation_report: Optional evaluation report dictionary
            
        Returns:
            Documentation string in Markdown format
        """
        lines = [
            f"# {translation_result.module_name}",
            "",
            "## Translation Summary",
            "",
            f"- Status: {translation_result.status.value if hasattr(translation_result.status, 'value') else str(translation_result.status)}",
            f"- Dependencies Used: {len(translation_result.dependencies_used)}",
            f"- Token Usage: {translation_result.token_usage}",
            ""
        ]
        
        # Add validation status
        if validation_report:
            lines.extend([
                "## Validation Status",
                "",
                f"- Structure Valid: {'✓' if validation_report.structure_valid else '✗'}",
                f"- Symbols Preserved: {'✓' if validation_report.symbols_preserved else '✗'}",
                f"- Syntax Valid: {'✓' if validation_report.syntax_valid else '✗'}",
                f"- Dependencies Complete: {'✓' if validation_report.dependencies_complete else '✗'}",
                ""
            ])
            
            if validation_report.missing_dependencies:
                lines.extend([
                    "### Missing Dependencies",
                    ""
                ])
                for dep in validation_report.missing_dependencies:
                    lines.append(f"- {dep}")
                lines.append("")
            
            if validation_report.errors:
                lines.extend([
                    "### Validation Errors",
                    ""
                ])
                for error in validation_report.errors:
                    lines.append(f"- {error}")
                lines.append("")
        
        # Add evaluation metrics
        if evaluation_report:
            lines.extend([
                "## Evaluation Metrics",
                ""
            ])
            
            if "token_metrics" in evaluation_report:
                token_metrics = evaluation_report["token_metrics"]
                lines.extend([
                    "### Token Efficiency",
                    "",
                    f"- Reduction: {token_metrics.get('reduction_percentage', 0)}%",
                    f"- Efficiency Score: {token_metrics.get('efficiency_score', 0)}/100",
                    ""
                ])
            
            if "quality_metrics" in evaluation_report:
                quality_metrics = evaluation_report["quality_metrics"]
                lines.extend([
                    "### Quality Metrics",
                    "",
                    f"- Validation Pass Rate: {quality_metrics.get('validation_pass_rate', 0)}%",
                    f"- Syntax Error Rate: {quality_metrics.get('syntax_error_rate', 0)}%",
                    ""
                ])
        
        # Add translated code preview
        if translation_result.translated_code:
            lines.extend([
                "## Translated Code",
                "",
                "```python",
                translation_result.translated_code[:500] + ("..." if len(translation_result.translated_code) > 500 else ""),
                "```",
                ""
            ])
        
        # Add warnings
        if translation_result.warnings:
            lines.extend([
                "## Warnings",
                ""
            ])
            for warning in translation_result.warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        return "\n".join(lines)
