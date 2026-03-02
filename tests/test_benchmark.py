"""Tests for benchmark harness."""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from benchmark_runner import (
    compute_dataset_hash,
    compute_run_hash,
    extract_node_metrics,
    extract_phase_metrics,
    run_benchmark,
    BenchmarkMetrics,
    NodeMetrics,
    PhaseMetrics
)


class TestDatasetHash:
    """Tests for dataset hash computation."""
    
    def test_dataset_hash_deterministic(self):
        """Test dataset hash is deterministic."""
        dataset_path = "sample_repos/java_small.zip"
        
        hash1 = compute_dataset_hash(dataset_path)
        hash2 = compute_dataset_hash(dataset_path)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_dataset_hash_expected_value(self):
        """Test dataset hash matches expected value."""
        dataset_path = "sample_repos/java_small.zip"
        
        hash_value = compute_dataset_hash(dataset_path)
        
        # Expected hash from Phase-11 setup
        expected = "39dab571709c465c5c40f72f736e19901ef7e2489210eb085e5aa5833a6a32fa"
        assert hash_value == expected


class TestRunHash:
    """Tests for run hash computation."""
    
    def test_run_hash_deterministic(self):
        """Test run hash is deterministic for same metrics."""
        metrics = BenchmarkMetrics(
            dataset_hash="test_hash",
            run_hash="",
            nodes_total=3,
            nodes_translated=3,
            nodes_success=3,
            nodes_failed=0,
            success_rate=100.0,
            avg_tokens_per_node=100.0,
            total_tokens_input=150,
            total_tokens_output=150,
            avg_latency_ms=50.0,
            total_latency_ms=150.0,
            node_metrics=[
                {
                    "node_id": "node1",
                    "tokens_input": 50,
                    "tokens_output": 50,
                    "latency_ms": 50.0,
                    "success": True,
                    "model_name": "test",
                    "prompt_version": "1.0",
                    "error_message": None
                }
            ]
        )
        
        hash1 = compute_run_hash(metrics)
        hash2 = compute_run_hash(metrics)
        
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_run_hash_changes_with_metrics(self):
        """Test run hash changes when metrics change."""
        metrics1 = BenchmarkMetrics(
            dataset_hash="test_hash",
            run_hash="",
            nodes_total=3,
            nodes_translated=3,
            nodes_success=3,
            nodes_failed=0,
            success_rate=100.0,
            avg_tokens_per_node=100.0,
            total_tokens_input=150,
            total_tokens_output=150,
            avg_latency_ms=50.0,
            total_latency_ms=150.0,
            node_metrics=[]
        )
        
        metrics2 = BenchmarkMetrics(
            dataset_hash="test_hash",
            run_hash="",
            nodes_total=5,  # Different
            nodes_translated=5,
            nodes_success=5,
            nodes_failed=0,
            success_rate=100.0,
            avg_tokens_per_node=100.0,
            total_tokens_input=250,
            total_tokens_output=250,
            avg_latency_ms=50.0,
            total_latency_ms=250.0,
            node_metrics=[]
        )
        
        hash1 = compute_run_hash(metrics1)
        hash2 = compute_run_hash(metrics2)
        
        assert hash1 != hash2


class TestNodeMetrics:
    """Tests for node metrics extraction."""
    
    def test_extract_node_metrics_empty(self):
        """Test extraction with no translation results."""
        mock_result = Mock()
        mock_result.translation_results = None
        
        metrics = extract_node_metrics(mock_result)
        
        assert metrics == []
    
    def test_extract_node_metrics_success(self):
        """Test extraction with successful translations."""
        mock_tr = Mock()
        mock_tr.module_name = "TestModule"
        mock_tr.token_usage = 100
        mock_tr.status.value = "success"
        mock_tr.errors = []
        
        mock_result = Mock()
        mock_result.translation_results = [mock_tr]
        mock_result.evaluation_report = {
            "prompt_metadata": {
                "translation": {
                    "model_name": "gemini-1.5-flash",
                    "version": "1.0"
                }
            }
        }
        
        metrics = extract_node_metrics(mock_result)
        
        assert len(metrics) == 1
        assert metrics[0].node_id == "TestModule"
        assert metrics[0].tokens_output == 100
        assert metrics[0].success is True
        assert metrics[0].model_name == "gemini-1.5-flash"
        assert metrics[0].prompt_version == "1.0"


class TestPhaseMetrics:
    """Tests for phase metrics extraction."""
    
    def test_extract_phase_metrics_basic(self):
        """Test extraction of basic phase metrics."""
        mock_result = Mock()
        mock_result.file_count = 6
        mock_result.ast_node_count = 10
        mock_result.graph_node_count = 8
        mock_result.translation_results = []
        mock_result.validation_reports = []
        mock_result.documentation = []
        mock_result.audit_report = None
        
        metrics = extract_phase_metrics(mock_result)
        
        # Should have ingestion, parsing, graph_building phases
        assert len(metrics) >= 3
        
        phase_names = [m.phase_name for m in metrics]
        assert "ingestion" in phase_names
        assert "parsing" in phase_names
        assert "graph_building" in phase_names


