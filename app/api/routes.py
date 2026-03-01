"""API route definitions - thin transport layer only.

All routes are thin adapters that:
1. Validate input via Pydantic schemas
2. Call service layer
3. Transform service responses to API schemas
4. Return JSON-serializable responses

NO business logic, NO AST parsing, NO LLM calls, NO graph construction.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from typing import List
import tempfile
import hashlib
from pathlib import Path

from app.api.schemas import (
    UploadRepoRequest,
    UploadRepoResponse,
    FileMetadataResponse,
    TranslateRequest,
    TranslateResponse,
    TranslationModuleResult,
    ValidationSummary,
    DependencyGraphResponse,
    GraphNode,
    GraphEdge,
    ReportResponse,
    AuditCheckResult,
    AuditSummary,
    DocumentationModule,
    ErrorResponse,
)
from app.api.dependencies import (
    get_ingestion_service,
    get_graph_builder,
    get_translation_service,
    get_validation_engine,
    get_audit_engine,
    get_parser,
    get_storage,
    get_pipeline_service,
    InMemoryStorage,
)
from app.ingestion.ingestor import RepositoryIngestor, IngestionError
from app.dependency_graph.graph_builder import GraphBuilder
from app.translation.orchestrator import TranslationOrchestrator
from app.validation import ValidationEngine
from app.audit import AuditEngine
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# POST /upload_repo - Repository Upload
# ============================================================================

@router.post(
    "/upload_repo",
    response_model=UploadRepoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Upload repository for processing",
    description="Upload a ZIP file or provide path to repository for ingestion and analysis"
)
async def upload_repo(
    file: UploadFile = File(None, description="ZIP file upload"),
    ingestor: RepositoryIngestor = Depends(get_ingestion_service),
    storage: InMemoryStorage = Depends(get_storage)
) -> UploadRepoResponse:
    """Upload and ingest repository.
    
    Accepts ZIP file upload, extracts safely, and returns file metadata.
    
    Args:
        file: Uploaded ZIP file
        ingestor: Repository ingestion service
        storage: Storage service
        
    Returns:
        UploadRepoResponse with repository ID and file metadata
        
    Raises:
        HTTPException: On validation or ingestion errors
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP files are supported"
        )
    
    # Save uploaded file to temporary location
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp:
            content = await file.read()
            temp.write(content)
            temp_file = temp.name
        
        logger.info(f"Processing upload: {file.filename}")
        
        # Call ingestion service
        file_metadata_list = ingestor.ingest_zip(temp_file)
        
        # Generate repository ID from content hash
        content_hash = hashlib.sha256(content).hexdigest()
        repo_id = f"repo_{content_hash[:16]}"
        
        # Convert to response models
        files_response = [
            FileMetadataResponse(
                relative_path=fm.relative_path,
                language=fm.language,
                size=fm.size,
                sha256=fm.sha256,
                encoding=fm.encoding
            )
            for fm in file_metadata_list
        ]
        
        # Store repository data
        storage.store_repository(repo_id, {
            "file_metadata": file_metadata_list,
            "filename": file.filename,
            "content_hash": content_hash
        })
        
        logger.info(f"Repository uploaded: {repo_id}, {len(files_response)} files")
        
        return UploadRepoResponse(
            repository_id=repo_id,
            status="success",
            file_count=len(files_response),
            files=files_response,
            errors=[]
        )
        
    except IngestionError as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )
    finally:
        # Cleanup temporary file
        if temp_file and Path(temp_file).exists():
            Path(temp_file).unlink()
        # Cleanup ingestor temp directory
        ingestor.cleanup()


# ============================================================================
# POST /translate - Full Pipeline Execution
# ============================================================================

