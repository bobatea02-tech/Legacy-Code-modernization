"""Context optimization engine for dependency-aware code selection.

This module implements a BFS-based context optimizer that selects minimal
code context for LLM translation while respecting token limits and dependency depth.
"""

from typing import Dict, List, Optional
from collections import deque
import networkx as nx

from app.parsers.base import ASTNode
from app.context_optimizer.schema import (
    OptimizedContext,
    ContextOptimizationError,
    MissingNodeError,
    EmptyGraphError,
    TokenLimitExceededError,
    ContextWindowExceededError
)
from app.context_optimizer.token_estimator import TokenEstimator, HeuristicTokenEstimator
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContextOptimizer:
    """Optimizes code context for LLM token limits using dependency-aware selection."""
    
    def __init__(
        self,
        token_estimator: Optional[TokenEstimator] = None,
        max_tokens: Optional[int] = None,
        expansion_depth: Optional[int] = None
    ):
        """Initialize optimizer with token estimator and limits.
        
        Args:
            token_estimator: Token estimation strategy (uses HeuristicTokenEstimator if None)
            max_tokens: Maximum token count for context (uses config default if None)
            expansion_depth: Maximum dependency traversal depth (uses config default if None)
        """
        settings = get_settings()
        self.token_estimator = token_estimator if token_estimator is not None else HeuristicTokenEstimator()
        self.max_tokens = max_tokens if max_tokens is not None else settings.MAX_TOKEN_LIMIT
        self.expansion_depth = expansion_depth if expansion_depth is not None else settings.CONTEXT_EXPANSION_DEPTH
        
        logger.info(
            f"ContextOptimizer initialized: max_tokens={self.max_tokens}, expansion_depth={self.expansion_depth}",
            extra={"stage_name": "context_optimization", "max_tokens": self.max_tokens, "expansion_depth": self.expansion_depth}
        )
    
    def optimize_context(
        self,
        target_node_id: str,
        dependency_graph: nx.DiGraph,
        ast_index: Dict[str, ASTNode],
        max_tokens: Optional[int] = None,
        expansion_depth: Optional[int] = None
    ) -> OptimizedContext:
        """Select minimal dependency-aware code context for LLM translation.
        
        Uses BFS to expand from target node, respecting depth and token limits.
        Always includes the target node.
        
        Args:
            target_node_id: ID of the node to translate
            dependency_graph: NetworkX directed graph of dependencies
            ast_index: Dictionary mapping node IDs to ASTNode objects
            max_tokens: Override default max tokens (optional)
            expansion_depth: Override default expansion depth (optional)
            
        Returns:
            OptimizedContext with selected nodes and metadata
            
        Raises:
            EmptyGraphError: If dependency graph is empty
            MissingNodeError: If target node not found
            TokenLimitExceededError: If target node alone exceeds token limit
        """
        # Use instance defaults if not overridden
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        expansion_depth = expansion_depth if expansion_depth is not None else self.expansion_depth
        
        logger.info(
            f"Starting context optimization for {target_node_id}",
            extra={
                "stage_name": "context_optimization",
                "target_node_id": target_node_id,
                "max_tokens": max_tokens,
                "expansion_depth": expansion_depth
            }
        )
        
        # Validate inputs
        self._validate_inputs(target_node_id, dependency_graph, ast_index)
        
        # Initialize result
        result = OptimizedContext(
            target_node_id=target_node_id,
            expansion_depth=expansion_depth
        )
        
        # BFS expansion from target node
        included_nodes = []
        excluded_nodes = []
        current_tokens = 0
        
        # Always include target node first
        target_ast = ast_index[target_node_id]
        target_source = self.token_estimator.clean_source(target_ast.raw_source)
        target_tokens = self.token_estimator.estimate_tokens(target_source)
        
        if target_tokens > max_tokens:
            logger.error(
                f"Target node alone exceeds token limit: {target_tokens} > {max_tokens}",
                extra={
                    "stage_name": "context_optimization",
                    "target_node_id": target_node_id,
                    "target_tokens": target_tokens,
                    "max_tokens": max_tokens
                }
            )
            raise TokenLimitExceededError(
                f"Target node {target_node_id} alone requires {target_tokens} tokens, exceeds limit of {max_tokens}"
            )
        
        included_nodes.append(target_node_id)
        current_tokens += target_tokens
        
        logger.debug(
            f"Target node included: {target_node_id} ({target_tokens} tokens)",
            extra={"stage_name": "context_optimization", "node_id": target_node_id, "tokens": target_tokens}
        )
        
        # BFS to collect dependencies
        visited = {target_node_id}
        queue = deque([(target_node_id, 0)])  # (node_id, depth)
        
        while queue:
            current_node, current_depth = queue.popleft()
            
            # Stop if we've reached depth limit
            if current_depth >= expansion_depth:
                continue
            
            # Get dependencies (successors in the graph)
            if current_node in dependency_graph:
                for dependency in dependency_graph.successors(current_node):
                    if dependency in visited:
                        continue
                    
                    visited.add(dependency)
                    
                    # Check if dependency is in AST index
                    if dependency not in ast_index:
                        logger.warning(
                            f"Dependency {dependency} not found in AST index, skipping",
                            extra={"stage_name": "context_optimization", "dependency": dependency}
                        )
                        excluded_nodes.append(dependency)
                        continue
                    
                    # Estimate tokens for this dependency
                    dep_ast = ast_index[dependency]
                    dep_source = self.token_estimator.clean_source(dep_ast.raw_source)
                    dep_tokens = self.token_estimator.estimate_tokens(dep_source)
                    
                    # Check if adding this dependency would exceed token limit
                    if current_tokens + dep_tokens > max_tokens:
                        logger.debug(
                            f"Token limit reached, excluding {dependency}",
                            extra={
                                "stage_name": "context_optimization",
                                "node_id": dependency,
                                "current_tokens": current_tokens,
                                "dep_tokens": dep_tokens,
                                "max_tokens": max_tokens
                            }
                        )
                        excluded_nodes.append(dependency)
                        continue
                    
                    # Include this dependency
                    included_nodes.append(dependency)
                    current_tokens += dep_tokens
                    queue.append((dependency, current_depth + 1))
                    
                    logger.debug(
                        f"Dependency included: {dependency} ({dep_tokens} tokens, depth {current_depth + 1})",
                        extra={
                            "stage_name": "context_optimization",
                            "node_id": dependency,
                            "tokens": dep_tokens,
                            "depth": current_depth + 1
                        }
                    )
        
        # Combine source code from included nodes
        combined_sources = []
        for node_id in included_nodes:
            if node_id in ast_index:
                ast_node = ast_index[node_id]
                cleaned_source = self.token_estimator.clean_source(ast_node.raw_source)
                
                # Add file path comment for context
                file_comment = f"// File: {ast_node.file_path}, Line: {ast_node.start_line}\n"
                combined_sources.append(file_comment + cleaned_source)
        
        result.included_nodes = included_nodes
        result.excluded_nodes = excluded_nodes
        result.combined_source = "\n\n".join(combined_sources)
        result.estimated_tokens = current_tokens
        
        # TASK 4: Validate context window with 90% safety margin
        safe_limit = int(max_tokens * 0.9)
        if result.estimated_tokens > safe_limit:
            logger.error(
                f"Optimized context exceeds safe limit: {result.estimated_tokens} > {safe_limit} (90% of {max_tokens})",
                extra={
                    "stage_name": "context_optimization",
                    "target_node_id": target_node_id,
                    "estimated_tokens": result.estimated_tokens,
                    "safe_limit": safe_limit,
                    "max_tokens": max_tokens
                }
            )
            raise ContextWindowExceededError(
                f"Optimized context {result.estimated_tokens} tokens exceeds safe limit of {safe_limit} tokens (90% of {max_tokens})"
            )
        
        logger.info(
            f"Context optimization complete: {len(included_nodes)} included, {len(excluded_nodes)} excluded, {current_tokens} tokens",
            extra={
                "stage_name": "context_optimization",
                "target_node_id": target_node_id,
                "included_count": len(included_nodes),
                "excluded_count": len(excluded_nodes),
                "estimated_tokens": current_tokens
            }
        )
        
        return result
    
    def _validate_inputs(
        self,
        target_node_id: str,
        dependency_graph: nx.DiGraph,
        ast_index: Dict[str, ASTNode]
    ) -> None:
        """Validate inputs for context optimization.
        
        Args:
            target_node_id: Target node ID
            dependency_graph: Dependency graph
            ast_index: AST node index
            
        Raises:
            EmptyGraphError: If graph is empty
            MissingNodeError: If target node not found
        """
        if dependency_graph.number_of_nodes() == 0:
            logger.error("Empty dependency graph provided", extra={"stage_name": "context_optimization"})
            raise EmptyGraphError("Dependency graph is empty")
        
        if target_node_id not in dependency_graph:
            logger.error(
                f"Target node {target_node_id} not found in dependency graph",
                extra={"stage_name": "context_optimization", "target_node_id": target_node_id}
            )
            raise MissingNodeError(f"Target node {target_node_id} not found in dependency graph")
        
        if target_node_id not in ast_index:
            logger.error(
                f"Target node {target_node_id} not found in AST index",
                extra={"stage_name": "context_optimization", "target_node_id": target_node_id}
            )
            raise MissingNodeError(f"Target node {target_node_id} not found in AST index")
    
    def optimize(self, code_units: List[Dict]) -> List[Dict]:
        """Legacy method for backward compatibility.
        
        Args:
            code_units: List of code units with dependencies
            
        Returns:
            Optimized code units
        """
        # This is a legacy interface - new code should use optimize_context()
        logger.warning(
            "Using legacy optimize() method, consider using optimize_context() instead",
            extra={"stage_name": "context_optimization"}
        )
        return code_units
