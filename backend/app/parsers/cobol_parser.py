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
        
        Extracts PROGRAM-ID, SECTION, and paragraph definitions.
        Captures CALL and PERFORM statements as dependencies.
        
        Args:
            file_path: Path to COBOL source file
            
        Returns:
            List of ASTNode objects with complete schema
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
            
            # COBOL is case-insensitive, normalize to uppercase for pattern matching
            content_upper = content.upper()
            
            # Extract all CALL statements (external program dependencies)
            call_pattern = r'CALL\s+["\'](\w+)["\']'
            called_programs = set(re.findall(call_pattern, content_upper))
            
            # Extract all PERFORM statements (internal paragraph dependencies)
            perform_pattern = r'PERFORM\s+([\w-]+)'
            performed_paragraphs = set(re.findall(perform_pattern, content_upper))
            
            # Extract PROGRAM-ID
            program_pattern = r'PROGRAM-ID\.\s+([\w-]+)'
            for match in re.finditer(program_pattern, content_upper):
                program_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1
                
                # Combine all dependencies for program node
                all_dependencies = list(called_programs | performed_paragraphs)
                
                node = ASTNode(
                    id=f"{file_path}:{program_name}:{start_line}",
                    name=program_name,
                    node_type="program",
                    parameters=[],
                    return_type=None,
                    called_symbols=all_dependencies,
                    imports=[],
                    file_path=file_path,
                    start_line=start_line,
                    end_line=start_line + 1,
                    raw_source=match.group(0)
                )
                nodes.append(node)
            
            # Extract SECTION definitions
            section_pattern = r'([\w-]+)\s+SECTION'
            for match in re.finditer(section_pattern, content_upper):
                section_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1
                
                node = ASTNode(
                    id=f"{file_path}:{section_name}:{start_line}",
                    name=section_name,
                    node_type="section",
                    parameters=[],
                    return_type=None,
                    called_symbols=list(called_programs),
                    imports=[],
                    file_path=file_path,
                    start_line=start_line,
                    end_line=start_line + 1,
                    raw_source=match.group(0)
                )
                nodes.append(node)
            
            # Extract paragraph definitions with their local PERFORM dependencies
            paragraph_pattern = r'^[\s]*([\w-]+)\.\s*$'
            cobol_keywords = {
                'IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE',
                'WORKING-STORAGE', 'FILE', 'LINKAGE', 'CONFIGURATION',
                'INPUT-OUTPUT', 'FILE-CONTROL', 'DIVISION', 'SECTION'
            }
            
            for match in re.finditer(paragraph_pattern, content_upper, re.MULTILINE):
                para_name = match.group(1)
                
                # Skip COBOL division/section keywords
                if para_name in cobol_keywords:
                    continue
                
                start_line = content[:match.start()].count('\n') + 1
                
                # Extract PERFORM calls within this paragraph's scope
                # Find paragraph body (from current match to next paragraph or end)
                para_start = match.end()
                next_para_match = re.search(paragraph_pattern, content_upper[para_start:], re.MULTILINE)
                para_end = para_start + next_para_match.start() if next_para_match else len(content_upper)
                para_body = content_upper[para_start:para_end]
                
                # Find PERFORM statements in this paragraph
                local_performs = set(re.findall(perform_pattern, para_body))
                
                # Find CALL statements in this paragraph
                local_calls = set(re.findall(call_pattern, para_body))
                
                # Combine local dependencies
                local_dependencies = list(local_performs | local_calls)
                
                node = ASTNode(
                    id=f"{file_path}:{para_name}:{start_line}",
                    name=para_name,
                    node_type="paragraph",
                    parameters=[],
                    return_type=None,
                    called_symbols=local_dependencies,
                    imports=[],
                    file_path=file_path,
                    start_line=start_line,
                    end_line=start_line + 1,
                    raw_source=match.group(0)
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