@router.post(
    "/translate",
    response_model=TranslateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Repository not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Translate repository code",
    description="Execute full translation pipeline: parse → graph → optimize → translate → validate → audit"
)
async def translate(
    request: TranslateRequest,
    storage: InMemoryStorage = Depends(get_storage),
    pipeline_service = Depends(get_pipeline_service)
) -> TranslateResponse:
    """Execute full translation pipeline using centralized PipelineService.
    
    Pipeline order:
    1. Parse AST from repository files
    2. Build dependency graph
    3. Translate code (with context optimization)
    4. Validate translations
    5. Run audit checks
    
    Args:
        request: Translation request
        storage: Storage service
        pipeline_service: Centralized pipeline service
        
    Returns:
        TranslateResponse with translation results and validation
        
    Raises:
        HTTPException: On pipeline errors
    """
    repo_id = request.repository_id
    
    # Check repository exists
    if not storage.has_repository(repo_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repo_id}"
        )
    
    repo_data = storage.get_repository(repo_id)
    file_metadata_list = repo_data["file_metadata"]
    
    # Get temporary path from first file (all files are in same temp dir)
    if not file_metadata_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files in repository"
        )
    
    # Create temporary ZIP from extracted files for pipeline
    import tempfile
    import zipfile
    
    temp_zip = None
    try:
        # Create temporary ZIP file
        temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        temp_zip_path = temp_zip.name
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip_path, 'w') as zf:
            for file_meta in file_metadata_list:
                zf.write(file_meta.path, arcname=file_meta.relative_path)
        
        logger.info(f"Starting translation pipeline for {repo_id}")
        
        # Execute centralized pipeline
        pipeline_result = await pipeline_service.execute_full_pipeline(
            repo_path=temp_zip_path,
            source_language="java",  # TODO: detect from request
            target_language=request.target_language.value,
            repository_id=repo_id
        )
        
        if not pipeline_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pipeline failed: {', '.join(pipeline_result.errors)}"
            )
        
        # Store results
        storage.store_translations(repo_id, pipeline_result.translation_results)
        storage.store_validations(repo_id, pipeline_result.validation_reports)
        storage.store_documentation(repo_id, pipeline_result.documentation)
        
        if pipeline_result.audit_report:
            storage.store_audit(repo_id, {
                "overall_passed": pipeline_result.audit_report.overall_passed,
                "total_checks": pipeline_result.audit_report.total_checks,
                "passed_checks": pipeline_result.audit_report.passed_checks,
                "failed_checks": pipeline_result.audit_report.failed_checks,
                "execution_time_ms": pipeline_result.audit_report.execution_time_ms,
                "check_results": pipeline_result.audit_report.check_results
            })
        
        # Store evaluation report
        if pipeline_result.evaluation_report:
            storage.store_evaluation(repo_id, pipeline_result.evaluation_report)
        
        # Store prompt versions
        storage.store_prompt_versions(repo_id, pipeline_result.prompt_versions)
        
        # Build response
        modules_response = []
        for i, trans_result in enumerate(pipeline_result.translation_results):
            # Get validation for this module
            validation_summary = None
            if i < len(pipeline_result.validation_reports):
                val_report = pipeline_result.validation_reports[i]
                validation_summary = ValidationSummary(
                    structure_valid=val_report.structure_valid,
                    symbols_preserved=val_report.symbols_preserved,
                    syntax_valid=val_report.syntax_valid,
                    dependencies_complete=val_report.dependencies_complete,
                    missing_dependencies=val_report.missing_dependencies,
                    error_count=len(val_report.errors)
                )
            
            modules_response.append(TranslationModuleResult(
                module_name=trans_result.module_name,
                status=trans_result.status.value,
                translated_code=trans_result.translated_code if trans_result.translated_code else None,
                dependencies_used=trans_result.dependencies_used,
                token_usage=trans_result.token_usage,
                validation=validation_summary,
                errors=trans_result.errors,
                warnings=trans_result.warnings
            ))
        
        # Calculate statistics
        statistics = {
            "total_modules": len(pipeline_result.translation_results),
            "successful": sum(1 for r in pipeline_result.translation_results if r.status.value == "success"),
            "failed": sum(1 for r in pipeline_result.translation_results if r.status.value == "failed"),
            "audit_passed": pipeline_result.audit_report.overall_passed if pipeline_result.audit_report else False,
            "validation_passed": sum(
                1 for r in pipeline_result.validation_reports
                if r.syntax_valid and r.structure_valid and r.symbols_preserved and r.dependencies_complete
            )
        }
        
        return TranslateResponse(
            repository_id=repo_id,
            status="completed",
            modules=modules_response,
            statistics=statistics,
            errors=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation pipeline failed: {str(e)}"
        )
    finally:
        # Cleanup temporary ZIP
        if temp_zip and Path(temp_zip_path).exists():
            Path(temp_zip_path).unlink()


# ============================================================================
# GET /dependency_graph - Retrieve Dependency Graph
# ============================================================================

