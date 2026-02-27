"""COBOL language parser."""
from typing import List
from .base import BaseParser, ASTNode
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


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
        
        Args:
            file_path: Path to COBOL source file
            
        Returns:
            List of mock ASTNode objects
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
            
            # Mock parsing: Extract basic COBOL patterns
            # COBOL is case-insensitive, normalize to uppercase
            content_upper = content.upper()
            
            # Extract PROGRAM-ID
            program_pattern = r'PROGRAM-ID\.\s+(\w+)'
            for match in re.finditer(program_pattern, content_upper):
                program_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1
                
                node = ASTNode(
                    id=f"{file_path}::{program_name}",
                    name=program_name,
                    node_type="program",
                    parameters=[],
                    return_type=None,
                    called_symbols=[],
                    imports=[],
                    file_path=file_path,
                    start_line=start_line,
                    end_line=start_line + 1,
                    raw_source=match.group(0)
                )
                nodes.append(node)
            
            # Extract CALL statements (dependencies)
            call_pattern = r'CALL\s+["\'](\w+)["\']'
            called_programs = re.findall(call_pattern, content_upper)
            
            # Extract SECTION definitions
            section_pattern = r'(\w+)\s+SECTION'
            for match in re.finditer(section_pattern, content_upper):
                section_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1
                
                node = ASTNode(
                    id=f"{file_path}::{section_name}",
                    name=section_name,
                    node_type="section",
                    parameters=[],
                    return_type=None,
                    called_symbols=called_programs,
                    imports=[],
                    file_path=file_path,
                    start_line=start_line,
                    end_line=start_line + 1,
                    raw_source=match.group(0)
                )
                nodes.append(node)
            
            # Extract paragraph definitions
            paragraph_pattern = r'^[\s]*(\w+)\.\s*$'
            for match in re.finditer(paragraph_pattern, content_upper, re.MULTILINE):
                para_name = match.group(1)
                # Skip COBOL keywords
                if para_name in ['IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE', 
                                'WORKING-STORAGE', 'FILE', 'LINKAGE']:
                    continue
                    
                start_line = content[:match.start()].count('\n') + 1
                
                node = ASTNode(
                    id=f"{file_path}::{para_name}",
                    name=para_name,
                    node_type="paragraph",
                    parameters=[],
                    return_type=None,
                    called_symbols=[],
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
