#!/usr/bin/env python3
"""Main entry point for the legacy modernizer."""
import uvicorn
from app.api.main import app


def main() -> None:
    """Start the FastAPI application."""
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()
