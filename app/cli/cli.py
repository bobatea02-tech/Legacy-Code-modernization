"""Command Line Interface for Legacy Code Modernization Engine.

This module provides a thin CLI adapter using Typer framework.
All business logic is delegated to service layer - no pipeline reimplementation.

Commands:
- ingest: Ingest repository and extract metadata
- optimize: Run AST parsing + dependency graph + context optimization
- translate: Full pipeline execution (ingestion → translation → validation)
- validate: Validate existing translations

Architecture: CLI = Developer interface layer (thin orchestration only)
"""

import sys
from pathlib import Path
from typing import Optional
import json

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from app.ingestion.ingestor import RepositoryIngestor, IngestionConfig, IngestionError
from app.parsers.java_parser import JavaParser
from app.parsers.cobol_parser import CobolParser
from app.dependency_graph.graph_builder import GraphBuilder
from app.context_optimizer.optimizer import ContextOptimizer
from app.translation.orchestrator import TranslationOrchestrator, TranslationStore
from app.llm.gemini_client import GeminiClient
from app.validation import ValidationEngine
from app.audit import AuditEngine
from app.pipeline import PipelineService
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
console = Console()

# Create Typer app
app = typer.Typer(
    name="legacy-modernizer",
    help="Legacy Code Modernization Engine - Compiler-style code translation",
    add_completion=False
)


# ============================================================================
# Helper Functions
# ============================================================================

def validate_repo_path(repo_path: str) -> Path:
    """Validate repository path exists.
    
    Args:
        repo_path: Path to repository
        
    Returns:
        Validated Path object
        
    Raises:
        typer.Exit: If path doesn't exist
    """
    path = Path(repo_path)
    
    if not path.exists():
        console.print(f"[red]Error:[/red] Repository path does not exist: {repo_path}")
        raise typer.Exit(code=1)
    
    return path


def get_parser(language: str):
    """Get parser for specified language.
    
    Args:
        language: Language identifier (java, cobol)
        
    Returns:
        Parser instance
        
    Raises:
        typer.Exit: If language not supported
    """
    language_lower = language.lower()
    
    if language_lower == "java":
        return JavaParser()
    elif language_lower == "cobol":
        return CobolParser()
    else:
        console.print(f"[red]Error:[/red] Unsupported language: {language}")
        raise typer.Exit(code=1)


def print_json_summary(data: dict, title: str = "Summary") -> None:
    """Print JSON data as formatted summary.
    
    Args:
        data: Dictionary to print
        title: Title for the summary
    """
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print(json.dumps(data, indent=2))


def print_validation_summary(reports: list, verbose: bool = False) -> None:
    """Print validation report summary.
    
    Args:
        reports: List of ValidationReport objects
        verbose: Whether to print detailed information
    """
    if not reports:
        console.print("[yellow]No validation reports to display[/yellow]")
        return
    
    # Create summary table
    table = Table(title="Validation Summary")
    table.add_column("Module", style="cyan")
    table.add_column("Syntax", style="green")
    table.add_column("Structure", style="green")
    table.add_column("Symbols", style="green")
    table.add_column("Dependencies", style="green")
    table.add_column("Errors", style="red")
    
    for report in reports:
        table.add_row(
            report.module_name if hasattr(report, 'module_name') else "N/A",
            "✓" if report.syntax_valid else "✗",
            "✓" if report.structure_valid else "✗",
            "✓" if report.symbols_preserved else "✗",
            "✓" if report.dependencies_complete else "✗",
            str(len(report.errors))
        )
    
    console.print(table)
    
    # Print detailed errors if verbose
    if verbose:
        for i, report in enumerate(reports):
            if report.errors:
                console.print(f"\n[bold red]Errors in module {i+1}:[/bold red]")
                for error in report.errors:
                    console.print(f"  • {error}")
            
            if report.missing_dependencies:
                console.print(f"\n[bold yellow]Missing dependencies in module {i+1}:[/bold yellow]")
                for dep in report.missing_dependencies:
                    console.print(f"  • {dep}")


# ============================================================================
# Command: ingest
# ============================================================================

