"""Java language parser."""
from typing import List
from .base import BaseParser, ASTNode
from .registry import register_parser
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


@register_parser('java')
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
            
            lines = content.splitlines()
            total_lines = len(lines)

            # Extract class definitions — one node per class, raw_source = full class body
            class_pattern = r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)'
            class_matches = list(re.finditer(class_pattern, content))

            for i, match in enumerate(class_matches):
                class_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1

                # Determine end line: next class start or EOF
                if i + 1 < len(class_matches):
                    end_line = content[:class_matches[i + 1].start()].count('\n')
                else:
                    end_line = total_lines

                raw = "\n".join(lines[start_line - 1:end_line])

                node = ASTNode(
                    id=f"{file_path}:{class_name}:{start_line}",
                    name=class_name,
                    node_type="class",
                    parameters=[],
                    return_type=None,
                    called_symbols=[],
                    imports=imports,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    raw_source=raw,
                )
                nodes.append(node)

            # If no classes found, treat the whole file as one node
            if not nodes:
                node = ASTNode(
                    id=f"{file_path}:module:1",
                    name=re.sub(r'[^\w]', '_', file_path.split('/')[-1].replace('.java', '')),
                    node_type="module",
                    parameters=[],
                    return_type=None,
                    called_symbols=[],
                    imports=imports,
                    file_path=file_path,
                    start_line=1,
                    end_line=total_lines,
                    raw_source=content,
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
