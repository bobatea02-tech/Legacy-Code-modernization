"""Automatic cleanup of temporary files older than TTL.

Runs as a background asyncio task. Cleans:
- /tmp/modernize_outputs/{run_id}/   — output artifact directories
- /tmp/modernize_uploads/            — uploaded ZIP files

Default TTL: 24 hours.
"""

import asyncio
import shutil
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

TTL_HOURS = 24
CLEANUP_INTERVAL_SECONDS = 3600  # run every hour


async def cleanup_loop():
    """Background task: periodically delete old temp files."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        try:
            _cleanup_outputs()
            _cleanup_uploads()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def _cleanup_outputs():
    """Delete output directories older than TTL."""
    outputs_root = Path(tempfile.gettempdir()) / "modernize_outputs"
    if not outputs_root.exists():
        return

    cutoff = datetime.now(timezone.utc) - timedelta(hours=TTL_HOURS)
    removed = 0

    for run_dir in outputs_root.iterdir():
        if not run_dir.is_dir():
            continue
        try:
            mtime = datetime.fromtimestamp(run_dir.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                shutil.rmtree(run_dir, ignore_errors=True)
                removed += 1
        except Exception:
            pass

    if removed:
        logger.info(f"Cleanup: removed {removed} output directories older than {TTL_HOURS}h")


def _cleanup_uploads():
    """Delete uploaded ZIPs older than TTL."""
    uploads_root = Path(tempfile.gettempdir()) / "modernize_uploads"
    if not uploads_root.exists():
        return

    cutoff = datetime.now(timezone.utc) - timedelta(hours=TTL_HOURS)
    removed = 0

    for f in uploads_root.iterdir():
        if not f.is_file():
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                f.unlink(missing_ok=True)
                removed += 1
        except Exception:
            pass

    if removed:
        logger.info(f"Cleanup: removed {removed} uploaded ZIPs older than {TTL_HOURS}h")