@app.command()
def ingest(
    repo_path: str = typer.Argument(..., help="Path to repository (directory or ZIP file)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print detailed output")
) -> None:
    """Ingest repository and extract file metadata.
    
    Calls RepositoryIngestionService to:
    - Extract ZIP or scan directory
    - Detect file languages
    - Validate file sizes
    - Generate SHA256 hashes
    
    Returns ingestion summary with file count and metadata.
    """
    console.print("[bold]Repository Ingestion[/bold]\n")
    
    try:
        # Validate path
        path = validate_repo_path(repo_path)
        
        # Initialize ingestion service
        config = IngestionConfig()
        ingestor = RepositoryIngestor(config=config)
        
        console.print(f"Ingesting: {path}")
        
        # Ingest repository
        if path.suffix == '.zip':
            file_metadata_list = ingestor.ingest_zip(str(path))
        else:
            console.print("[red]Error:[/red] Only ZIP files are currently supported")
            raise typer.Exit(code=1)
        
        # Generate summary
        summary = {
            "repository_path": str(path),
            "status": "success",
            "file_count": len(file_metadata_list),
            "languages": list(set(fm.language for fm in file_metadata_list)),
            "total_size_bytes": sum(fm.size for fm in file_metadata_list)
        }
        
        # Print summary
        console.print(f"\n[green]✓[/green] Ingestion complete")
        console.print(f"  Files processed: {summary['file_count']}")
        console.print(f"  Languages detected: {', '.join(summary['languages'])}")
        console.print(f"  Total size: {summary['total_size_bytes']:,} bytes")
        
        # Print detailed file list if verbose
        if verbose:
            console.print("\n[bold]File Details:[/bold]")
            for fm in file_metadata_list:
                console.print(f"  • {fm.relative_path} ({fm.language}, {fm.size} bytes)")
        
        # Cleanup
        ingestor.cleanup()
        
    except IngestionError as e:
        console.print(f"[red]Ingestion Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Ingestion failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# Command: optimize
# ============================================================================

@app.command()
def optimize(
    repo_path: str = typer.Argument(..., help="Path to repository (ZIP file)"),
    language: str = typer.Option("java", "--language", "-l", help="Source language (java, cobol)"),
    depth: Optional[int] = typer.Option(None, "--depth", "-d", help="Context expansion depth"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print detailed output")
) -> None:
    """Run AST parsing + dependency graph + context optimization.
    
    Pipeline:
    1. Ingest repository
    2. Parse files to AST
    3. Build dependency graph
    4. Optimize context for each node
    
    Returns bounded context summary (node count, depth used).
    """
    console.print("[bold]Context Optimization Pipeline[/bold]\n")
    
    try:
        # Validate path
        path = validate_repo_path(repo_path)
        
        # Get settings
        settings = get_settings()
        expansion_depth = depth if depth is not None else settings.CONTEXT_EXPANSION_DEPTH
        
        # Phase 1: Ingest
        console.print("[1/4] Ingesting repository...")
        config = IngestionConfig()
        ingestor = RepositoryIngestor(config=config)
        file_metadata_list = ingestor.ingest_zip(str(path))
        console.print(f"  ✓ Ingested {len(file_metadata_list)} files")
        
        # Phase 2: Parse to AST
        console.print("\n[2/4] Parsing files to AST...")
        parser = get_parser(language)
        ast_nodes = []
        
        for file_meta in file_metadata_list:
            if file_meta.language.lower() == language.lower():
                try:
                    nodes = parser.parse_file(str(file_meta.path))
                    ast_nodes.extend(nodes)
                except Exception as e:
                    if verbose:
                        console.print(f"  [yellow]Warning:[/yellow] Failed to parse {file_meta.relative_path}: {e}")
        
        console.print(f"  ✓ Parsed {len(ast_nodes)} AST nodes")
        
        if not ast_nodes:
            console.print("[red]Error:[/red] No parseable files found")
            raise typer.Exit(code=1)
        
        # Phase 3: Build dependency graph
        console.print("\n[3/4] Building dependency graph...")
        graph_builder = GraphBuilder()
        dependency_graph = graph_builder.build_graph(ast_nodes)
        
        node_count = dependency_graph.number_of_nodes()
        edge_count = dependency_graph.number_of_edges()
        console.print(f"  ✓ Built graph: {node_count} nodes, {edge_count} edges")
        
        # Phase 4: Optimize context for sample nodes
        console.print(f"\n[4/4] Optimizing context (depth={expansion_depth})...")
        context_optimizer = ContextOptimizer(expansion_depth=expansion_depth)
        ast_index = {node.id: node for node in ast_nodes}
        
        # Optimize context for first few nodes as examples
        sample_size = min(3, len(ast_nodes))
        optimizations = []
        
        for i, node in enumerate(ast_nodes[:sample_size]):
            try:
                optimized = context_optimizer.optimize_context(
                    target_node_id=node.id,
                    dependency_graph=dependency_graph,
                    ast_index=ast_index,
                    expansion_depth=expansion_depth
                )
                optimizations.append({
                    "node_name": node.name,
                    "included_nodes": len(optimized.included_nodes),
                    "excluded_nodes": len(optimized.excluded_nodes),
                    "estimated_tokens": optimized.estimated_tokens
                })
            except Exception as e:
                if verbose:
                    console.print(f"  [yellow]Warning:[/yellow] Failed to optimize {node.name}: {e}")
        
        console.print(f"  ✓ Optimized context for {len(optimizations)} sample nodes")
        
        # Print summary
        console.print("\n[bold green]Optimization Complete[/bold green]")
        
        summary = {
            "repository": str(path),
            "language": language,
            "ast_nodes": len(ast_nodes),
            "graph_nodes": node_count,
            "graph_edges": edge_count,
            "expansion_depth": expansion_depth,
            "sample_optimizations": optimizations
        }
        
        if verbose:
            print_json_summary(summary, "Optimization Summary")
        else:
            console.print(f"  AST Nodes: {len(ast_nodes)}")
            console.print(f"  Graph: {node_count} nodes, {edge_count} edges")
            console.print(f"  Depth: {expansion_depth}")
        
        # Cleanup
        ingestor.cleanup()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Optimization failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# Command: translate
# ============================================================================

@app.command()
def translate(
    repo_path: str = typer.Argument(..., help="Path to repository (ZIP file)"),
    language: str = typer.Option("java", "--language", "-l", help="Source language (java, cobol)"),
    target: str = typer.Option("python", "--target", "-t", help="Target language"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print detailed output")
) -> None:
    """Execute full translation pipeline using centralized PipelineService.
    
    Pipeline:
    1. Ingestion → File metadata
    2. AST Parsing → AST nodes
    3. Dependency Graph → NetworkX DiGraph
    4. Context Optimization → Bounded context
    5. Translation → Python code
    6. Validation → Validation reports
    7. Audit → Audit report
    
    Returns structured summary (not raw code dump).
    """
    console.print("[bold]Full Translation Pipeline[/bold]\n")
    
    try:
        # Validate path
        path = validate_repo_path(repo_path)
        
        # Initialize centralized pipeline service
        console.print("Initializing pipeline service...")
        pipeline_service = PipelineService()
        
        # Execute full pipeline
        console.print(f"Executing pipeline for {path}...\n")
        
        import asyncio
        pipeline_result = asyncio.run(pipeline_service.execute_full_pipeline(
            repo_path=str(path),
            source_language=language,
            target_language=target
        ))
        
        if not pipeline_result.success:
            console.print(f"[red]Pipeline failed:[/red]")
            for error in pipeline_result.errors:
                console.print(f"  • {error}")
            raise typer.Exit(code=1)
        
        # Print summary
        console.print("\n[bold green]Translation Complete[/bold green]")
        
        summary = {
            "repository": str(path),
            "source_language": language,
            "target_language": target,
            "files_ingested": pipeline_result.file_count,
            "ast_nodes": pipeline_result.ast_node_count,
            "translations": {
                "total": len(pipeline_result.translation_results),
                "successful": sum(1 for r in pipeline_result.translation_results if r.status.value == "success"),
                "failed": sum(1 for r in pipeline_result.translation_results if r.status.value == "failed")
            },
            "validation": {
                "total": len(pipeline_result.validation_reports),
                "passed": sum(
                    1 for r in pipeline_result.validation_reports
                    if r.syntax_valid and r.structure_valid and r.symbols_preserved and r.dependencies_complete
                ),
                "failed": sum(
                    1 for r in pipeline_result.validation_reports
                    if not (r.syntax_valid and r.structure_valid and r.symbols_preserved and r.dependencies_complete)
                )
            },
            "audit": {
                "overall_passed": pipeline_result.audit_report.overall_passed if pipeline_result.audit_report else False,
                "checks_passed": pipeline_result.audit_report.passed_checks if pipeline_result.audit_report else 0,
                "checks_failed": pipeline_result.audit_report.failed_checks if pipeline_result.audit_report else 0
            }
        }
        
        # Add evaluation summary if available
        if pipeline_result.evaluation_report:
            eval_report = pipeline_result.evaluation_report
            summary["evaluation"] = {
                "efficiency_score": eval_report["token_metrics"]["efficiency_score"],
                "token_reduction_pct": eval_report["token_metrics"]["reduction_percentage"],
                "runtime_seconds": eval_report["runtime_metrics"]["total_runtime_seconds"],
                "validation_pass_rate": eval_report["quality_metrics"]["validation_pass_rate"]
            }
        
        if verbose:
            print_json_summary(summary, "Translation Summary")
            print_validation_summary(pipeline_result.validation_reports, verbose=True)
            
            # Print evaluation details if available
            if pipeline_result.evaluation_report:
                console.print("\n[bold cyan]Evaluation Report[/bold cyan]")
                eval_report = pipeline_result.evaluation_report
                console.print(f"  Efficiency Score: {eval_report['token_metrics']['efficiency_score']}/100")
                console.print(f"  Token Reduction: {eval_report['token_metrics']['reduction_percentage']}%")
                console.print(f"  Runtime: {eval_report['runtime_metrics']['total_runtime_seconds']:.2f}s")
                console.print(f"  Validation Pass Rate: {eval_report['quality_metrics']['validation_pass_rate']}%")
        else:
            console.print(f"\n  Files: {pipeline_result.file_count}")
            console.print(f"  Translations: {summary['translations']['successful']}/{summary['translations']['total']} successful")
            console.print(f"  Validation: {summary['validation']['passed']}/{summary['validation']['total']} passed")
            console.print(f"  Audit: {'✓ PASSED' if summary['audit']['overall_passed'] else '✗ FAILED'}")
            
            # Print condensed evaluation summary
            if pipeline_result.evaluation_report:
                eval_report = pipeline_result.evaluation_report
                console.print(f"  Efficiency: {eval_report['token_metrics']['efficiency_score']}/100 "
                            f"({eval_report['token_metrics']['reduction_percentage']}% token reduction)")
        
        # Exit with error if audit failed
        if pipeline_result.audit_report and not pipeline_result.audit_report.overall_passed:
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Translation failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# Command: validate
# ============================================================================

@app.command()
def validate(
    repo_path: str = typer.Argument(..., help="Path to repository (ZIP file)"),
    language: str = typer.Option("java", "--language", "-l", help="Source language (java, cobol)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print detailed output")
) -> None:
    """Validate repository structure and dependencies.
    
    Runs validation checks without translation:
    1. Parse files to AST
    2. Build dependency graph
    3. Check for circular dependencies
    4. Validate file structure
    
    Returns validation summary.
    """
    console.print("[bold]Repository Validation[/bold]\n")
    
    try:
        # Validate path
        path = validate_repo_path(repo_path)
        
        # Phase 1: Ingest
        console.print("[1/3] Ingesting repository...")
        config = IngestionConfig()
        ingestor = RepositoryIngestor(config=config)
        file_metadata_list = ingestor.ingest_zip(str(path))
        console.print(f"  ✓ Ingested {len(file_metadata_list)} files")
        
        # Phase 2: Parse to AST
        console.print("\n[2/3] Parsing files to AST...")
        parser = get_parser(language)
        ast_nodes = []
        parse_errors = []
        
        for file_meta in file_metadata_list:
            if file_meta.language.lower() == language.lower():
                try:
                    nodes = parser.parse_file(str(file_meta.path))
                    ast_nodes.extend(nodes)
                except Exception as e:
                    parse_errors.append(f"{file_meta.relative_path}: {e}")
        
        console.print(f"  ✓ Parsed {len(ast_nodes)} AST nodes")
        
        if parse_errors and verbose:
            console.print(f"\n  [yellow]Parse errors:[/yellow]")
            for error in parse_errors[:5]:  # Show first 5
                console.print(f"    • {error}")
        
        if not ast_nodes:
            console.print("[red]Error:[/red] No parseable files found")
            raise typer.Exit(code=1)
        
        # Phase 3: Build and validate dependency graph
        console.print("\n[3/3] Validating dependency graph...")
        graph_builder = GraphBuilder()
        dependency_graph = graph_builder.build_graph(ast_nodes)
        
        node_count = dependency_graph.number_of_nodes()
        edge_count = dependency_graph.number_of_edges()
        
        # Check for circular dependencies
        import networkx as nx
        is_dag = nx.is_directed_acyclic_graph(dependency_graph)
        
        if is_dag:
            console.print(f"  ✓ No circular dependencies detected")
        else:
            cycles = list(nx.simple_cycles(dependency_graph))
            console.print(f"  [red]✗[/red] Circular dependencies detected: {len(cycles)} cycles")
            if verbose and cycles:
                console.print(f"\n  [yellow]Sample cycles:[/yellow]")
                for cycle in cycles[:3]:  # Show first 3
                    console.print(f"    • {' → '.join(cycle)}")
        
        # Print summary
        console.print("\n[bold green]Validation Complete[/bold green]")
        
        summary = {
            "repository": str(path),
            "language": language,
            "files_ingested": len(file_metadata_list),
            "ast_nodes": len(ast_nodes),
            "parse_errors": len(parse_errors),
            "graph_nodes": node_count,
            "graph_edges": edge_count,
            "is_dag": is_dag,
            "circular_dependencies": 0 if is_dag else len(list(nx.simple_cycles(dependency_graph)))
        }
        
        if verbose:
            print_json_summary(summary, "Validation Summary")
        else:
            console.print(f"\n  Files: {len(file_metadata_list)}")
            console.print(f"  AST Nodes: {len(ast_nodes)}")
            console.print(f"  Graph: {node_count} nodes, {edge_count} edges")
            console.print(f"  DAG: {'✓ Yes' if is_dag else '✗ No (circular dependencies)'}")
        
        # Cleanup
        ingestor.cleanup()
        
        # Exit with error if validation failed
        if not is_dag or parse_errors:
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error(f"Validation failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
