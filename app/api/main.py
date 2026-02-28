"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Legacy Code Modernization Engine",
    description="AI-powered code translation pipeline with deterministic validation and audit",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["Translation Pipeline"])


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
