"""Dependency graph abstract interface.

This module defines the abstract interface for dependency graph implementations.
GraphBuilder is the concrete implementation using NetworkX.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Set


class DependencyGraph(ABC):
    """Abstract base class for dependency graph implementations.
    
    This interface allows swapping graph implementations without changing
    consumers. GraphBuilder provides the concrete NetworkX-based implementation.
    """
    
    @abstractmethod
    def add_node(self, node_id: str, metadata: Dict[str, Any]) -> None:
        """Add a node to the graph.
        
        Args:
            node_id: Unique identifier for the node
            metadata: Node metadata (name, type, file_path, etc.)
        """
        pass
    
    @abstractmethod
    def add_edge(self, source: str, target: str, edge_type: str) -> None:
        """Add a dependency edge.
        
        Args:
            source: Source node identifier
            target: Target node identifier
            edge_type: Type of dependency (e.g., 'calls', 'imports')
        """
        pass
    
    @abstractmethod
    def get_dependencies(self, node_id: str) -> Set[str]:
        """Get all dependencies for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Set of dependent node identifiers
        """
        pass
