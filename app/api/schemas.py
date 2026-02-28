"""Pydantic schemas for API request/response models.

All API data transfer objects are defined here with strict typing
and validation. No business logic - pure data models only.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class LanguageType(str, Enum):
    """Supported source languages."""
    JAVA = "java"
    COBOL = "cobol"
    C = "c"


class TargetLanguage(str, Enum):
    """Supported target languages."""
    PYTHON = "python"


# ============================================================================
# Upload Repository Schemas
# ============================================================================

class UploadRepoRequest(BaseModel):
    """Request model for repository upload."""
    
    repo_path: Optional[str] = Field(
        None,
        description="Path to local repository or ZIP file",
        max_length=500
    )
    
    @field_validator('repo_path')
    @classmethod
    def validate_repo_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate repository path."""
        if v and len(v.strip()) == 0:
            raise ValueError("repo_path cannot be empty string")
        return v


class FileMetadataResponse(BaseModel):
    """Response model for file metadata."""
    
    relative_path: str = Field(..., description="Relative path within repository")
    language: str = Field(..., description="Detected language")
    size: int = Field(..., description="File size in bytes", ge=0)
    sha256: str = Field(..., description="SHA256 hash of file content")
    encoding: str = Field(..., description="File encoding")


class UploadRepoResponse(BaseModel):
    """Response model for repository upload."""
    
    repository_id: str = Field(..., description="Unique repository identifier")
    status: str = Field(..., description="Ingestion status")
    file_count: int = Field(..., description="Number of files ingested", ge=0)
    files: List[FileMetadataResponse] = Field(
        default_factory=list,
        description="List of ingested file metadata"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of ingestion errors"
    )


# ============================================================================
# Translation Schemas
# ============================================================================

class TranslateRequest(BaseModel):
    """Request model for code translation."""
    
    repository_id: str = Field(
        ...,
        description="Repository identifier from upload",
        min_length=1,
        max_length=100
    )
    target_language: TargetLanguage = Field(
        default=TargetLanguage.PYTHON,
        description="Target programming language"
    )
    source_language: Optional[LanguageType] = Field(
        None,
        description="Source language (auto-detected if not provided)"
    )


class ValidationSummary(BaseModel):
    """Summary of validation results."""
    
    structure_valid: bool = Field(..., description="Structure preservation check")
    symbols_preserved: bool = Field(..., description="Symbol preservation check")
    syntax_valid: bool = Field(..., description="Syntax validation check")
    dependencies_complete: bool = Field(..., description="Dependency completeness check")
    missing_dependencies: List[str] = Field(
        default_factory=list,
        description="List of missing dependencies"
    )
    error_count: int = Field(..., description="Number of validation errors", ge=0)


class TranslationModuleResult(BaseModel):
    """Result for a single translated module."""
    
    module_name: str = Field(..., description="Module identifier")
    status: str = Field(..., description="Translation status")
    translated_code: Optional[str] = Field(
        None,
        description="Translated Python code"
    )
    dependencies_used: List[str] = Field(
        default_factory=list,
        description="Dependencies included in translation"
    )
    token_usage: int = Field(default=0, description="Token usage", ge=0)
    validation: Optional[ValidationSummary] = Field(
        None,
        description="Validation results"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Translation errors"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Translation warnings"
    )


class TranslateResponse(BaseModel):
    """Response model for code translation."""
    
    repository_id: str = Field(..., description="Repository identifier")
    status: str = Field(..., description="Overall translation status")
    modules: List[TranslationModuleResult] = Field(
        default_factory=list,
        description="Translation results per module"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Translation statistics"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Pipeline errors"
    )


# ============================================================================
# Dependency Graph Schemas
# ============================================================================

class GraphNode(BaseModel):
    """Dependency graph node."""
    
    id: str = Field(..., description="Node identifier")
    name: str = Field(..., description="Node name")
    node_type: str = Field(..., description="Node type (function, class, etc.)")
    file_path: str = Field(..., description="Source file path")
    start_line: int = Field(..., description="Start line number", ge=1)
    end_line: int = Field(..., description="End line number", ge=1)


class GraphEdge(BaseModel):
    """Dependency graph edge."""
    
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    edge_type: str = Field(..., description="Edge type (calls, imports)")


class DependencyGraphResponse(BaseModel):
    """Response model for dependency graph."""
    
    repository_id: str = Field(..., description="Repository identifier")
    nodes: List[GraphNode] = Field(
        default_factory=list,
        description="Graph nodes"
    )
    edges: List[GraphEdge] = Field(
        default_factory=list,
        description="Graph edges"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Graph statistics"
    )


# ============================================================================
# Report Schemas
# ============================================================================

class AuditCheckResult(BaseModel):
    """Individual audit check result."""
    
    check_name: str = Field(..., description="Name of the check")
    passed: bool = Field(..., description="Whether check passed")
    message: str = Field(..., description="Check result message")
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-critical warnings"
    )


class AuditSummary(BaseModel):
    """Audit report summary."""
    
    overall_passed: bool = Field(..., description="Overall audit status")
    total_checks: int = Field(..., description="Total number of checks", ge=0)
    passed_checks: int = Field(..., description="Number of passed checks", ge=0)
    failed_checks: int = Field(..., description="Number of failed checks", ge=0)
    execution_time_ms: float = Field(..., description="Execution time in ms", ge=0)
    check_results: List[AuditCheckResult] = Field(
        default_factory=list,
        description="Individual check results"
    )


class DocumentationModule(BaseModel):
    """Documentation for a single module."""
    
    module_name: str = Field(..., description="Module name")
    documentation: str = Field(..., description="Generated documentation")


class ReportResponse(BaseModel):
    """Response model for comprehensive report."""
    
    repository_id: str = Field(..., description="Repository identifier")
    validation_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Validation summary"
    )
    audit_summary: Optional[AuditSummary] = Field(
        None,
        description="Audit summary"
    )
    documentation: List[DocumentationModule] = Field(
        default_factory=list,
        description="Generated documentation"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Overall statistics"
    )


# ============================================================================
# Error Response Schema
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
