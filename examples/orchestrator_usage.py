"""Example usage of TranslationOrchestrator.

This example demonstrates how to use the TranslationOrchestrator to translate
legacy code to Python in dependency-aware order.
"""

import asyncio
from pathlib import Path

from app.parsers.java_parser import JavaParser
from app.dependency_graph.graph_builder import GraphBuilder
from app.translation.orchestrator import TranslationOrchestrator, TranslationStatus
from app.llm.gemini_client import GeminiClient
from app.validation.validator import CodeValidator
from app.core.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Run translation orchestration example."""
    
    # Step 1: Parse source files
    logger.info("Step 1: Parsing Java source files")
    parser = JavaParser()
    
    # Example: Parse multiple Java files
    source_files = [
        "sample_repos/Calculator.java",
        "sample_repos/MathUtils.java",
        "sample_repos/Main.java"
    ]
    
    all_ast_nodes = []
    for file_path in source_files:
        if Path(file_path).exists():
            ast_nodes = parser.parse_file(file_path)
            all_ast_nodes.extend(ast_nodes)
            logger.info(f"Parsed {file_path}: {len(ast_nodes)} nodes")
    
    if not all_ast_nodes:
        logger.error("No AST nodes parsed. Ensure source files exist.")
        return
    
    # Step 2: Build dependency graph
    logger.info("Step 2: Building dependency graph")
    graph_builder = GraphBuilder()
    dependency_graph = graph_builder.build_graph(all_ast_nodes)
    
    # Create AST index for quick lookup
    ast_index = {
        f"{node.file_path}:{node.name}:{node.start_line}": node
        for node in all_ast_nodes
    }
    
    logger.info(f"Dependency graph: {dependency_graph.number_of_nodes()} nodes, "
                f"{dependency_graph.number_of_edges()} edges")
    
    # Step 3: Initialize orchestrator
    logger.info("Step 3: Initializing translation orchestrator")
    llm_client = GeminiClient()
    validator = CodeValidator()
    orchestrator = TranslationOrchestrator(
        llm_client=llm_client,
        validator=validator
    )
    
    # Step 4: Translate repository
    logger.info("Step 4: Starting translation")
    try:
        results = await orchestrator.translate_repository(
            dependency_graph=dependency_graph,
            ast_index=ast_index,
            target_language="python"
        )
        
        # Step 5: Display results
        logger.info("Step 5: Translation complete")
        
        for result in results:
            status_symbol = "✓" if result.status == TranslationStatus.SUCCESS else "✗"
            logger.info(f"{status_symbol} {result.module_name}: {result.status.value}")
            
            if result.errors:
                logger.error(f"  Errors: {', '.join(result.errors)}")
            
            if result.warnings:
                logger.warning(f"  Warnings: {', '.join(result.warnings)}")
            
            if result.status == TranslationStatus.SUCCESS:
                logger.info(f"  Token usage: {result.token_usage}")
                logger.info(f"  Dependencies: {len(result.dependencies_used)}")
        
        # Step 6: Display statistics
        stats = orchestrator.get_translation_statistics(results)
        logger.info("\nTranslation Statistics:")
        logger.info(f"  Total modules: {stats['total_modules']}")
        logger.info(f"  Successful: {stats['successful']}")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Skipped (cached): {stats['skipped']}")
        logger.info(f"  Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"  Total tokens: {stats['total_tokens']}")
        logger.info(f"  Average tokens/module: {stats['average_tokens_per_module']:.0f}")
        
        # Step 7: Save translated code
        output_dir = Path("output/translated")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for result in results:
            if result.status == TranslationStatus.SUCCESS:
                # Extract module name from node_id
                module_name = result.module_name.split(":")[-2]  # Get name part
                output_file = output_dir / f"{module_name}.py"
                
                output_file.write_text(result.translated_code)
                logger.info(f"Saved: {output_file}")
        
    except ValueError as e:
        logger.error(f"Translation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
