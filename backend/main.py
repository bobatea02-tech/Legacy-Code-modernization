#!/usr/bin/env python3
"""Main entry point for the legacy modernizer."""
import sys
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn


def main() -> None:
    """Start the FastAPI application."""
    uvicorn.run(
        "app.api.main:app",  # Import string for reload support
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND_DIR)]  # Watch backend directory for changes
    )


if __name__ == "__main__":
    main()