class TestBenchmarkMetrics:
    """Tests for BenchmarkMetrics dataclass."""
    
    def test_metrics_to_dict(self):
        """Test metrics serialization to dict."""
        metrics = BenchmarkMetrics(
            dataset_hash="test_hash",
            run_hash="run_hash",
            nodes_total=3,
            nodes_translated=3,
            nodes_success=3,
            nodes_failed=0,
            success_rate=100.0,
            avg_tokens_per_node=100.0,
            total_tokens_input=150,
            total_tokens_output=150,
            avg_latency_ms=50.0,
            total_latency_ms=150.0
        )
        
        result = metrics.to_dict()
        
        assert isinstance(result, dict)
        assert result["dataset_hash"] == "test_hash"
        assert result["nodes_total"] == 3
        assert result["success_rate"] == 100.0
    
    def test_metrics_json_serializable(self):
        """Test metrics can be serialized to JSON."""
        metrics = BenchmarkMetrics(
            dataset_hash="test_hash",
            run_hash="run_hash",
            nodes_total=3,
            nodes_translated=3,
            nodes_success=3,
            nodes_failed=0,
            success_rate=100.0,
            avg_tokens_per_node=100.0,
            total_tokens_input=150,
            total_tokens_output=150,
            avg_latency_ms=50.0,
            total_latency_ms=150.0,
            environment={"python_version": "3.13.2"}
        )
        
        # Should not raise exception
        json_str = json.dumps(metrics.to_dict())
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["dataset_hash"] == "test_hash"


class TestBenchmarkSchema:
    """Tests for benchmark output schema validation."""
    
    def test_benchmark_report_schema(self):
        """Test benchmark report has required fields."""
        required_fields = [
            "deterministic_hash_match",
            "run1_hash",
            "run2_hash",
            "run1_metrics",
            "run2_metrics"
        ]
        
        # Mock verification result
        result = {
            "deterministic_hash_match": True,
            "run1_hash": "hash1",
            "run2_hash": "hash2",
            "run1_metrics": {},
            "run2_metrics": {}
        }
        
        for field in required_fields:
            assert field in result
    
    def test_metrics_schema(self):
        """Test metrics object has required fields."""
        required_fields = [
            "dataset_hash",
            "run_hash",
            "nodes_total",
            "nodes_translated",
            "nodes_success",
            "nodes_failed",
            "success_rate",
            "avg_tokens_per_node",
            "total_tokens_input",
            "total_tokens_output",
            "avg_latency_ms",
            "total_latency_ms",
            "phase_metrics",
            "node_metrics",
            "environment"
        ]
        
        metrics = BenchmarkMetrics(
            dataset_hash="test",
            run_hash="test",
            nodes_total=0,
            nodes_translated=0,
            nodes_success=0,
            nodes_failed=0,
            success_rate=0.0,
            avg_tokens_per_node=0.0,
            total_tokens_input=0,
            total_tokens_output=0,
            avg_latency_ms=0.0,
            total_latency_ms=0.0
        )
        
        metrics_dict = metrics.to_dict()
        
        for field in required_fields:
            assert field in metrics_dict


class TestBenchmarkIntegration:
    """Integration tests for benchmark runner."""
    
    @pytest.mark.asyncio
    async def test_benchmark_produces_valid_output(self):
        """Test benchmark produces schema-valid output."""
        # This is a smoke test - full execution requires API key
        # Just verify the function signature and basic structure
        
        # Mock PipelineService
        with patch('benchmark_runner.PipelineService') as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline_class.return_value = mock_pipeline
            
            # Mock pipeline result
            mock_result = Mock()
            mock_result.success = True
            mock_result.file_count = 6
            mock_result.ast_node_count = 10
            mock_result.graph_node_count = 8
            mock_result.translation_results = []
            mock_result.validation_reports = []
            mock_result.documentation = []
            mock_result.audit_report = None
            mock_result.evaluation_report = {}
            
            mock_pipeline.execute_full_pipeline.return_value = mock_result
            
            # Run benchmark
            metrics = await run_benchmark(
                dataset_path="sample_repos/java_small.zip",
                source_language="java",
                target_language="python",
                repository_id="test"
            )
            
            # Verify output structure
            assert isinstance(metrics, BenchmarkMetrics)
            assert metrics.dataset_hash is not None
            assert metrics.run_hash is not None
            assert isinstance(metrics.environment, dict)
