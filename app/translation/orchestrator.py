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
from app.llm.llm_service import LLMService
from app.parsers.base import ASTNode
from app.core.config import get_settings
from app.core.logging import get_logger
from app.prompt_versioning import PromptVersionManager
from app.prompt_versioning.schema import PromptBundle

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
        llm_service: LLMService,
        context_optimizer: Optional[ContextOptimizer] = None,
        translation_store: Optional[TranslationStore] = None,
        prompt_manager: Optional[PromptVersionManager] = None
    ):
        """Initialize translation orchestrator.
        
        Args:
            llm_service: LLM service for translation (with caching and retry)
            context_optimizer: Context optimizer (optional, uses default if None)
            translation_store: Translation cache (optional, creates new if None)
            prompt_manager: Prompt version manager (optional, creates new if None)
        """
        self.llm_service = llm_service
        self.context_optimizer = context_optimizer or ContextOptimizer()
        self.translation_store = translation_store or TranslationStore()
        self.prompt_manager = prompt_manager or PromptVersionManager()
        self.settings = get_settings()
        
        # Register and load translation prompt template
        self._register_prompts()
        
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
        
        # Prepare translation prompt bundle
        prompt_bundle = self._build_translation_prompt(
            source_code=optimized_context.combined_source,
            target_language=target_language,
            node_name=ast_node.name,
            node_type=ast_node.node_type
        )
        
        # Call LLM for translation
        try:
            response = self.llm_service.generate(
                system_prompt=prompt_bundle.system_prompt,
                user_prompt=prompt_bundle.user_prompt,
                max_tokens=self.settings.MAX_TOKEN_LIMIT,
                temperature=0.3  # Lower temperature for more deterministic translation
            )
            
            translated_code = response.text
            
            # Use token count from response if available, otherwise estimate
            if response.token_count > 0:
                token_usage = response.token_count
            else:
                # Estimate token usage (prompt + response)
                token_usage = self.context_optimizer.token_estimator.estimate_tokens(
                    prompt_bundle.system_prompt + prompt_bundle.user_prompt
                ) + self.context_optimizer.token_estimator.estimate_tokens(translated_code)
            
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
        
        # Validate translation (removed - validation done separately in pipeline)
        validation_errors = []
        validation_warnings = []
        
        # Determine final status
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
    
    def _register_prompts(self) -> None:
        """Register prompt templates in PromptVersionManager.
        
        Loads prompts from files and registers them with version 1.0.0.
        This should be called once during initialization.
        """
        prompts_to_register = [
            ("code_translation", "prompts/translation_v1.txt", "Code translation prompt"),
        ]
        
        for prompt_name, prompt_file, description in prompts_to_register:
            try:
                # Check if prompt already registered
                try:
                    existing = self.prompt_manager.get_latest(prompt_name)
                    logger.debug(
                        f"Prompt '{prompt_name}' already registered at v{existing.version}",
                        extra={"stage_name": "translation_orchestration"}
                    )
                    continue
                except:
                    # Prompt not registered, proceed with registration
                    pass
                
                # Load prompt content from file
                prompt_path = Path(prompt_file)
                if not prompt_path.exists():
                    logger.warning(
                        f"Prompt file not found: {prompt_file}",
                        extra={"stage_name": "translation_orchestration"}
                    )
                    continue
                
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Register with version 1.0.0
                self.prompt_manager.register_prompt(
                    name=prompt_name,
                    version="1.0.0",
                    content=content,
                    metadata={
                        "description": description,
                        "source_file": prompt_file,
                        "registered_at": "pipeline_initialization"
                    }
                )
                
                logger.info(
                    f"Registered prompt '{prompt_name}' v1.0.0",
                    extra={"stage_name": "translation_orchestration"}
                )
                
            except Exception as e:
                logger.warning(
                    f"Failed to register prompt '{prompt_name}': {e}",
                    extra={"stage_name": "translation_orchestration", "error": str(e)}
                )
    
    def _sanitize_code(self, code: str, max_length: int = 50000) -> str:
        """Sanitize code to prevent token overflow.
        
        Args:
            code: Source code to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized code
        """
        if not code:
            return ""
        
        if len(code) > max_length:
            logger.warning(
                "Source code truncated to prevent token overflow",
                extra={"stage_name": "translation_orchestration"}
            )
            return code[:max_length]
        
        return code
    
    def _build_translation_prompt(
        self,
        source_code: str,
        target_language: str,
        node_name: str,
        node_type: str
    ) -> PromptBundle:
        """Build structured translation prompt bundle.
        
        Args:
            source_code: Source code to translate
            target_language: Target programming language
            node_name: Name of the node being translated
            node_type: Type of the node (function, class, etc.)
            
        Returns:
            PromptBundle with system and user prompts
        """
        # Sanitize source code to prevent token overflow
        sanitized_source = self._sanitize_code(source_code)
        
        # Get prompt bundle from version manager
        try:
            prompt_bundle = self.prompt_manager.get_prompt_bundle("code_translation")
        except Exception as e:
            logger.error(
                f"Failed to load prompt bundle: {e}",
                extra={"stage_name": "translation_orchestration", "error": str(e)}
            )
            # Fallback to basic prompts
            prompt_bundle = PromptBundle(
                system_prompt="You are a code translation assistant. Translate the provided code accurately.",
                user_prompt="Translate the following code to {target_language}:\n\n{source_code}",
                version="fallback",
                metadata={}
            )
        
        # Format user prompt with actual values
        formatted_user_prompt = prompt_bundle.user_prompt.format(
            node_type=node_type,
            node_name=node_name,
            target_language=target_language,
            source_code=sanitized_source
        )
        
        return PromptBundle(
            system_prompt=prompt_bundle.system_prompt,
            user_prompt=formatted_user_prompt,
            version=prompt_bundle.version,
            metadata=prompt_bundle.metadata
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
    
    def get_prompt_version(self, prompt_name: str) -> str:
        """Get current version of a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Version string (e.g., "1.0.0")
        """
        try:
            prompt = self.prompt_manager.get_latest(prompt_name)
            return prompt.version
        except Exception:
            return "unknown"
