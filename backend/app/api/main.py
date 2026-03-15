"""FastAPI application entry point."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.logging import get_logger

logger = get_logger(__name__)

# Get allowed origins from environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app = FastAPI(
    title="Legacy Code Modernization Engine",
    description="AI-powered code translation pipeline with deterministic validation and audit",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["Translation Pipeline"])

# Include new pipeline routes for frontend integration
from app.api.pipeline_routes import router as pipeline_router
app.include_router(pipeline_router, prefix="/api", tags=["Pipeline"])

# Mount pipeline WebSocket routes under /api/v1 so the frontend path
# /api/v1/pipeline/{run_id}/ws resolves correctly
app.include_router(pipeline_router, prefix="/api/v1", tags=["Pipeline WS"], include_in_schema=False)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "service": "legacy-code-modernization-engine",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "api": "operational",
            "validation": "operational",
            "audit": "operational"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Legacy Code Modernization Engine starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Legacy Code Modernization Engine shutting down")
