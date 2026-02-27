"""Java language parser."""
from typing import List
from .base import BaseParser, ASTNode
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class JavaParser(BaseParser):
    """Parser for Java source code with mock AST generation."""
    
    def __init__(self):
        """Initialize Java parser."""
        super().__init__()
    
    def supports_language(self) -> str:
        """Return supported language."""
        return "java"
    
    def parse_file(self, file_path: str) -> List[ASTNode]:
        """Parse Java file into normalized AST nodes.
        
        Args:
            file_path: Path to Java source file
            
        Returns:
            List of mock ASTNode objects
        """
        logger.info(
            f"Starting Java parse: {file_path}",
            extra={"stage_name": "ast_parsing", "language": "java", "file_path": file_path}
        )
        
        try:
            content = self._read_file_safely(file_path)
            if content is None:
                return []
            
            nodes = []
            
            # Mock parsing: Extract basic patterns
            # Extract imports
            imports = re.findall(r'import\s+([\w.]+);', content)
            
            # Extract class definitions
            class_pattern = r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1
                
                node = ASTNode(
                    id=f"{file_path}::{class_name}",
                    name=class_name,
                    node_type="class",
                    parameters=[],
                    return_type=None,
                    called_symbols=[],
                    imports=imports,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=start_line + 10,  # Mock end line
                    raw_source=match.group(0)
                )
                nodes.append(node)
            
            # Extract method definitions
            method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(\w+)\s+(\w+)\s*\((.*?)\)'
            for match in re.finditer(method_pattern, content):
                return_type = match.group(1)
                method_name = match.group(2)
                params = match.group(3)
                start_line = content[:match.start()].count('\n') + 1
                
                # Parse parameters
                param_list = [p.strip() for p in params.split(',') if p.strip()]
                
                node = ASTNode(
                    id=f"{file_path}::{method_name}",
                    name=method_name,
                    node_type="method",
                    parameters=param_list,
                    return_type=return_type if return_type != "void" else None,
                    called_symbols=[],
                    imports=imports,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=start_line + 5,  # Mock end line
                    raw_source=match.group(0)
                )
                nodes.append(node)
            
            logger.info(
                f"Completed Java parse: {file_path} ({len(nodes)} nodes extracted)",
                extra={"stage_name": "ast_parsing", "language": "java", "file_path": file_path, "node_count": len(nodes)}
            )
            return nodes
            
        except Exception as e:
            logger.error(
                f"Error parsing Java file {file_path}: {e}",
                extra={"stage_name": "ast_parsing", "language": "java", "file_path": file_path, "error": str(e)}
            )
            return []
    
    def extract_dependencies(self, nodes: List[ASTNode]) -> List[str]:
        """Extract dependencies from Java AST nodes.
        
        Args:
            nodes: List of ASTNode objects
            
        Returns:
            List of unique import statements
        """
        dependencies = set()
        for node in nodes:
            dependencies.update(node.imports)
            dependencies.update(node.called_symbols)
        return sorted(list(dependencies))
