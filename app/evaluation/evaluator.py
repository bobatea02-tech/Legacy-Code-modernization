"""Evaluation module for quantitative pipeline effectiveness measurement.

This module provides deterministic evaluation of the optimization + translation pipeline,
measuring token efficiency, runtime performance, and quality signals.

Architecture:
- Pure service layer (no FastAPI, CLI, or file I/O)
- Callable from PipelineService
- Deterministic outputs for testing
- JSON-serializable reports
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import time

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationInput:
    """Input data for pipeline evaluation.
    
    Attributes:
        repo_id: Repository identifier
        naive_token_count: Token count without optimization
        optimized_token_count: Token count after optimization
        start_time: Pipeline start timestamp (seconds since epoch)
        end_time: Pipeline end timestamp (seconds since epoch)
        files_processed: Number of files successfully processed
        errors_encountered: Number of errors during pipeline
        phase_metadata: Dictionary of phase-specific metrics
    """
    repo_id: str
    naive_token_count: int
    optimized_token_count: int
    start_time: float
    end_time: float
    files_processed: int
    errors_encountered: int = 0
    phase_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenMetrics:
    """Token efficiency metrics.
    
    Attributes:
        naive_token_count: Tokens without optimization
        optimized_token_count: Tokens after optimization
        token_reduction: Absolute token reduction
        reduction_percentage: Percentage reduction (0-100)
        tokens_per_file: Average tokens per file
        efficiency_score: Weighted efficiency score (0-100)
    """
    naive_token_count: int
    optimized_token_count: int
    token_reduction: int
    reduction_percentage: float
    tokens_per_file: float
    efficiency_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class RuntimeMetrics:
    """Runtime performance metrics.
    
    Attributes:
        total_runtime_seconds: Total pipeline runtime
        runtime_per_file: Average runtime per file
        runtime_per_phase: Dictionary of phase name to runtime
        timeout_detected: Whether any timeouts occurred
    """
    total_runtime_seconds: float
    runtime_per_file: float
    runtime_per_phase: Dict[str, float]
    timeout_detected: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class QualityMetrics:
    """Quality signal metrics.
    
    Attributes:
        validation_pass_rate: Percentage of validations passed (0-100)
        dependency_resolution_rate: Percentage of dependencies resolved (0-100)
        syntax_error_rate: Percentage of syntax errors (0-100)
        total_validations: Total number of validations performed
        passed_validations: Number of validations passed
    """
    validation_pass_rate: float
    dependency_resolution_rate: float
    syntax_error_rate: float
    total_validations: int
    passed_validations: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class EvaluationReport:
    """Complete evaluation report for pipeline execution.
    
    Attributes:
        repo_id: Repository identifier
        token_metrics: Token efficiency metrics
        runtime_metrics: Runtime performance metrics
        quality_metrics: Quality signal metrics
        summary_text: Human-readable summary
        timestamp: Report generation timestamp (ISO format)
        prompt_versions: Dictionary of prompt_name -> version used (deprecated, use prompt_metadata)
        prompt_metadata: Dictionary of prompt_name -> {version, checksum, model_name}
    """
    repo_id: str
    token_metrics: TokenMetrics
    runtime_metrics: RuntimeMetrics
    quality_metrics: QualityMetrics
    summary_text: str
    timestamp: str
    prompt_versions: Dict[str, str] = field(default_factory=dict)
    prompt_metadata: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the report
        """
        return {
            "repo_id": self.repo_id,
            "token_metrics": self.token_metrics.to_dict(),
            "runtime_metrics": self.runtime_metrics.to_dict(),
            "quality_metrics": self.quality_metrics.to_dict(),
            "summary_text": self.summary_text,
            "timestamp": self.timestamp,
            "prompt_versions": self.prompt_versions,
            "prompt_metadata": self.prompt_metadata
        }


