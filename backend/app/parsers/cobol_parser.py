"""COBOL language parser."""
from typing import List, Optional, Set
from .base import BaseParser, ASTNode
from .registry import register_parser
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


@register_parser('cobol')
class CobolParser(BaseParser):
    """Parser for COBOL source code with mock AST generation."""
    
    def __init__(self):
        """Initialize COBOL parser."""
        super().__init__()
    
    def supports_language(self) -> str:
        """Return supported language."""
        return "cobol"
    
    def parse_file(self, file_path: str) -> List[ASTNode]:
        """Parse COBOL file into normalized AST nodes.

        One node per PROGRAM-ID (or one node for the whole file if none found).
        raw_source is the full file content so the LLM has everything it needs.
        """
        logger.info(
            f"Starting COBOL parse: {file_path}",
            extra={"stage_name": "ast_parsing", "language": "cobol", "file_path": file_path}
        )

        try:
            content = self._read_file_safely(file_path)
            if content is None:
                return []

            nodes = []
            content_upper = content.upper()
            total_lines = len(content.splitlines())

            call_pattern = r'CALL\s+["\'](\w+)["\']'
            perform_pattern = r'PERFORM\s+([\w-]+)'
            called_programs = set(re.findall(call_pattern, content_upper))
            performed_paragraphs = set(re.findall(perform_pattern, content_upper))
            all_dependencies = list(called_programs | performed_paragraphs)

            program_pattern = r'PROGRAM-ID\.\s+([\w-]+)'
            program_matches = list(re.finditer(program_pattern, content_upper))

            if program_matches:
                for match in program_matches:
                    program_name = match.group(1)
                    start_line = content[:match.start()].count('\n') + 1
                    node = ASTNode(
                        id=f"{file_path}:{program_name}:{start_line}",
                        name=program_name,
                        node_type="program",
                        parameters=[],
                        return_type=None,
                        called_symbols=all_dependencies,
                        imports=[],
                        file_path=file_path,
                        start_line=1,
                        end_line=total_lines,
                        raw_source=content,
                    )
                    nodes.append(node)
            else:
                filename = file_path.replace('\\', '/').split('/')[-1]
                prog_name = re.sub(r'[^A-Z0-9_-]', '_', filename.upper().split('.')[0])
                node = ASTNode(
                    id=f"{file_path}:{prog_name}:1",
                    name=prog_name,
                    node_type="program",
                    parameters=[],
                    return_type=None,
                    called_symbols=all_dependencies,
                    imports=[],
                    file_path=file_path,
                    start_line=1,
                    end_line=total_lines,
                    raw_source=content,
                )
                nodes.append(node)

            logger.info(
                f"Completed COBOL parse: {file_path} ({len(nodes)} nodes extracted)",
                extra={"stage_name": "ast_parsing", "language": "cobol", "file_path": file_path, "node_count": len(nodes)}
            )
            return nodes

        except Exception as e:
            logger.error(
                f"Error parsing COBOL file {file_path}: {e}",
                extra={"stage_name": "ast_parsing", "language": "cobol", "file_path": file_path, "error": str(e)}
            )
            return []

    
    def extract_dependencies(self, nodes: List[ASTNode]) -> List[str]:
        """Extract dependencies from COBOL AST nodes.
        
        Args:
            nodes: List of ASTNode objects
            
        Returns:
            List of unique called programs
        """
        dependencies = set()
        for node in nodes:
            dependencies.update(node.called_symbols)
        return sorted(list(dependencies))
