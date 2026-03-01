"""Dependency graph builder using NetworkX.

This module converts AST nodes into a directed, typed dependency graph
suitable for context optimization and subgraph extraction.
"""

from typing import Dict, Any, List, Set, Optional
from collections import deque
import networkx as nx

from app.parsers.base import ASTNode
from app.core.logging import get_logger

logger = get_logger(__name__)


class GraphBuilder:
    """Builds and manages directed dependency graphs from AST nodes."""
    
    def __init__(self):
        """Initialize graph builder."""
        self.graph: Optional[nx.DiGraph] = None
        self._symbol_index: Dict[str, str] = {}  # symbol_name -> node_id mapping
        
    def build_graph(self, ast_nodes: List[ASTNode]) -> nx.DiGraph:
        """Build directed dependency graph from AST nodes.
        
        Args:
            ast_nodes: List of ASTNode objects (not mutated)
            
        Returns:
            NetworkX directed graph with typed edges
            
        Note:
            - Node IDs format: "{file_path}:{name}:{start_line}"
            - Edge types: "calls", "imports"
            - Unresolved symbols are logged but don't cause failures
        """
        logger.info(
            f"Starting graph build with {len(ast_nodes)} AST nodes",
            extra={"stage_name": "dependency_graph", "node_count": len(ast_nodes)}
        )
        
        # Initialize new graph
        self.graph = nx.DiGraph()
        self._symbol_index = {}
        
        # Handle empty input safely
        if not ast_nodes:
            logger.warning("Empty AST node list provided", extra={"stage_name": "dependency_graph"})
            return self.graph
        
        # Phase 1: Add all nodes and build symbol index
        self._add_nodes(ast_nodes)
        
        # Phase 2: Add edges based on dependencies
        self._add_edges(ast_nodes)
        
        # Phase 3: Detect and log cycles
        self._detect_cycles()
        
        logger.info(
            f"Graph build complete: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges",
            extra={
                "stage_name": "dependency_graph",
                "node_count": self.graph.number_of_nodes(),
                "edge_count": self.graph.number_of_edges()
            }
        )
        
        return self.graph
    
    def _add_nodes(self, ast_nodes: List[ASTNode]) -> None:
        """Add all AST nodes to the graph and build symbol index.
        
        Args:
            ast_nodes: List of ASTNode objects
        """
        for ast_node in ast_nodes:
            try:
                # Generate globally unique node ID
                node_id = self._generate_node_id(ast_node)
                
                # Add node with attributes
                self.graph.add_node(
                    node_id,
                    id=ast_node.id,
                    name=ast_node.name,
                    node_type=ast_node.node_type,
                    file_path=ast_node.file_path,
                    start_line=ast_node.start_line,
                    end_line=ast_node.end_line
                )
                
                # Build symbol index for O(1) lookup
                # Use qualified name for better resolution
                symbol_key = f"{ast_node.file_path}:{ast_node.name}"
                self._symbol_index[symbol_key] = node_id
                
                # Also index by simple name for cross-file resolution
                if ast_node.name not in self._symbol_index:
                    self._symbol_index[ast_node.name] = node_id
                
            except Exception as e:
                logger.warning(
                    f"Failed to add node for {ast_node.name}: {e}",
                    extra={"stage_name": "dependency_graph", "node_name": ast_node.name, "error": str(e)}
                )
                continue
    
    def _add_edges(self, ast_nodes: List[ASTNode]) -> None:
        """Add dependency edges to the graph.
        
        Args:
            ast_nodes: List of ASTNode objects
        """
        unresolved_symbols: Set[str] = set()
        
        for ast_node in ast_nodes:
            try:
                source_id = self._generate_node_id(ast_node)
                
                # Skip if source node wasn't added
                if source_id not in self.graph:
                    continue
                
                # Add "calls" edges for called symbols
                for called_symbol in ast_node.called_symbols:
                    target_id = self._resolve_symbol(called_symbol, ast_node.file_path)
                    
                    if target_id:
                        self.graph.add_edge(source_id, target_id, edge_type="calls")
                    else:
                        unresolved_symbols.add(called_symbol)
                
                # Add "imports" edges for imported symbols
                for imported_symbol in ast_node.imports:
                    target_id = self._resolve_symbol(imported_symbol, ast_node.file_path)
                    
                    if target_id:
                        self.graph.add_edge(source_id, target_id, edge_type="imports")
                    else:
                        unresolved_symbols.add(imported_symbol)
                        
            except Exception as e:
                logger.warning(
                    f"Failed to add edges for {ast_node.name}: {e}",
                    extra={"stage_name": "dependency_graph", "node_name": ast_node.name, "error": str(e)}
                )
                continue
        
        # Log unresolved symbols (expected for external dependencies)
        if unresolved_symbols:
            logger.debug(
                f"Unresolved symbols: {len(unresolved_symbols)} (external dependencies)",
                extra={
                    "stage_name": "dependency_graph",
                    "unresolved_count": len(unresolved_symbols),
                    "sample_symbols": list(unresolved_symbols)[:10]
                }
            )
    
    def _resolve_symbol(self, symbol: str, current_file: str) -> Optional[str]:
        """Resolve a symbol name to a node ID.
        
        Args:
            symbol: Symbol name to resolve
            current_file: Current file path for context
            
        Returns:
            Node ID if resolved, None otherwise
        """
        # Try file-qualified lookup first (most specific)
        qualified_key = f"{current_file}:{symbol}"
        if qualified_key in self._symbol_index:
            return self._symbol_index[qualified_key]
        
        # Fall back to simple name lookup (cross-file)
        if symbol in self._symbol_index:
            return self._symbol_index[symbol]
        
        # Symbol not found (likely external dependency)
        return None
    
    def _generate_node_id(self, ast_node: ASTNode) -> str:
        """Generate globally unique node ID.
        
        Args:
            ast_node: ASTNode object
            
        Returns:
            Unique node ID in format "{file_path}:{name}:{start_line}"
        """
        return f"{ast_node.file_path}:{ast_node.name}:{ast_node.start_line}"
    
    def _detect_cycles(self) -> None:
        """Detect and log cycles in the dependency graph.
        
        When cycles are detected, annotates circular edges with metadata
        'is_circular': True for downstream consumers.
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            
            if cycles:
                logger.info(
                    f"Detected {len(cycles)} cycles in dependency graph",
                    extra={
                        "stage_name": "dependency_graph",
                        "cycle_count": len(cycles),
                        "sample_cycles": cycles[:5]  # Log first 5 cycles
                    }
                )
                
                # TASK 2: Annotate circular edges with metadata
                for cycle in cycles:
                    for i in range(len(cycle)):
                        source = cycle[i]
                        target = cycle[(i + 1) % len(cycle)]
                        
                        # Mark edge as circular if it exists
                        if self.graph.has_edge(source, target):
                            self.graph.edges[source, target]['is_circular'] = True
                
                logger.debug(
                    f"Annotated {len(cycles)} circular dependency paths",
                    extra={"stage_name": "dependency_graph", "cycle_count": len(cycles)}
                )
            else:
                logger.debug(
                    "No cycles detected in dependency graph",
                    extra={"stage_name": "dependency_graph"}
                )
                
        except Exception as e:
            logger.warning(
                f"Failed to detect cycles: {e}",
                extra={"stage_name": "dependency_graph", "error": str(e)}
            )
    
    def get_subgraph(self, root_id: str, depth: int) -> nx.DiGraph:
        """Extract dependency-limited subgraph using BFS traversal.
        
        Args:
            root_id: Starting node ID
            depth: Maximum traversal depth (0 = root only, 1 = root + direct deps, etc.)
            
        Returns:
            Subgraph containing root and dependencies up to specified depth
            
        Raises:
            ValueError: If root_id not in graph or depth is negative
        """
        if self.graph is None:
            logger.error("Graph not built yet", extra={"stage_name": "dependency_graph"})
            return nx.DiGraph()
        
        if root_id not in self.graph:
            logger.error(
                f"Root node {root_id} not found in graph",
                extra={"stage_name": "dependency_graph", "root_id": root_id}
            )
            raise ValueError(f"Node {root_id} not found in graph")
        
        if depth < 0:
            raise ValueError(f"Depth must be non-negative, got {depth}")
        
        logger.info(
            f"Extracting subgraph from {root_id} with depth {depth}",
            extra={"stage_name": "dependency_graph", "root_id": root_id, "depth": depth}
        )
        
        # BFS traversal to collect nodes within depth limit
        visited_nodes = set()
        queue = deque([(root_id, 0)])  # (node_id, current_depth)
        visited_nodes.add(root_id)
        
        while queue:
            current_node, current_depth = queue.popleft()
            
            # Stop if we've reached depth limit
            if current_depth >= depth:
                continue
            
            # Add all successors (dependencies)
            for successor in self.graph.successors(current_node):
                if successor not in visited_nodes:
                    visited_nodes.add(successor)
                    queue.append((successor, current_depth + 1))
        
        # Create subgraph with collected nodes
        subgraph = self.graph.subgraph(visited_nodes).copy()
        
        logger.info(
            f"Subgraph extracted: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges",
            extra={
                "stage_name": "dependency_graph",
                "subgraph_nodes": subgraph.number_of_nodes(),
                "subgraph_edges": subgraph.number_of_edges()
            }
        )
        
        return subgraph
    
    def export_json(self) -> Dict[str, Any]:
        """Export graph to JSON-serializable structure.
        
        Returns:
            Dictionary with "nodes" and "edges" lists
            
        Format:
            {
                "nodes": [
                    {
                        "id": "file.py:func:10",
                        "name": "func",
                        "node_type": "function",
                        "file_path": "file.py",
                        "start_line": 10,
                        "end_line": 20
                    },
                    ...
                ],
                "edges": [
                    {
                        "source": "file.py:func:10",
                        "target": "file.py:helper:30",
                        "edge_type": "calls"
                    },
                    ...
                ]
            }
        """
        if self.graph is None:
            logger.warning("Graph not built yet, returning empty structure", extra={"stage_name": "dependency_graph"})
            return {"nodes": [], "edges": []}
        
        # Export nodes with attributes
        nodes = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            nodes.append({
                "id": node_id,
                "name": node_data.get("name"),
                "node_type": node_data.get("node_type"),
                "file_path": node_data.get("file_path"),
                "start_line": node_data.get("start_line"),
                "end_line": node_data.get("end_line")
            })
        
        # Export edges with attributes
        edges = []
        for source, target, edge_data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "edge_type": edge_data.get("edge_type")
            })
        
        logger.debug(
            f"Exported graph: {len(nodes)} nodes, {len(edges)} edges",
            extra={"stage_name": "dependency_graph", "node_count": len(nodes), "edge_count": len(edges)}
        )
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def get_node_dependencies(self, node_id: str) -> Set[str]:
        """Get all direct dependencies for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Set of node IDs that this node depends on
        """
        if self.graph is None or node_id not in self.graph:
            return set()
        
        return set(self.graph.successors(node_id))
    
    def get_node_dependents(self, node_id: str) -> Set[str]:
        """Get all nodes that depend on this node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Set of node IDs that depend on this node
        """
        if self.graph is None or node_id not in self.graph:
            return set()
        
        return set(self.graph.predecessors(node_id))
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics for monitoring and debugging.
        
        Returns:
            Dictionary with graph metrics
        """
        if self.graph is None:
            return {
                "node_count": 0,
                "edge_count": 0,
                "is_dag": True,
                "connected_components": 0
            }
        
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
            "connected_components": nx.number_weakly_connected_components(self.graph),
            "density": nx.density(self.graph)
        }
