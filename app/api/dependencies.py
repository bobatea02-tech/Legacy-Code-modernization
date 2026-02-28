"""FastAPI dependency injection providers.

This module provides dependency injection functions for service layer classes.
No business logic - pure dependency construction only.
"""

from typing import Optional
from functools import lru_cache

from app.ingestion.ingestor import RepositoryIngestor, IngestionConfig
from app.parsers.java_parser import JavaParser
from app.parsers.cobol_parser import CobolParser
from app.dependency_graph.graph_builder import GraphBuilder
from app.context_optimizer.optimizer import ContextOptimizer
from app.llm.gemini_client import GeminiClient
from app.translation.orchestrator import TranslationOrchestrator, TranslationStore
from app.validation import ValidationEngine
from app.audit import AuditEngine
from app.pipeline import PipelineService
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# Service Singletons (cached for performance)
# ============================================================================

@lru_cache
def get_ingestion_service() -> RepositoryIngestor:
    """Get repository ingestion service.
    
    Returns:
        RepositoryIngestor instance
    """
    config = IngestionConfig()
    return RepositoryIngestor(config=config)


@lru_cache
def get_graph_builder() -> GraphBuilder:
    """Get dependency graph builder service.
    
    Returns:
        GraphBuilder instance
    """
    return GraphBuilder()


@lru_cache
def get_context_optimizer() -> ContextOptimizer:
    """Get context optimizer service.
    
    Returns:
        ContextOptimizer instance
    """
    return ContextOptimizer()


@lru_cache
def get_llm_client() -> GeminiClient:
    """Get LLM client service.
    
    Returns:
        GeminiClient instance
    """
    return GeminiClient()


@lru_cache
def get_validation_engine() -> ValidationEngine:
    """Get validation engine service.
    
    Returns:
        ValidationEngine instance
    """
    return ValidationEngine()


@lru_cache
def get_audit_engine() -> AuditEngine:
    """Get audit engine service.
    
    Returns:
        AuditEngine instance
    """
    return AuditEngine()


@lru_cache
def get_pipeline_service() -> PipelineService:
    """Get centralized pipeline service.
    
    Returns:
        PipelineService instance
    """
    return PipelineService()


# ============================================================================
# Translation Service (with dependencies)
# ============================================================================

def get_translation_service() -> TranslationOrchestrator:
    """Get translation orchestrator service with all dependencies.
    
    Returns:
        TranslationOrchestrator instance with injected dependencies
    """
    llm_client = get_llm_client()
    context_optimizer = get_context_optimizer()
    translation_store = TranslationStore()
    
    return TranslationOrchestrator(
        llm_client=llm_client,
        context_optimizer=context_optimizer,
        translation_store=translation_store
    )


# ============================================================================
# Parser Factory
# ============================================================================

def get_parser(language: str):
    """Get parser for specified language.
    
    Args:
        language: Language identifier (java, cobol, c)
        
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


# ============================================================================
# In-Memory Storage (for demo/development)
# ============================================================================

class InMemoryStorage:
    """Simple in-memory storage for repository data.
    
    Note: In production, replace with proper database/cache.
    """
    
    def __init__(self):
        """Initialize storage."""
        self._repositories: dict = {}
        self._graphs: dict = {}
        self._translations: dict = {}
        self._validations: dict = {}
        self._documentation: dict = {}
        self._audits: dict = {}
        self._evaluations: dict = {}
    
    def store_repository(self, repo_id: str, data: dict) -> None:
        """Store repository data."""
        self._repositories[repo_id] = data
    
    def get_repository(self, repo_id: str) -> Optional[dict]:
        """Get repository data."""
        return self._repositories.get(repo_id)
    
    def store_graph(self, repo_id: str, graph_data: dict) -> None:
        """Store dependency graph."""
        self._graphs[repo_id] = graph_data
    
    def get_graph(self, repo_id: str) -> Optional[dict]:
        """Get dependency graph."""
        return self._graphs.get(repo_id)
    
    def store_translations(self, repo_id: str, translations: list) -> None:
        """Store translation results."""
        self._translations[repo_id] = translations
    
    def get_translations(self, repo_id: str) -> Optional[list]:
        """Get translation results."""
        return self._translations.get(repo_id)
    
    def store_validations(self, repo_id: str, validations: list) -> None:
        """Store validation results."""
        self._validations[repo_id] = validations
    
    def get_validations(self, repo_id: str) -> Optional[list]:
        """Get validation results."""
        return self._validations.get(repo_id)
    
    def store_documentation(self, repo_id: str, docs: dict) -> None:
        """Store documentation."""
        self._documentation[repo_id] = docs
    
    def get_documentation(self, repo_id: str) -> Optional[dict]:
        """Get documentation."""
        return self._documentation.get(repo_id)
    
    def store_audit(self, repo_id: str, audit: dict) -> None:
        """Store audit results."""
        self._audits[repo_id] = audit
    
    def get_audit(self, repo_id: str) -> Optional[dict]:
        """Get audit results."""
        return self._audits.get(repo_id)
    
    def store_evaluation(self, repo_id: str, evaluation: dict) -> None:
        """Store evaluation report."""
        self._evaluations[repo_id] = evaluation
    
    def get_evaluation(self, repo_id: str) -> Optional[dict]:
        """Get evaluation report."""
        return self._evaluations.get(repo_id)
    
    def has_repository(self, repo_id: str) -> bool:
        """Check if repository exists."""
        return repo_id in self._repositories


# Global storage instance (replace with proper DB in production)
_storage = InMemoryStorage()


def get_storage() -> InMemoryStorage:
    """Get storage instance.
    
    Returns:
        InMemoryStorage instance
    """
    return _storage
