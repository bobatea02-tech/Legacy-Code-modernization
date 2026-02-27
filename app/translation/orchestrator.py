"""Translation orchestrator for dependency-aware code translation.

This module coordinates the translation of legacy code into Python using
dependency graph analysis, context optimization, and LLM interface.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import networkx as nx

from app.context_optimizer.optimizer import ContextOptimizer
from app.llm.client import LLMClient
from app.validation.validator import CodeValidator, ValidationLevel
from app.parsers.base import ASTNode
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TranslationStatus(Enum):
    """Translation status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


@dataclass
class TranslationResult:
    """Result of a single module/function translation."""
    module_name: str
    status: TranslationStatus
    translated_code: str = ""
    dependencies_used: List[str] = field(default_factory=list)
    token_usage: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    source_hash: Optional[str] = None


class TranslationStore:
    """In-memory cache for translated code."""
    
    def __init__(self):
        """Initialize translation store."""
        self._cache: Dict[str, TranslationResult] = {}
        self._hash_index: Dict[str, str] = {}  # source_hash -> module_name
    
    def get(self, module_name: str) -> Optional[TranslationResult]:
        """Get cached translation result.
        
        Args:
            module_name: Module identifier
            
        Returns:
            TranslationResult if cached, None otherwise
        """
        return self._cache.get(module_name)
    
    def get_by_hash(self, source_hash: str) -> Optional[TranslationResult]:
        """Get cached translation by source hash.
        
        Args:
            source_hash: Hash of source code
            
        Returns:
            TranslationResult if cached, None otherwise
        """
        module_name = self._hash_index.get(source_hash)
        if module_name:
            return self._cache.get(module_name)
        return None
    
    def store(self, result: TranslationResult) -> None:
        """Store translation result.
        
        Args:
            result: TranslationResult to cache
        """
        self._cache[result.module_name] = result
        if result.source_hash:
            self._hash_index[result.source_hash] = result.module_name
    
    def has(self, module_name: str) -> bool:
        """Check if module is cached.
        
        Args:
            module_name: Module identifier
            
        Returns:
            True if cached, False otherwise
        """
        return module_name in self._cache
    
    def clear(self) -> None:
        """Clear all cached translations."""
        self._cache.clear()
        self._hash_index.clear()


