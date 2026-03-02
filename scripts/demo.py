#!/usr/bin/env python3
"""Deterministic demo script for Legacy Code Modernization Pipeline.

This script demonstrates reproducible pipeline execution with:
- Fixed sample dataset (java_small)
- Deterministic mode enabled
- SHA256 hash verification
- No external randomness

Usage:
    python demo.py

Output:
    - demo_output/ directory with translation results
    - SHA256 hash of outputs for reproducibility verification
"""

import asyncio
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any

from app.pipeline.service import PipelineService
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_output_hash(output_dir: Path) -> str:
    """Compute deterministic SHA256 hash of all outputs.
    
    Args:
        output_dir: Directory containing output files
        
    Returns:
        SHA256 hex digest of sorted output contents
    """
    hasher = hashlib.sha256()
    
    # Sort files for deterministic ordering
    files = sorted(output_dir.rglob("*.json"))
    
    for file_path in files:
        # Add filename to hash
        hasher.update(file_path.name.encode())
        
        # Add file content to hash
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Normalize whitespace for determinism
            normalized = json.dumps(json.loads(content), sort_keys=True)
            hasher.update(normalized.encode())
    
    return hasher.hexdigest()


def save_results(result: Dict[str, Any], output_dir: Path) -> None:
    """Save pipeline results to output directory.
    
    Args:
        result: Pipeline execution result
        output_dir: Directory to save results
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save full result
    with open(output_dir / "full_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    
    # Save translation results
    if "translation_results" in result:
        translations = []
        for tr in result["translation_results"]:
            translations.append({
                "module_name": tr.module_name,
                "status": tr.status.value,
                "translated_code": tr.translated_code,
                "dependencies_used": tr.dependencies_used,
                "token_usage": tr.token_usage,
                "errors": tr.errors,
                "warnings": tr.warnings
            })
        
        with open(output_dir / "translations.json", "w", encoding="utf-8") as f:
            json.dump(translations, f, indent=2, sort_keys=True)
    
    # Save validation reports
    if "validation_reports" in result:
        validations = []
        for vr in result["validation_reports"]:
            validations.append({
                "structure_valid": vr.structure_valid,
                "symbols_preserved": vr.symbols_preserved,
                "syntax_valid": vr.syntax_valid,
                "dependencies_complete": vr.dependencies_complete,
                "missing_dependencies": vr.missing_dependencies,
                "errors": vr.errors
            })
        
        with open(output_dir / "validations.json", "w", encoding="utf-8") as f:
            json.dump(validations, f, indent=2, sort_keys=True)
    
    # Save evaluation report
    if "evaluation_report" in result:
        with open(output_dir / "evaluation.json", "w", encoding="utf-8") as f:
            json.dump(result["evaluation_report"], f, indent=2, sort_keys=True)
    
    # Save audit report
    if "audit_report" in result:
        audit_dict = {
            "overall_passed": result["audit_report"].overall_passed,
            "total_checks": result["audit_report"].total_checks,
            "passed_checks": result["audit_report"].passed_checks,
            "failed_checks": result["audit_report"].failed_checks,
            "execution_time_ms": result["audit_report"].execution_time_ms,
            "timestamp": result["audit_report"].timestamp,
            "summary": result["audit_report"].summary
        }
        
        with open(output_dir / "audit.json", "w", encoding="utf-8") as f:
            json.dump(audit_dict, f, indent=2, sort_keys=True)


async def run_demo() -> Dict[str, Any]:
    """Run deterministic demo pipeline.
    
    Returns:
        Dictionary with demo results and hash
    """
    print("=" * 70)
    print("Legacy Code Modernization Pipeline - Deterministic Demo")
    print("=" * 70)
    print()
    
    # Verify deterministic mode
    settings = get_settings()
    if not settings.DETERMINISTIC_MODE:
        print("WARNING: DETERMINISTIC_MODE is not enabled in .env")
        print("Set DETERMINISTIC_MODE=true for reproducible outputs")
        print()
    
    # Setup
    repo_path = "sample_repos/java_small.zip"
    output_dir = Path("demo_output")
    
    # Clean previous outputs
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    print(f"Input: {repo_path}")
    print(f"Output: {output_dir}/")
    print(f"Deterministic Mode: {settings.DETERMINISTIC_MODE}")
    print()
    
    # Initialize pipeline
    print("Initializing pipeline...")
    pipeline = PipelineService()
    
    # Execute full pipeline
    print("Executing full translation pipeline...")
    print()
    
    result = await pipeline.execute_full_pipeline(
        repo_path=repo_path,
        source_language="java",
        target_language="python",
        repository_id="demo-java-small"
    )
    
    # Check success
    if not result.success:
        print("❌ Pipeline failed!")
        print(f"Errors: {result.errors}")
        return {
            "success": False,
            "errors": result.errors
        }
    
    print("✓ Pipeline execution complete")
    print()
    
    # Save results
    print("Saving results...")
    result_dict = {
        "success": result.success,
        "repository_id": result.repository_id,
        "file_count": result.file_count,
        "ast_node_count": result.ast_node_count,
        "graph_node_count": result.graph_node_count,
        "graph_edge_count": result.graph_edge_count,
        "translation_results": result.translation_results,
        "validation_reports": result.validation_reports,
        "evaluation_report": result.evaluation_report,
        "audit_report": result.audit_report,
        "errors": result.errors,
        "warnings": result.warnings
    }
    
    save_results(result_dict, output_dir)
    print(f"✓ Results saved to {output_dir}/")
    print()
    
    # Compute hash
    print("Computing output hash...")
    output_hash = compute_output_hash(output_dir)
    print(f"✓ Output hash: {output_hash}")
    print()
    
    # Print summary
    print("=" * 70)
    print("Demo Summary")
    print("=" * 70)
    print(f"Files processed: {result.file_count}")
    print(f"AST nodes: {result.ast_node_count}")
    print(f"Graph nodes: {result.graph_node_count}")
    print(f"Graph edges: {result.graph_edge_count}")
    
    if result.translation_results:
        success_count = sum(1 for tr in result.translation_results if tr.status.value == "success")
        print(f"Translations: {success_count}/{len(result.translation_results)} successful")
    
    if result.validation_reports:
        valid_count = sum(1 for vr in result.validation_reports if vr.syntax_valid)
        print(f"Validations: {valid_count}/{len(result.validation_reports)} passed")
    
    if result.audit_report:
        print(f"Audit: {result.audit_report.passed_checks}/{result.audit_report.total_checks} checks passed")
    
    if result.evaluation_report:
        efficiency = result.evaluation_report["token_metrics"]["efficiency_score"]
        print(f"Efficiency score: {efficiency:.1f}/100")
    
    print()
    print(f"Output hash: {output_hash}")
    print()
    print("✓ Demo complete!")
    print()
    
    if settings.DETERMINISTIC_MODE:
        print("Reproducibility: Run this script again to verify identical hash")
    else:
        print("Note: Enable DETERMINISTIC_MODE=true in .env for reproducible outputs")
    
    return {
        "success": True,
        "output_hash": output_hash,
        "output_dir": str(output_dir),
        "file_count": result.file_count,
        "translation_count": len(result.translation_results) if result.translation_results else 0,
        "validation_count": len(result.validation_reports) if result.validation_reports else 0
    }


def main() -> None:
    """Main entry point."""
    try:
        result = asyncio.run(run_demo())
        
        if result["success"]:
            exit(0)
        else:
            exit(1)
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed")
        exit(1)


if __name__ == "__main__":
    main()