@router.get(
    "/dependency_graph/{repository_id}",
    response_model=DependencyGraphResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Repository or graph not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Get dependency graph",
    description="Retrieve serialized dependency graph for repository"
)
async def get_dependency_graph(
    repository_id: str,
    storage: InMemoryStorage = Depends(get_storage),
    graph_builder: GraphBuilder = Depends(get_graph_builder)
) -> DependencyGraphResponse:
    """Get dependency graph for repository.
    
    Returns JSON-serializable graph with nodes and edges.
    
    Args:
        repository_id: Repository identifier
        storage: Storage service
        graph_builder: Graph builder service
        
    Returns:
        DependencyGraphResponse with nodes and edges
        
    Raises:
        HTTPException: If repository or graph not found
    """
    # Check repository exists
    if not storage.has_repository(repository_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}"
        )
    
    # Get graph data
    graph_data = storage.get_graph(repository_id)
    if not graph_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dependency graph not found for repository: {repository_id}"
        )
    
    # Convert to response models
    nodes_response = [
        GraphNode(
            id=node["id"],
            name=node["name"],
            node_type=node["node_type"],
            file_path=node["file_path"],
            start_line=node["start_line"],
            end_line=node["end_line"]
        )
        for node in graph_data["nodes"]
    ]
    
    edges_response = [
        GraphEdge(
            source=edge["source"],
            target=edge["target"],
            edge_type=edge["edge_type"]
        )
        for edge in graph_data["edges"]
    ]
    
    # Calculate statistics
    statistics = {
        "node_count": len(nodes_response),
        "edge_count": len(edges_response),
        "avg_dependencies": len(edges_response) / len(nodes_response) if nodes_response else 0
    }
    
    return DependencyGraphResponse(
        repository_id=repository_id,
        nodes=nodes_response,
        edges=edges_response,
        statistics=statistics
    )


# ============================================================================
# GET /report - Comprehensive Report
# ============================================================================

@router.get(
    "/report/{repository_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Repository not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Get comprehensive report",
    description="Retrieve validation, audit, and documentation report for repository"
)
async def get_report(
    repository_id: str,
    storage: InMemoryStorage = Depends(get_storage)
) -> ReportResponse:
    """Get comprehensive report for repository.
    
    Includes validation results, audit results, and documentation.
    
    Args:
        repository_id: Repository identifier
        storage: Storage service
        
    Returns:
        ReportResponse with all report data
        
    Raises:
        HTTPException: If repository not found
    """
    # Check repository exists
    if not storage.has_repository(repository_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}"
        )
    
    # Get validation results
    validations = storage.get_validations(repository_id) or []
    validation_summary = {
        "total_validations": len(validations),
        "passed": sum(
            1 for v in validations
            if v.syntax_valid and v.structure_valid and v.symbols_preserved and v.dependencies_complete
        ),
        "failed": sum(
            1 for v in validations
            if not (v.syntax_valid and v.structure_valid and v.symbols_preserved and v.dependencies_complete)
        )
    }
    
    # Get audit results
    audit_data = storage.get_audit(repository_id)
    audit_summary = None
    if audit_data:
        check_results = [
            AuditCheckResult(
                check_name=check.check_name,
                passed=check.passed,
                message=check.message,
                warnings=check.warnings
            )
            for check in audit_data["check_results"]
        ]
        
        audit_summary = AuditSummary(
            overall_passed=audit_data["overall_passed"],
            total_checks=audit_data["total_checks"],
            passed_checks=audit_data["passed_checks"],
            failed_checks=audit_data["failed_checks"],
            execution_time_ms=audit_data["execution_time_ms"],
            check_results=check_results
        )
    
    # Get documentation
    docs = storage.get_documentation(repository_id) or {}
    documentation_response = [
        DocumentationModule(
            module_name=module_name,
            documentation=doc_content
        )
        for module_name, doc_content in docs.items()
    ]
    
    # Get translations for statistics
    translations = storage.get_translations(repository_id) or []
    
    # Get evaluation report
    evaluation = storage.get_evaluation(repository_id)
    
    # Get prompt versions
    prompt_versions = storage.get_prompt_versions(repository_id)
    
    statistics = {
        "total_modules": len(translations),
        "total_validations": len(validations),
        "documentation_count": len(documentation_response),
        "audit_passed": audit_data["overall_passed"] if audit_data else False,
        "evaluation": evaluation if evaluation else None,
        "prompt_versions": prompt_versions if prompt_versions else {}
    }
    
    return ReportResponse(
        repository_id=repository_id,
        validation_summary=validation_summary,
        audit_summary=audit_summary,
        documentation=documentation_response,
        statistics=statistics
    )