class PipelineEvaluator:
    """Evaluator for quantitative pipeline effectiveness measurement.
    
    This class provides deterministic evaluation of the optimization + translation
    pipeline, computing token efficiency, runtime performance, and quality metrics.
    """
    
    def __init__(self) -> None:
        """Initialize pipeline evaluator."""
        logger.info("PipelineEvaluator initialized")
    
    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationReport:
        """Evaluate pipeline execution and generate comprehensive report.
        
        Args:
            evaluation_input: Input data containing pipeline metrics
            
        Returns:
            EvaluationReport with all computed metrics
        """
        logger.info(
            f"Starting evaluation for repository: {evaluation_input.repo_id}",
            extra={"repo_id": evaluation_input.repo_id}
        )
        
        # Compute token efficiency metrics
        token_metrics = self._compute_token_metrics(evaluation_input)
        
        # Compute runtime metrics
        runtime_metrics = self._compute_runtime_metrics(evaluation_input)
        
        # Compute quality metrics
        quality_metrics = self._compute_quality_metrics(evaluation_input)
        
        # Generate summary text
        summary_text = self._generate_summary(
            evaluation_input,
            token_metrics,
            runtime_metrics,
            quality_metrics
        )
        
        # Extract prompt versions from metadata (legacy format)
        prompt_versions = evaluation_input.phase_metadata.get("prompt_versions", {})
        
        # Extract prompt metadata (new format with checksum and model_name)
        prompt_metadata = evaluation_input.phase_metadata.get("prompt_metadata", {})
        
        # Create report
        report = EvaluationReport(
            repo_id=evaluation_input.repo_id,
            token_metrics=token_metrics,
            runtime_metrics=runtime_metrics,
            quality_metrics=quality_metrics,
            summary_text=summary_text,
            timestamp=datetime.now(timezone.utc).isoformat(),
            prompt_versions=prompt_versions,
            prompt_metadata=prompt_metadata
        )
        
        logger.info(
            f"Evaluation complete for repository: {evaluation_input.repo_id}",
            extra={
                "repo_id": evaluation_input.repo_id,
                "efficiency_score": token_metrics.efficiency_score,
                "total_runtime": runtime_metrics.total_runtime_seconds,
                "validation_pass_rate": quality_metrics.validation_pass_rate,
                "prompt_metadata": prompt_metadata
            }
        )
        
        return report
    
    def _compute_token_metrics(self, eval_input: EvaluationInput) -> TokenMetrics:
        """Compute token efficiency metrics.
        
        Args:
            eval_input: Evaluation input data
            
        Returns:
            TokenMetrics with computed values
        """
        # Calculate token reduction
        token_reduction = eval_input.naive_token_count - eval_input.optimized_token_count
        
        # Calculate reduction percentage
        if eval_input.naive_token_count > 0:
            reduction_percentage = (token_reduction / eval_input.naive_token_count) * 100
        else:
            reduction_percentage = 0.0
        
        # Calculate tokens per file
        if eval_input.files_processed > 0:
            tokens_per_file = eval_input.optimized_token_count / eval_input.files_processed
        else:
            tokens_per_file = 0.0
        
        # Calculate efficiency score (0-100 weighted metric)
        efficiency_score = self._calculate_efficiency_score(
            reduction_percentage,
            eval_input.files_processed,
            eval_input.errors_encountered
        )
        
        logger.debug(
            f"Token metrics computed: reduction={token_reduction}, "
            f"percentage={reduction_percentage:.2f}%, score={efficiency_score:.2f}",
            extra={"repo_id": eval_input.repo_id}
        )
        
        return TokenMetrics(
            naive_token_count=eval_input.naive_token_count,
            optimized_token_count=eval_input.optimized_token_count,
            token_reduction=token_reduction,
            reduction_percentage=round(reduction_percentage, 2),
            tokens_per_file=round(tokens_per_file, 2),
            efficiency_score=round(efficiency_score, 2)
        )
    
    def _compute_runtime_metrics(self, eval_input: EvaluationInput) -> RuntimeMetrics:
        """Compute runtime performance metrics.
        
        Args:
            eval_input: Evaluation input data
            
        Returns:
            RuntimeMetrics with computed values
        """
        # Calculate total runtime
        total_runtime = eval_input.end_time - eval_input.start_time
        
        # Calculate runtime per file
        if eval_input.files_processed > 0:
            runtime_per_file = total_runtime / eval_input.files_processed
        else:
            runtime_per_file = 0.0
        
        # Extract runtime per phase from metadata
        runtime_per_phase = eval_input.phase_metadata.get("phase_runtimes", {})
        
        # Detect timeouts (heuristic: any phase taking > 300 seconds)
        timeout_detected = any(
            runtime > 300.0 for runtime in runtime_per_phase.values()
        )
        
        logger.debug(
            f"Runtime metrics computed: total={total_runtime:.2f}s, "
            f"per_file={runtime_per_file:.2f}s, timeout={timeout_detected}",
            extra={"repo_id": eval_input.repo_id}
        )
        
        return RuntimeMetrics(
            total_runtime_seconds=round(total_runtime, 2),
            runtime_per_file=round(runtime_per_file, 2),
            runtime_per_phase=runtime_per_phase,
            timeout_detected=timeout_detected
        )
    
    def _compute_quality_metrics(self, eval_input: EvaluationInput) -> QualityMetrics:
        """Compute quality signal metrics.
        
        Args:
            eval_input: Evaluation input data
            
        Returns:
            QualityMetrics with computed values
        """
        # Extract quality data from phase metadata
        validation_data = eval_input.phase_metadata.get("validation", {})
        
        total_validations = validation_data.get("total", 0)
        passed_validations = validation_data.get("passed", 0)
        syntax_errors = validation_data.get("syntax_errors", 0)
        dependency_issues = validation_data.get("dependency_issues", 0)
        
        # Calculate validation pass rate
        if total_validations > 0:
            validation_pass_rate = (passed_validations / total_validations) * 100
        else:
            validation_pass_rate = 0.0
        
        # Calculate dependency resolution rate
        if total_validations > 0:
            resolved = total_validations - dependency_issues
            dependency_resolution_rate = (resolved / total_validations) * 100
        else:
            dependency_resolution_rate = 0.0
        
        # Calculate syntax error rate
        if total_validations > 0:
            syntax_error_rate = (syntax_errors / total_validations) * 100
        else:
            syntax_error_rate = 0.0
        
        logger.debug(
            f"Quality metrics computed: pass_rate={validation_pass_rate:.2f}%, "
            f"dependency_rate={dependency_resolution_rate:.2f}%, "
            f"syntax_error_rate={syntax_error_rate:.2f}%",
            extra={"repo_id": eval_input.repo_id}
        )
        
        return QualityMetrics(
            validation_pass_rate=round(validation_pass_rate, 2),
            dependency_resolution_rate=round(dependency_resolution_rate, 2),
            syntax_error_rate=round(syntax_error_rate, 2),
            total_validations=total_validations,
            passed_validations=passed_validations
        )
    
    def _calculate_efficiency_score(
        self,
        reduction_percentage: float,
        files_processed: int,
        errors_encountered: int
    ) -> float:
        """Calculate weighted efficiency score (0-100).
        
        Scoring formula:
        - Token reduction: 60% weight
        - Success rate: 30% weight
        - Throughput bonus: 10% weight
        
        Args:
            reduction_percentage: Token reduction percentage
            files_processed: Number of files processed
            errors_encountered: Number of errors
            
        Returns:
            Efficiency score (0-100)
        """
        # Token reduction component (60% weight, capped at 100%)
        token_component = min(reduction_percentage, 100.0) * 0.6
        
        # Success rate component (30% weight)
        total_attempts = files_processed + errors_encountered
        if total_attempts > 0:
            success_rate = (files_processed / total_attempts) * 100
        else:
            success_rate = 0.0
        success_component = success_rate * 0.3
        
        # Throughput bonus (10% weight, scaled by file count)
        # Bonus increases with more files processed (up to 100 files = max bonus)
        throughput_bonus = min(files_processed / 100.0, 1.0) * 100 * 0.1
        
        # Calculate total score
        efficiency_score = token_component + success_component + throughput_bonus
        
        return min(efficiency_score, 100.0)
    
    def _generate_summary(
        self,
        eval_input: EvaluationInput,
        token_metrics: TokenMetrics,
        runtime_metrics: RuntimeMetrics,
        quality_metrics: QualityMetrics
    ) -> str:
        """Generate human-readable summary text.
        
        Args:
            eval_input: Evaluation input data
            token_metrics: Computed token metrics
            runtime_metrics: Computed runtime metrics
            quality_metrics: Computed quality metrics
            
        Returns:
            Summary text string
        """
        summary_lines = [
            f"Pipeline Evaluation Summary for {eval_input.repo_id}",
            "",
            f"Token Efficiency:",
            f"  - Reduced tokens by {token_metrics.token_reduction:,} "
            f"({token_metrics.reduction_percentage}%)",
            f"  - Average {token_metrics.tokens_per_file:.0f} tokens per file",
            f"  - Efficiency score: {token_metrics.efficiency_score}/100",
            "",
            f"Runtime Performance:",
            f"  - Total runtime: {runtime_metrics.total_runtime_seconds:.2f}s",
            f"  - Average {runtime_metrics.runtime_per_file:.2f}s per file",
            f"  - Timeout detected: {'Yes' if runtime_metrics.timeout_detected else 'No'}",
            "",
            f"Quality Metrics:",
            f"  - Validation pass rate: {quality_metrics.validation_pass_rate}%",
            f"  - Dependency resolution: {quality_metrics.dependency_resolution_rate}%",
            f"  - Syntax error rate: {quality_metrics.syntax_error_rate}%",
            "",
            f"Files processed: {eval_input.files_processed}",
            f"Errors encountered: {eval_input.errors_encountered}"
        ]
        
        return "\n".join(summary_lines)
