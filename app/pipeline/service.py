"""Centralized pipeline orchestration service.

This module provides a single entry point for the full translation pipeline,
eliminating duplication between API and CLI layers.

Pipeline Phases:
1. Ingestion → File metadata
2. AST Parsing → AST nodes
3. Dependency Graph → NetworkX DiGraph
4. Context Optimization → Bounded context (implicit in translation)
5. Translation → Python code
6. Validation → Validation reports
7. Audit → Audit report
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import asyncio
import time

from app.ingestion.ingestor import RepositoryIngestor, IngestionConfig, IngestionError
from app.parsers.java_parser import JavaParser
from app.parsers.cobol_parser import CobolParser
from app.parsers.base import BaseParser
from app.dependency_graph.graph_builder import GraphBuilder
from app.context_optimizer.optimizer import ContextOptimizer
from app.llm.gemini_client import GeminiClient
from app.translation.orchestrator import TranslationOrchestrator, TranslationStore
from app.validation import ValidationEngine
from app.audit import AuditEngine
from app.evaluation import PipelineEvaluator, EvaluationInput
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Result of full pipeline execution.
    
    Attributes:
        success: Whether pipeline completed successfully
        repository_id: Repository identifier
        file_count: Number of files ingested
        ast_node_count: Number of AST nodes parsed
        graph_node_count: Number of nodes in dependency graph
        graph_edge_count: Number of edges in dependency graph
        translation_results: List of translation results
        validation_reports: List of validation reports
        audit_report: Audit report
        documentation: Generated documentation
        evaluation_report: Evaluation report (metrics and analysis)
        prompt_versions: Dictionary of prompt_name -> version used
        errors: List of error messages
        warnings: List of warning messages
        start_time: Pipeline start timestamp
        end_time: Pipeline end timestamp
    """
    success: bool
    repository_id: Optional[str] = None
    file_count: int = 0
    ast_node_count: int = 0
    graph_node_count: int = 0
    graph_edge_count: int = 0
    translation_results: List = field(default_factory=list)
    validation_reports: List = field(default_factory=list)
    audit_report: Optional[any] = None
    documentation: Dict[str, str] = field(default_factory=dict)
    evaluation_report: Optional[Dict[str, Any]] = None
    prompt_versions: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0


