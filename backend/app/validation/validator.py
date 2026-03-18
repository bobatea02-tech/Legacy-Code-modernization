"""Deterministic validation engine for translated code.

This module provides validation without LLM usage, ensuring:
- Syntax correctness via AST parsing
- Dependency completeness via graph traversal
- Structure preservation checks
- Symbol preservation verification
- Unit test stub generation
"""

import ast
import re
from dataclasses import dataclass
from typing import List, Set, Optional
from collections import deque

import networkx as nx

from app.parsers.base import ASTNode
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationReport:
    """Validation results for translated code."""
    
    module_name: str
    structure_valid: bool
    symbols_preserved: bool
    syntax_valid: bool
    dependencies_complete: bool
    missing_dependencies: List[str]
    unit_test_stub: str
    errors: List[str]


class ValidationEngine:
    """Deterministic validation engine for code translation."""
    
    def __init__(self):
        """Initialize validation engine with configuration."""
        settings = get_settings()
        self.context_expansion_depth = settings.CONTEXT_EXPANSION_DEPTH
    
    def validate_translation(
        self,
        original_node: ASTNode,
        translated_code: str,
        dependency_graph: Optional[nx.DiGraph] = None
    ) -> ValidationReport:
        """Validate translated code against original AST node.
        
        Args:
            original_node: Original AST node from source language
            translated_code: Generated Python code
            dependency_graph: Optional dependency graph for completeness check
            
        Returns:
            ValidationReport with all validation results
        """
        logger.info(
            f"Starting validation for {original_node.name}",
            extra={"stage_name": "validation", "node_name": original_node.name}
        )
        
        errors: List[str] = []
        
        # Run all validation checks
        syntax_valid = self._check_syntax(translated_code, errors)
        structure_valid = self._check_structure(original_node, translated_code, errors)
        symbols_preserved = self._check_symbols(original_node, translated_code, errors)
        
        missing_deps: List[str] = []
        dependencies_complete = self._check_dependencies(
            original_node,
            translated_code,
            dependency_graph,
            missing_deps,
            errors
        )
        
        # Check for incomplete translation markers
        completeness_valid = self._check_completeness(translated_code, errors)
        
        # Generate unit test stub
        unit_test_stub = self._generate_test_stub(original_node)
        
        # Overall validation status
        all_valid = (
            syntax_valid
            and structure_valid
            and symbols_preserved
            and dependencies_complete
            and completeness_valid
        )
        
        logger.info(
            f"Validation complete for {original_node.name}: {'PASS' if all_valid else 'FAIL'}",
            extra={
                "stage_name": "validation",
                "node_name": original_node.name,
                "syntax_valid": syntax_valid,
                "structure_valid": structure_valid,
                "symbols_preserved": symbols_preserved,
                "dependencies_complete": dependencies_complete,
                "error_count": len(errors)
            }
        )
        
        return ValidationReport(
            module_name=original_node.name,
            structure_valid=structure_valid,
            symbols_preserved=symbols_preserved,
            syntax_valid=syntax_valid,
            dependencies_complete=dependencies_complete,
            missing_dependencies=missing_deps,
            unit_test_stub=unit_test_stub,
            errors=errors
        )
    
    def _check_syntax(self, translated_code: str, errors: List[str]) -> bool:
        """Check Python syntax validity using AST parsing.
        
        Args:
            translated_code: Python code to validate
            errors: List to append error messages
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            ast.parse(translated_code)
            logger.debug("Syntax check passed", extra={"stage_name": "validation"})
            return True
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            errors.append(error_msg)
            logger.warning(
                f"Syntax check failed: {error_msg}",
                extra={"stage_name": "validation", "error": error_msg}
            )
            return False
        except Exception as e:
            error_msg = f"Unexpected error during syntax check: {str(e)}"
            errors.append(error_msg)
            logger.warning(
                f"Syntax check failed: {error_msg}",
                extra={"stage_name": "validation", "error": error_msg}
            )
            return False
    
    def _check_structure(
        self,
        original_node: ASTNode,
        translated_code: str,
        errors: List[str]
    ) -> bool:
        """Check if structure is preserved in translation.
        
        Validates:
        - Function/class name preservation
        - Parameter count preservation
        - Approximate control flow block count
        
        Args:
            original_node: Original AST node
            translated_code: Translated Python code
            errors: List to append error messages
            
        Returns:
            True if structure is preserved, False otherwise
        """
        structure_valid = True
        
        # Check name preservation
        if original_node.name not in translated_code:
            error_msg = f"Function/class name '{original_node.name}' not found in translated code"
            errors.append(error_msg)
            structure_valid = False
            logger.warning(
                error_msg,
                extra={"stage_name": "validation", "node_name": original_node.name}
            )
        
        # Check parameter count preservation
        try:
            tree = ast.parse(translated_code)
            translated_params = self._extract_parameters(tree, original_node.name)
            
            if translated_params is not None:
                original_param_count = len(original_node.parameters)
                translated_param_count = len(translated_params)
                
                if original_param_count != translated_param_count:
                    error_msg = (
                        f"Parameter count mismatch: expected {original_param_count}, "
                        f"got {translated_param_count}"
                    )
                    errors.append(error_msg)
                    structure_valid = False
                    logger.warning(
                        error_msg,
                        extra={"stage_name": "validation", "node_name": original_node.name}
                    )
        except Exception as e:
            error_msg = f"Failed to extract parameters: {str(e)}"
            errors.append(error_msg)
            structure_valid = False
            logger.warning(
                error_msg,
                extra={"stage_name": "validation", "node_name": original_node.name}
            )
        
        # Check approximate control flow preservation
        original_blocks = self._count_control_blocks(original_node.raw_source)
        translated_blocks = self._count_control_blocks(translated_code)
        
        # Allow some variance (±2 blocks) due to language differences
        if abs(original_blocks - translated_blocks) > 2:
            error_msg = (
                f"Control flow block count differs significantly: "
                f"original={original_blocks}, translated={translated_blocks}"
            )
            errors.append(error_msg)
            structure_valid = False
            logger.warning(
                error_msg,
                extra={"stage_name": "validation", "node_name": original_node.name}
            )
        
        logger.debug(
            f"Structure check: {'passed' if structure_valid else 'failed'}",
            extra={"stage_name": "validation", "node_name": original_node.name}
        )
        
        return structure_valid
    
    def _check_symbols(
        self,
        original_node: ASTNode,
        translated_code: str,
        errors: List[str]
    ) -> bool:
        """Check if all called symbols are preserved in translation.
        
        Args:
            original_node: Original AST node
            translated_code: Translated Python code
            errors: List to append error messages
            
        Returns:
            True if all symbols are preserved, False otherwise
        """
        missing_symbols: List[str] = []
        
        # Remove comments to avoid false positives
        code_without_comments = self._remove_comments(translated_code)
        
        for symbol in original_node.called_symbols:
            # Check if symbol appears in translated code (excluding comments)
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(symbol) + r'\b'
            if not re.search(pattern, code_without_comments):
                missing_symbols.append(symbol)
        
        if missing_symbols:
            error_msg = f"Missing called symbols: {', '.join(missing_symbols)}"
            errors.append(error_msg)
            logger.warning(
                error_msg,
                extra={
                    "stage_name": "validation",
                    "node_name": original_node.name,
                    "missing_symbols": missing_symbols
                }
            )
            return False
        
        logger.debug(
            "Symbol preservation check passed",
            extra={"stage_name": "validation", "node_name": original_node.name}
        )
        return True
    
    def _check_dependencies(
        self,
        original_node: ASTNode,
        translated_code: str,
        dependency_graph: Optional[nx.DiGraph],
        missing_deps: List[str],
        errors: List[str]
    ) -> bool:
        """Check if all dependencies are complete.
        
        Verifies that all called symbols either:
        1. Appear in the translated code, OR
        2. Are reachable in the dependency graph within CONTEXT_EXPANSION_DEPTH
        
        Args:
            original_node: Original AST node
            translated_code: Translated Python code
            dependency_graph: Optional dependency graph
            missing_deps: List to populate with missing dependencies
            errors: List to append error messages
            
        Returns:
            True if all dependencies are complete, False otherwise
        """
        if not original_node.called_symbols:
            logger.debug(
                "No dependencies to check",
                extra={"stage_name": "validation", "node_name": original_node.name}
            )
            return True
        
        # Get reachable symbols from dependency graph
        reachable_symbols: Set[str] = set()
        if dependency_graph is not None:
            reachable_symbols = self._get_reachable_symbols(
                original_node,
                dependency_graph
            )
        
        # Remove comments to avoid false positives
        code_without_comments = self._remove_comments(translated_code)
        
        # Check each called symbol
        for symbol in original_node.called_symbols:
            # Check if symbol is in translated code (excluding comments)
            pattern = r'\b' + re.escape(symbol) + r'\b'
            in_translated = bool(re.search(pattern, code_without_comments))
            
            # Check if symbol is reachable in graph
            in_graph = symbol in reachable_symbols
            
            # Symbol must be in either location
            if not (in_translated or in_graph):
                missing_deps.append(symbol)
        
        if missing_deps:
            error_msg = f"Missing dependencies: {', '.join(missing_deps)}"
            errors.append(error_msg)
            logger.warning(
                error_msg,
                extra={
                    "stage_name": "validation",
                    "node_name": original_node.name,
                    "missing_count": len(missing_deps)
                }
            )
            return False
        
        logger.debug(
            "Dependency completeness check passed",
            extra={"stage_name": "validation", "node_name": original_node.name}
        )
        return True
    
    def _check_completeness(self, translated_code: str, errors: List[str]) -> bool:
        """Check if translation is complete (no TODO/pass/NotImplemented markers).
        
        Args:
            translated_code: Translated Python code
            errors: List to append error messages
            
        Returns:
            True if translation is complete, False otherwise
        """
        incomplete_markers = []
        
        # Check for TODO comments
        if re.search(r'#\s*TODO', translated_code, re.IGNORECASE):
            incomplete_markers.append("TODO")
        
        # Check for pass statements (excluding valid uses in empty classes/functions)
        # This is a simplified check - may have false positives
        if re.search(r'^\s*pass\s*$', translated_code, re.MULTILINE):
            incomplete_markers.append("pass")
        
        # Check for NotImplemented/NotImplementedError
        if re.search(r'\bNotImplemented(Error)?\b', translated_code):
            incomplete_markers.append("NotImplemented")
        
        # Check for empty function bodies (def followed by pass or nothing)
        if re.search(r'def\s+\w+\([^)]*\):\s*pass', translated_code):
            incomplete_markers.append("empty body")
        
        if incomplete_markers:
            error_msg = f"Incomplete translation markers found: {', '.join(incomplete_markers)}"
            errors.append(error_msg)
            logger.warning(
                error_msg,
                extra={"stage_name": "validation", "markers": incomplete_markers}
            )
            return False
        
        logger.debug(
            "Completeness check passed",
            extra={"stage_name": "validation"}
        )
        return True
    
    def _generate_test_stub(self, original_node: ASTNode) -> str:
        """Generate pytest-style unit test stub.
        
        Args:
            original_node: Original AST node
            
        Returns:
            Python test stub code
        """
        test_name = f"test_{original_node.name}"
        
        # Generate parameter placeholders
        param_placeholders = []
        for param in original_node.parameters:
            # Create simple placeholder based on parameter name
            if 'count' in param.lower() or 'num' in param.lower():
                param_placeholders.append("0")
            elif 'name' in param.lower() or 'str' in param.lower():
                param_placeholders.append('""')
            elif 'list' in param.lower() or 'array' in param.lower():
                param_placeholders.append("[]")
            else:
                param_placeholders.append("None")
        
        params_str = ", ".join(param_placeholders)
        
        # Generate test stub
        stub = f'''def {test_name}():
    """Test for {original_node.name}."""
    # Arrange
    # TODO: Set up test data
    
    # Act
    result = {original_node.name}({params_str})
    
    # Assert
    assert result is not None
    # TODO: Add specific assertions
'''
        
        logger.debug(
            f"Generated test stub for {original_node.name}",
            extra={"stage_name": "validation", "node_name": original_node.name}
        )
        
        return stub
    
    def _extract_parameters(
        self,
        tree: ast.AST,
        function_name: str
    ) -> Optional[List[str]]:
        """Extract parameter names from AST for a specific function.
        
        Args:
            tree: Python AST
            function_name: Name of function to find
            
        Returns:
            List of parameter names, or None if function not found
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return [arg.arg for arg in node.args.args]
            elif isinstance(node, ast.ClassDef):
                # Check methods within classes
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == function_name:
                        # Exclude 'self' or 'cls' for methods
                        params = [arg.arg for arg in item.args.args]
                        if params and params[0] in ('self', 'cls'):
                            return params[1:]
                        return params
        
        return None
    
    def _count_control_blocks(self, code: str) -> int:
        """Count control flow blocks (if/for/while) in code.
        
        Args:
            code: Source code
            
        Returns:
            Approximate count of control flow blocks
        """
        # Use regex to count control flow keywords
        # This is language-agnostic and approximate
        patterns = [
            r'\bif\b',
            r'\bfor\b',
            r'\bwhile\b',
            r'\bswitch\b',
            r'\bcase\b',
            r'\btry\b',
            r'\bcatch\b',
            r'\bexcept\b'
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, code, re.IGNORECASE))
        
        return count
    
    def _remove_comments(self, code: str) -> str:
        """Remove Python comments from code.
        
        Args:
            code: Python source code
            
        Returns:
            Code with comments removed
        """
        # Remove single-line comments
        code_without_comments = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        
        # Remove multi-line strings (docstrings) that might contain false positives
        # This is a simplified approach
        code_without_comments = re.sub(r'""".*?"""', '', code_without_comments, flags=re.DOTALL)
        code_without_comments = re.sub(r"'''.*?'''", '', code_without_comments, flags=re.DOTALL)
        
        return code_without_comments
    
    def _get_reachable_symbols(
        self,
        original_node: ASTNode,
        dependency_graph: nx.DiGraph
    ) -> Set[str]:
        """Get all symbols reachable within CONTEXT_EXPANSION_DEPTH.
        
        Uses BFS traversal to find reachable nodes in dependency graph.
        
        Args:
            original_node: Starting node
            dependency_graph: Dependency graph
            
        Returns:
            Set of reachable symbol names
        """
        # Find node ID in graph
        node_id = self._find_node_id(original_node, dependency_graph)
        if node_id is None:
            logger.debug(
                f"Node {original_node.name} not found in dependency graph",
                extra={"stage_name": "validation", "node_name": original_node.name}
            )
            return set()
        
        # BFS traversal
        reachable: Set[str] = set()
        visited: Set[str] = {node_id}
        queue = deque([(node_id, 0)])
        
        while queue:
            current_id, depth = queue.popleft()
            
            # Add current node's name to reachable set
            if current_id in dependency_graph.nodes:
                node_data = dependency_graph.nodes[current_id]
                if 'name' in node_data:
                    reachable.add(node_data['name'])
            
            # Stop if we've reached depth limit
            if depth >= self.context_expansion_depth:
                continue
            
            # Add successors (dependencies)
            for successor in dependency_graph.successors(current_id):
                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, depth + 1))
        
        logger.debug(
            f"Found {len(reachable)} reachable symbols for {original_node.name}",
            extra={
                "stage_name": "validation",
                "node_name": original_node.name,
                "reachable_count": len(reachable)
            }
        )
        
        return reachable
    
    def _find_node_id(
        self,
        original_node: ASTNode,
        dependency_graph: nx.DiGraph
    ) -> Optional[str]:
        """Find node ID in dependency graph matching original node.
        
        Args:
            original_node: AST node to find
            dependency_graph: Dependency graph
            
        Returns:
            Node ID if found, None otherwise
        """
        # Try to match by file path, name, and line number
        for node_id in dependency_graph.nodes:
            node_data = dependency_graph.nodes[node_id]
            
            if (node_data.get('name') == original_node.name and
                node_data.get('file_path') == original_node.file_path and
                node_data.get('start_line') == original_node.start_line):
                return node_id
        
        # Fallback: match by name only (less precise)
        for node_id in dependency_graph.nodes:
            node_data = dependency_graph.nodes[node_id]
            if node_data.get('name') == original_node.name:
                return node_id
        
        return None