class TranslationOrchestrator:
    """Orchestrates dependency-aware translation of legacy code to Python."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        validator: Optional[CodeValidator] = None,
        context_optimizer: Optional[ContextOptimizer] = None,
        translation_store: Optional[TranslationStore] = None
    ):
        """Initialize translation orchestrator.
        
        Args:
            llm_client: LLM client for translation
            validator: Code validator (optional)
            context_optimizer: Context optimizer (optional, uses default if None)
            translation_store: Translation cache (optional, creates new if None)
        """
        self.llm_client = llm_client
        self.validator = validator or CodeValidator()
        self.context_optimizer = context_optimizer or ContextOptimizer()
        self.translation_store = translation_store or TranslationStore()
        self.settings = get_settings()
        
        # Load translation prompt template from file
        self._translation_prompt_template = self._load_prompt_template()
        
        logger.info(
            "TranslationOrchestrator initialized",
            extra={"stage_name": "translation_orchestration"}
        )
    
    async def translate_repository(
        self,
        dependency_graph: nx.DiGraph,
        ast_index: Dict[str, ASTNode],
        target_language: str = "python"
    ) -> List[TranslationResult]:
        """Translate entire repository in dependency order.
        
        Args:
            dependency_graph: NetworkX directed graph of dependencies
            ast_index: Dictionary mapping node IDs to ASTNode objects
            target_language: Target programming language (default: python)
            
        Returns:
            List of TranslationResult objects
            
        Raises:
            ValueError: If circular dependencies detected
        """
        logger.info(
            f"Starting repository translation to {target_language}",
            extra={
                "stage_name": "translation_orchestration",
                "target_language": target_language,
                "node_count": dependency_graph.number_of_nodes()
            }
        )
        
        # Step 1: Detect circular dependencies
        if not nx.is_directed_acyclic_graph(dependency_graph):
            cycles = list(nx.simple_cycles(dependency_graph))
            error_msg = f"Circular dependencies detected: {len(cycles)} cycles found"
            logger.error(
                error_msg,
                extra={
                    "stage_name": "translation_orchestration",
                    "cycle_count": len(cycles),
                    "sample_cycles": cycles[:3]
                }
            )
            raise ValueError(error_msg)
        
        # Step 2: Perform topological sort (leaf-first)
        try:
            sorted_nodes = list(nx.topological_sort(dependency_graph))
            logger.info(
                f"Topological sort complete: {len(sorted_nodes)} nodes",
                extra={
                    "stage_name": "translation_orchestration",
                    "sorted_node_count": len(sorted_nodes)
                }
            )
        except nx.NetworkXError as e:
            logger.error(
                f"Topological sort failed: {e}",
                extra={"stage_name": "translation_orchestration", "error": str(e)}
            )
            raise ValueError(f"Failed to sort dependencies: {e}")
        
        # Step 3: Translate each node in order
        results: List[TranslationResult] = []
        
        for node_id in sorted_nodes:
            try:
                result = await self._translate_node(
                    node_id=node_id,
                    dependency_graph=dependency_graph,
                    ast_index=ast_index,
                    target_language=target_language
                )
                results.append(result)
                
            except Exception as e:
                logger.error(
                    f"Failed to translate node {node_id}: {e}",
                    extra={
                        "stage_name": "translation_orchestration",
                        "node_id": node_id,
                        "error": str(e)
                    }
                )
                # Create failed result and continue
                results.append(TranslationResult(
                    module_name=node_id,
                    status=TranslationStatus.FAILED,
                    errors=[str(e)]
                ))
        
        # Summary logging
        success_count = sum(1 for r in results if r.status == TranslationStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == TranslationStatus.FAILED)
        skipped_count = sum(1 for r in results if r.status == TranslationStatus.SKIPPED)
        total_tokens = sum(r.token_usage for r in results)
        
        logger.info(
            f"Repository translation complete: {success_count} success, {failed_count} failed, {skipped_count} skipped",
            extra={
                "stage_name": "translation_orchestration",
                "success_count": success_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
                "total_tokens": total_tokens
            }
        )
        
        return results

    async def _translate_node(
        self,
        node_id: str,
        dependency_graph: nx.DiGraph,
        ast_index: Dict[str, ASTNode],
        target_language: str
    ) -> TranslationResult:
        """Translate a single node with caching and validation.
        
        Args:
            node_id: Node identifier
            dependency_graph: Dependency graph
            ast_index: AST node index
            target_language: Target language
            
        Returns:
            TranslationResult
        """
        logger.info(
            f"Translating node: {node_id}",
            extra={"stage_name": "translation_orchestration", "node_id": node_id}
        )
        
        # Get AST node
        if node_id not in ast_index:
            error_msg = f"Node {node_id} not found in AST index"
            logger.error(
                error_msg,
                extra={"stage_name": "translation_orchestration", "node_id": node_id}
            )
            return TranslationResult(
                module_name=node_id,
                status=TranslationStatus.FAILED,
                errors=[error_msg]
            )
        
        ast_node = ast_index[node_id]
        
        # Calculate source hash for caching
        source_hash = self._calculate_hash(ast_node.raw_source)
        
        # Check cache if enabled
        if self.settings.CACHE_ENABLED:
            cached_result = self.translation_store.get_by_hash(source_hash)
            if cached_result:
                logger.info(
                    f"Cache hit for {node_id}",
                    extra={"stage_name": "translation_orchestration", "node_id": node_id}
                )
                # Return cached result with updated module name
                cached_result.module_name = node_id
                cached_result.status = TranslationStatus.SKIPPED
                return cached_result
        
        # Build optimized context
        try:
            optimized_context = self.context_optimizer.optimize_context(
                target_node_id=node_id,
                dependency_graph=dependency_graph,
                ast_index=ast_index
            )
            
            logger.debug(
                f"Context optimized: {len(optimized_context.included_nodes)} nodes, {optimized_context.estimated_tokens} tokens",
                extra={
                    "stage_name": "translation_orchestration",
                    "node_id": node_id,
                    "included_nodes": len(optimized_context.included_nodes),
                    "estimated_tokens": optimized_context.estimated_tokens
                }
            )
            
        except Exception as e:
            logger.error(
                f"Context optimization failed for {node_id}: {e}",
                extra={"stage_name": "translation_orchestration", "node_id": node_id, "error": str(e)}
            )
            return TranslationResult(
                module_name=node_id,
                status=TranslationStatus.FAILED,
                errors=[f"Context optimization failed: {e}"]
            )
        
        # Prepare translation prompt
        prompt = self._build_translation_prompt(
            source_code=optimized_context.combined_source,
            target_language=target_language,
            node_name=ast_node.name,
            node_type=ast_node.node_type
        )
        
        # Call LLM for translation
        try:
            translated_code = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more deterministic translation
                max_tokens=self.settings.MAX_TOKEN_LIMIT
            )
            
            # Estimate token usage (prompt + response)
            token_usage = self.context_optimizer.estimate_tokens(prompt) + \
                         self.context_optimizer.estimate_tokens(translated_code)
            
            logger.info(
                f"Translation complete for {node_id}",
                extra={
                    "stage_name": "translation_orchestration",
                    "node_id": node_id,
                    "token_usage": token_usage
                }
            )
            
        except Exception as e:
            logger.error(
                f"LLM translation failed for {node_id}: {e}",
                extra={"stage_name": "translation_orchestration", "node_id": node_id, "error": str(e)}
            )
            return TranslationResult(
                module_name=node_id,
                status=TranslationStatus.FAILED,
                errors=[f"LLM translation failed: {e}"],
                dependencies_used=optimized_context.included_nodes
            )
        
        # Validate translation
        validation_errors = []
        validation_warnings = []
        
        if self.validator:
            try:
                validation_results = self.validator.validate_syntax(
                    code=translated_code,
                    language=target_language
                )
                
                for result in validation_results:
                    if result.level == ValidationLevel.ERROR:
                        validation_errors.append(f"{result.location}: {result.message}")
                    elif result.level == ValidationLevel.WARNING:
                        validation_warnings.append(f"{result.location}: {result.message}")
                
                if validation_errors:
                    logger.warning(
                        f"Validation errors for {node_id}: {len(validation_errors)} errors",
                        extra={
                            "stage_name": "translation_orchestration",
                            "node_id": node_id,
                            "error_count": len(validation_errors)
                        }
                    )
                
            except Exception as e:
                logger.warning(
                    f"Validation failed for {node_id}: {e}",
                    extra={"stage_name": "translation_orchestration", "node_id": node_id, "error": str(e)}
                )
                validation_warnings.append(f"Validation error: {e}")
        
        # Determine final status
        if validation_errors:
            status = TranslationStatus.FAILED
        else:
            status = TranslationStatus.SUCCESS
        
        # Create result
        result = TranslationResult(
            module_name=node_id,
            status=status,
            translated_code=translated_code,
            dependencies_used=optimized_context.included_nodes,
            token_usage=token_usage,
            errors=validation_errors,
            warnings=validation_warnings,
            source_hash=source_hash
        )
        
        # Store in cache
        if self.settings.CACHE_ENABLED:
            self.translation_store.store(result)
        
        return result
    
    def _calculate_hash(self, source: str) -> str:
        """Calculate SHA-256 hash of source code.
        
        Args:
            source: Source code string
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(source.encode('utf-8')).hexdigest()
    
    def _load_prompt_template(self) -> str:
        """Load translation prompt template from file.
        
        Returns:
            Prompt template string
        """
        prompt_file = Path("prompts/translation_v1.txt")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()
            logger.debug(
                f"Loaded prompt template from {prompt_file}",
                extra={"stage_name": "translation_orchestration"}
            )
            return template
        except FileNotFoundError:
            logger.warning(
                f"Prompt template file not found: {prompt_file}, using default",
                extra={"stage_name": "translation_orchestration"}
            )
            # Fallback to embedded template if file not found
            return self._get_default_prompt_template()
        except Exception as e:
            logger.warning(
                f"Failed to load prompt template: {e}, using default",
                extra={"stage_name": "translation_orchestration", "error": str(e)}
            )
            return self._get_default_prompt_template()
    
    def _get_default_prompt_template(self) -> str:
        """Get default prompt template as fallback.
        
        Returns:
            Default prompt template string
        """
        return """Translate the following {node_type} named '{node_name}' from legacy code to {target_language}.

Requirements:
1. Preserve the original logic and behavior
2. Follow {target_language} best practices and idioms
3. Add type hints where appropriate
4. Include docstrings for functions and classes
5. Handle errors gracefully
6. Maintain the same interface (function signatures, class methods)

Source Code:
```
{source_code}
```

Provide only the translated {target_language} code without explanations or markdown formatting.
"""
    
    def _build_translation_prompt(
        self,
        source_code: str,
        target_language: str,
        node_name: str,
        node_type: str
    ) -> str:
        """Build translation prompt from template.
        
        Args:
            source_code: Source code to translate
            target_language: Target programming language
            node_name: Name of the node being translated
            node_type: Type of the node (function, class, etc.)
            
        Returns:
            Formatted prompt string
        """
        return self._translation_prompt_template.format(
            node_type=node_type,
            node_name=node_name,
            target_language=target_language,
            source_code=source_code
        )
    
    def get_translation_statistics(self, results: List[TranslationResult]) -> Dict[str, any]:
        """Calculate statistics from translation results.
        
        Args:
            results: List of TranslationResult objects
            
        Returns:
            Dictionary with statistics
        """
        total = len(results)
        success = sum(1 for r in results if r.status == TranslationStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == TranslationStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TranslationStatus.SKIPPED)
        total_tokens = sum(r.token_usage for r in results)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        
        return {
            "total_modules": total,
            "successful": success,
            "failed": failed,
            "skipped": skipped,
            "success_rate": (success / total * 100) if total > 0 else 0.0,
            "total_tokens": total_tokens,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "average_tokens_per_module": (total_tokens / total) if total > 0 else 0
        }
