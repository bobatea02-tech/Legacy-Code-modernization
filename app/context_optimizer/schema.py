"""Schema definitions for context optimization."""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class OptimizedContext:
    """Result of context optimization containing selected nodes and metadata.
    
    This dataclass represents the optimized code context ready for LLM translation.
    It includes the minimal set of dependencies needed while staying under token limits.
    """
    
    included_nodes: List[str] = field(default_factory=list)
    """List of node IDs included in the optimized context."""
    
    excluded_nodes: List[str] = field(default_factory=list)
    """List of node IDs excluded due to token limits."""
    
    combined_source: str = ""
    """Combined source code from all included nodes."""
    
    estimated_tokens: int = 0
    """Estimated token count for the combined source."""
    
    target_node_id: str = ""
    """The target node ID that was being optimized."""
    
    expansion_depth: int = 0
    """The depth used for dependency expansion."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "included_nodes": self.included_nodes,
            "excluded_nodes": self.excluded_nodes,
            "combined_source": self.combined_source,
            "estimated_tokens": self.estimated_tokens,
            "target_node_id": self.target_node_id,
            "expansion_depth": self.expansion_depth
        }


class ContextOptimizationError(Exception):
    """Base exception for context optimization errors."""
    pass


class MissingNodeError(ContextOptimizationError):
    """Raised when a required node is not found in the graph or AST index."""
    pass


class EmptyGraphError(ContextOptimizationError):
    """Raised when the dependency graph is empty."""
    pass


class TokenLimitExceededError(ContextOptimizationError):
    """Raised when even the target node alone exceeds token limits."""
    pass


class ContextWindowExceededError(ContextOptimizationError):
    """Raised when optimized context exceeds safe context window limit."""
    pass
