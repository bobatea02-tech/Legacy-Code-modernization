"""Centralized logging module using loguru.

This module provides a configured logger instance with:
- Console and file logging
- Configurable log levels from settings
- Structured logging with contextual fields
- Automatic log directory creation
- Singleton pattern to prevent duplicate handlers
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import get_settings

# Global flag to ensure configuration runs only once
_LOGGER_CONFIGURED = False


def _configure_logger() -> None:
    """Configure loguru logger with console and file handlers.
    
    This function:
    - Removes default handlers
    - Adds console handler with colored output
    - Adds file handler with rotation
    - Sets log level from settings
    - Creates logs directory if missing
    
    Runs only once per application lifecycle.
    """
    global _LOGGER_CONFIGURED
    
    if _LOGGER_CONFIGURED:
        return
    
    settings = get_settings()
    
    # Remove default handler to prevent duplicates
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    # Define log format with required fields
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Add console handler with colors
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler with rotation
    logger.add(
        log_dir / "app.log",
        format=log_format,
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
    
    _LOGGER_CONFIGURED = True
    logger.info(f"Logger configured with level: {settings.LOG_LEVEL}")


def get_logger(name: str):
    """Get a logger instance for the specified module.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Configured logger instance with contextual binding
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
        >>> logger.bind(request_id="123", stage_name="parsing").info("Stage complete")
    """
    _configure_logger()
    return logger.bind(module=name)


# Convenience function for structured logging with context
def log_with_context(
    logger_instance,
    level: str,
    message: str,
    token_usage: Optional[int] = None,
    stage_name: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs,
) -> None:
    """Log a message with optional contextual fields.
    
    Args:
        logger_instance: Logger instance from get_logger()
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        token_usage: Optional token usage count
        stage_name: Optional pipeline stage name
        request_id: Optional request identifier
        **kwargs: Additional contextual fields
    
    Example:
        >>> logger = get_logger(__name__)
        >>> log_with_context(
        ...     logger,
        ...     "info",
        ...     "Translation complete",
        ...     token_usage=1500,
        ...     stage_name="translation",
        ...     request_id="req-123"
        ... )
    """
    context = {}
    
    if token_usage is not None:
        context["token_usage"] = token_usage
    
    if stage_name is not None:
        context["stage_name"] = stage_name
    
    if request_id is not None:
        context["request_id"] = request_id
    
    # Add any additional context fields
    context.update(kwargs)
    
    # Bind context and log
    bound_logger = logger_instance.bind(**context) if context else logger_instance
    log_method = getattr(bound_logger, level.lower())
    log_method(message)