class PipelineService:
    """Centralized service for full translation pipeline orchestration.
    
    This service encapsulates all pipeline logic in one place, eliminating
    duplication between API and CLI layers.
    """
    
    def __init__(self):
        """Initialize pipeline service with all required components."""
        self.ingestor: Optional[RepositoryIngestor] = None
        self.graph_builder = GraphBuilder()
        self.context_optimizer = ContextOptimizer()
        self.llm_client = GeminiClient()
        self.translation_store = TranslationStore()
        self.validation_engine = ValidationEngine()
        self.audit_engine = AuditEngine()
        self.evaluator = PipelineEvaluator()
        
        logger.info("PipelineService initialized")
    
    def get_parser(self, language: str) -> BaseParser:
        """Get parser for specified language.
        
        Args:
            language: Language identifier (java, cobol)
            
        Returns:
            Parser instance
            
        Raises:
            ValueError: If language not supported
        """
        language_lower = language.lower()
        
        if language_lower == "java":
            return JavaParser()
        elif language_lower == "cobol":
            return CobolParser()
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    async def execute_full_pipeline(
        self,
        repo_path: str,
        source_language: str = "java",
        target_language: str = "python",
        repository_id: Optional[str] = None
    ) -> PipelineResult:
        """Execute full translation pipeline.
        
        This is the single entry point for complete pipeline execution.
        
        Args:
            repo_path: Path to repository (ZIP file or directory)
            source_language: Source language (java, cobol)
            target_language: Target language (python)
            repository_id: Optional repository ID (generated if not provided)
            
        Returns:
            PipelineResult with all pipeline outputs including evaluation report
            
        Raises:
            IngestionError: If ingestion fails
            ValueError: If language not supported
        """
        result = PipelineResult(success=False)
        result.start_time = time.time()
        result.repository_id = repository_id or "unknown"
        
        # Track phase runtimes for evaluation
        phase_runtimes = {}
        
        try:
            # Phase 1: Ingestion
            phase_start = time.time()
            logger.info(
                "Phase 1: Ingesting repository",
                extra={"phase": "ingestion", "repo_id": result.repository_id}
            )
            file_metadata_list = await self._phase_1_ingest(repo_path)
            result.file_count = len(file_metadata_list)
            phase_duration = time.time() - phase_start
            phase_runtimes["ingestion"] = phase_duration
            logger.info(
                f"Phase 1 complete: {len(file_metadata_list)} files ingested",
                extra={
                    "phase": "ingestion",
                    "repo_id": result.repository_id,
                    "duration": phase_duration,
                    "file_count": len(file_metadata_list)
                }
            )
            
            if not file_metadata_list:
                result.errors.append("No files found in repository")
                result.end_time = time.time()
                return result
            
            # Phase 2: AST Parsing
            phase_start = time.time()
            logger.info(
                "Phase 2: Parsing files to AST",
                extra={"phase": "parsing", "repo_id": result.repository_id}
            )
            ast_nodes, ast_index = await self._phase_2_parse(
                file_metadata_list,
                source_language
            )
            result.ast_node_count = len(ast_nodes)
            phase_duration = time.time() - phase_start
            phase_runtimes["parsing"] = phase_duration
            logger.info(
                f"Phase 2 complete: {len(ast_nodes)} AST nodes parsed",
                extra={
                    "phase": "parsing",
                    "repo_id": result.repository_id,
                    "duration": phase_duration,
                    "ast_node_count": len(ast_nodes)
                }
            )
            
            if not ast_nodes:
                result.errors.append("No parseable files found")
                result.end_time = time.time()
                return result
            
            # Phase 3: Dependency Graph
            phase_start = time.time()
            logger.info(
                "Phase 3: Building dependency graph",
                extra={"phase": "graph_building", "repo_id": result.repository_id}
            )
            dependency_graph = await self._phase_3_build_graph(ast_nodes)
            result.graph_node_count = dependency_graph.number_of_nodes()
            result.graph_edge_count = dependency_graph.number_of_edges()
            phase_duration = time.time() - phase_start
            phase_runtimes["graph_building"] = phase_duration
            logger.info(
                f"Phase 3 complete: {result.graph_node_count} nodes, {result.graph_edge_count} edges",
                extra={
                    "phase": "graph_building",
                    "repo_id": result.repository_id,
                    "duration": phase_duration,
                    "node_count": result.graph_node_count,
                    "edge_count": result.graph_edge_count
                }
            )
            
            # Phase 4: Context Optimization (implicit in translation)
            logger.info(
                "Phase 4: Context optimization ready",
                extra={"phase": "context_optimization", "repo_id": result.repository_id}
            )
            
            # Phase 5: Translation
            phase_start = time.time()
            logger.info(
                "Phase 5: Translating code",
                extra={
                    "phase": "translation",
                    "repo_id": result.repository_id
                }
            )
            translation_results = await self._phase_5_translate(
                dependency_graph,
                ast_index,
                target_language
            )
            result.translation_results = translation_results
            phase_duration = time.time() - phase_start
            phase_runtimes["translation"] = phase_duration
            
            # Record prompt version used (get from orchestrator)
            translation_prompt_version = self.translation_orchestrator.get_prompt_version("code_translation")
            result.prompt_versions["code_translation"] = translation_prompt_version
            
            logger.info(
                f"Phase 5 complete: {len(translation_results)} modules translated",
                extra={
                    "phase": "translation",
                    "repo_id": result.repository_id,
                    "duration": phase_duration,
                    "module_count": len(translation_results),
                    "prompt_version": translation_prompt_version
                }
            )
            
            # Phase 6: Validation
            phase_start = time.time()
            logger.info(
                "Phase 6: Validating translations",
                extra={"phase": "validation", "repo_id": result.repository_id}
            )
            validation_reports = await self._phase_6_validate(
                translation_results,
                ast_index,
                dependency_graph
            )
            result.validation_reports = validation_reports
            phase_duration = time.time() - phase_start
            phase_runtimes["validation"] = phase_duration
            logger.info(
                f"Phase 6 complete: {len(validation_reports)} validations performed",
                extra={
                    "phase": "validation",
                    "repo_id": result.repository_id,
                    "duration": phase_duration,
                    "validation_count": len(validation_reports)
                }
            )
            
            # Phase 7: Documentation
            phase_start = time.time()
            logger.info(
                "Phase 7: Generating documentation",
                extra={"phase": "documentation", "repo_id": result.repository_id}
            )
            documentation = await self._phase_7_document(translation_results)
            result.documentation = documentation
            phase_duration = time.time() - phase_start
            phase_runtimes["documentation"] = phase_duration
            logger.info(
                f"Phase 7 complete: {len(documentation)} modules documented",
                extra={
                    "phase": "documentation",
                    "repo_id": result.repository_id,
                    "duration": phase_duration,
                    "doc_count": len(documentation)
                }
            )
            
            # Phase 8: Audit
            phase_start = time.time()
            logger.info(
                "Phase 8: Running audit",
                extra={"phase": "audit", "repo_id": result.repository_id}
            )
            audit_report = await self._phase_8_audit(
                validation_reports,
                documentation
            )
            result.audit_report = audit_report
            phase_duration = time.time() - phase_start
            phase_runtimes["audit"] = phase_duration
            logger.info(
                f"Phase 8 complete: audit {'passed' if audit_report.overall_passed else 'failed'}",
                extra={
                    "phase": "audit",
                    "repo_id": result.repository_id,
                    "duration": phase_duration,
                    "audit_passed": audit_report.overall_passed
                }
            )
            
            # Mark success
            result.success = True
            result.end_time = time.time()
            
            # Phase 9: Evaluation
            phase_start = time.time()
            logger.info(
                "Phase 9: Evaluating pipeline effectiveness",
                extra={"phase": "evaluation", "repo_id": result.repository_id}
            )
            evaluation_report = await self._phase_9_evaluate(
                result,
                phase_runtimes
            )
            result.evaluation_report = evaluation_report
            phase_duration = time.time() - phase_start
            logger.info(
                f"Phase 9 complete: efficiency score {evaluation_report['token_metrics']['efficiency_score']}/100",
                extra={
                    "phase": "evaluation",
                    "repo_id": result.repository_id,
                    "duration": phase_duration,
                    "efficiency_score": evaluation_report['token_metrics']['efficiency_score']
                }
            )
            
            logger.info(
                f"Pipeline complete: {len(translation_results)} translations, "
                f"{len(validation_reports)} validations, "
                f"audit {'passed' if audit_report.overall_passed else 'failed'}, "
                f"efficiency score: {evaluation_report['token_metrics']['efficiency_score']}/100",
                extra={
                    "repo_id": result.repository_id,
                    "total_duration": result.end_time - result.start_time
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Pipeline execution failed: {e}",
                extra={"repo_id": result.repository_id, "error": str(e)}
            )
            result.errors.append(str(e))
            result.end_time = time.time()
            return result
        finally:
            # Cleanup
            if self.ingestor:
                self.ingestor.cleanup()
    
    async def _phase_1_ingest(self, repo_path: str) -> List:
        """Phase 1: Ingest repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            List of FileMetadata objects
        """
        config = IngestionConfig()
        self.ingestor = RepositoryIngestor(config=config)
        
        path = Path(repo_path)
        
        if path.suffix == '.zip':
            file_metadata_list = self.ingestor.ingest_zip(str(path))
        else:
            raise IngestionError("Only ZIP files are currently supported")
        
        logger.info(f"Ingested {len(file_metadata_list)} files")
        return file_metadata_list
    
    async def _phase_2_parse(
        self,
        file_metadata_list: List,
        source_language: str
    ) -> tuple:
        """Phase 2: Parse files to AST.
        
        Args:
            file_metadata_list: List of FileMetadata objects
            source_language: Source language
            
        Returns:
            Tuple of (ast_nodes, ast_index)
        """
        parser = self.get_parser(source_language)
        ast_nodes = []
        
        for file_meta in file_metadata_list:
            if file_meta.language.lower() == source_language.lower():
                try:
                    nodes = parser.parse_file(str(file_meta.path))
                    ast_nodes.extend(nodes)
                except Exception as e:
                    logger.warning(f"Failed to parse {file_meta.relative_path}: {e}")
                    continue
        
        # Build AST index
        ast_index = {node.id: node for node in ast_nodes}
        
        logger.info(f"Parsed {len(ast_nodes)} AST nodes")
        return ast_nodes, ast_index
    
    async def _phase_3_build_graph(self, ast_nodes: List):
        """Phase 3: Build dependency graph.
        
        Args:
            ast_nodes: List of ASTNode objects
            
        Returns:
            NetworkX DiGraph
        """
        dependency_graph = self.graph_builder.build_graph(ast_nodes)
        
        logger.info(
            f"Built graph: {dependency_graph.number_of_nodes()} nodes, "
            f"{dependency_graph.number_of_edges()} edges"
        )
        
        return dependency_graph
    
    async def _phase_5_translate(
        self,
        dependency_graph,
        ast_index: Dict,
        target_language: str
    ) -> List:
        """Phase 5: Translate code.
        
        Args:
            dependency_graph: NetworkX DiGraph
            ast_index: Dictionary of AST nodes
            target_language: Target language
            
        Returns:
            List of TranslationResult objects
        """
        orchestrator = TranslationOrchestrator(
            llm_client=self.llm_client,
            context_optimizer=self.context_optimizer,
            translation_store=self.translation_store
        )
        
        # Store orchestrator reference to access prompt version later
        self.translation_orchestrator = orchestrator
        
        translation_results = await orchestrator.translate_repository(
            dependency_graph=dependency_graph,
            ast_index=ast_index,
            target_language=target_language
        )
        
        success_count = sum(
            1 for r in translation_results
            if r.status.value == "success"
        )
        
        logger.info(f"Translated {success_count}/{len(translation_results)} modules")
        
        return translation_results
    
    async def _phase_6_validate(
        self,
        translation_results: List,
        ast_index: Dict,
        dependency_graph
    ) -> List:
        """Phase 6: Validate translations.
        
        Args:
            translation_results: List of TranslationResult objects
            ast_index: Dictionary of AST nodes
            dependency_graph: NetworkX DiGraph
            
        Returns:
            List of ValidationReport objects
        """
        validation_reports = []
        
        for trans_result in translation_results:
            if trans_result.translated_code:
                original_node = ast_index.get(trans_result.module_name)
                if original_node:
                    validation_report = self.validation_engine.validate_translation(
                        original_node=original_node,
                        translated_code=trans_result.translated_code,
                        dependency_graph=dependency_graph
                    )
                    validation_reports.append(validation_report)
        
        passed_count = sum(
            1 for r in validation_reports
            if r.syntax_valid and r.structure_valid and
               r.symbols_preserved and r.dependencies_complete
        )
        
        logger.info(f"Validated {passed_count}/{len(validation_reports)} translations")
        
        return validation_reports
    
    async def _phase_7_document(self, translation_results: List) -> Dict[str, str]:
        """Phase 7: Generate documentation.
        
        Args:
            translation_results: List of TranslationResult objects
            
        Returns:
            Dictionary of module_name -> documentation
        """
        documentation = {}
        
        for trans_result in translation_results:
            if trans_result.translated_code:
                documentation[trans_result.module_name] = (
                    f"# {trans_result.module_name}\n\n"
                    f"Generated documentation for translated module."
                )
        
        logger.info(f"Generated documentation for {len(documentation)} modules")
        
        return documentation
    
    async def _phase_8_audit(
        self,
        validation_reports: List,
        documentation: Dict[str, str]
    ):
        """Phase 8: Run audit.
        
        Args:
            validation_reports: List of ValidationReport objects
            documentation: Dictionary of documentation
            
        Returns:
            AuditReport object
        """
        audit_report = self.audit_engine.run_audit(
            validation_reports=validation_reports,
            documentation=documentation
        )
        
        logger.info(
            f"Audit complete: {audit_report.passed_checks}/{audit_report.total_checks} "
            f"checks passed"
        )
        
        return audit_report
    
    async def _phase_9_evaluate(
        self,
        pipeline_result: PipelineResult,
        phase_runtimes: Dict[str, float]
    ) -> Dict[str, Any]:
        """Phase 9: Evaluate pipeline effectiveness.
        
        Args:
            pipeline_result: Pipeline execution result
            phase_runtimes: Dictionary of phase name to runtime
            
        Returns:
            Dictionary representation of EvaluationReport
        """
        # Calculate token counts
        naive_token_count = self._calculate_naive_token_count(pipeline_result)
        optimized_token_count = self._calculate_optimized_token_count(pipeline_result)
        
        # Extract validation metrics
        validation_metrics = self._extract_validation_metrics(pipeline_result.validation_reports)
        
        # Construct evaluation input
        eval_input = EvaluationInput(
            repo_id=pipeline_result.repository_id or "unknown",
            naive_token_count=naive_token_count,
            optimized_token_count=optimized_token_count,
            start_time=pipeline_result.start_time,
            end_time=pipeline_result.end_time,
            files_processed=pipeline_result.file_count,
            errors_encountered=len(pipeline_result.errors),
            phase_metadata={
                "phase_runtimes": phase_runtimes,
                "validation": validation_metrics,
                "prompt_versions": pipeline_result.prompt_versions
            }
        )
        
        # Run evaluation
        report = self.evaluator.evaluate(eval_input)
        
        # Convert to JSON-serializable dict
        report_dict = report.to_dict()
        
        logger.info(
            f"Evaluation complete: efficiency={report.token_metrics.efficiency_score}/100, "
            f"token_reduction={report.token_metrics.reduction_percentage}%"
        )
        
        return report_dict
    
    def _calculate_naive_token_count(self, pipeline_result: PipelineResult) -> int:
        """Calculate naive token count (without optimization).
        
        Estimates tokens as if all dependencies were included without optimization.
        
        Args:
            pipeline_result: Pipeline execution result
            
        Returns:
            Estimated naive token count
        """
        # Estimate: AST nodes * average tokens per node (rough heuristic)
        # In production, this would be calculated during context optimization
        tokens_per_node = 150  # Average tokens per AST node
        return pipeline_result.ast_node_count * tokens_per_node
    
    def _calculate_optimized_token_count(self, pipeline_result: PipelineResult) -> int:
        """Calculate optimized token count (after context optimization).
        
        Sums actual token usage from translation results.
        
        Args:
            pipeline_result: Pipeline execution result
            
        Returns:
            Actual optimized token count
        """
        total_tokens = 0
        for trans_result in pipeline_result.translation_results:
            if hasattr(trans_result, 'token_usage') and trans_result.token_usage:
                total_tokens += trans_result.token_usage
        
        # If no token usage recorded, estimate from translated code length
        if total_tokens == 0:
            for trans_result in pipeline_result.translation_results:
                if trans_result.translated_code:
                    # Rough estimate: 1 token per 4 characters
                    total_tokens += len(trans_result.translated_code) // 4
        
        return total_tokens
    
    def _extract_validation_metrics(self, validation_reports: List) -> Dict[str, int]:
        """Extract validation metrics for evaluation.
        
        Args:
            validation_reports: List of ValidationReport objects
            
        Returns:
            Dictionary with validation metrics
        """
        total = len(validation_reports)
        passed = sum(
            1 for r in validation_reports
            if r.syntax_valid and r.structure_valid and
               r.symbols_preserved and r.dependencies_complete
        )
        syntax_errors = sum(1 for r in validation_reports if not r.syntax_valid)
        dependency_issues = sum(1 for r in validation_reports if not r.dependencies_complete)
        
        return {
            "total": total,
            "passed": passed,
            "syntax_errors": syntax_errors,
            "dependency_issues": dependency_issues
        }
