"""Persistent storage for pipeline run history.

Saves pipeline_runs to a JSON file so history survives backend restarts.
Thread-safe with a lock around all file I/O.
"""

import json
import threading
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

_HISTORY_FILE = Path(__file__).parent.parent.parent / "data" / "run_history.json"
_lock = threading.Lock()


def _ensure_dir():
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_history() -> Dict[str, Any]:
    """Load all run history from disk. Returns empty dict if file missing."""
    _ensure_dir()
    with _lock:
        if not _HISTORY_FILE.exists():
            return {}
        try:
            return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not load run history: {e}")
            return {}


def save_run(run_id: str, run_data: Dict[str, Any]) -> None:
    """Persist a single run entry to disk."""
    _ensure_dir()
    with _lock:
        try:
            history = {}
            if _HISTORY_FILE.exists():
                try:
                    history = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
                except Exception:
                    history = {}

            # Store a summary (not the full result blob — keep it lean)
            history[run_id] = _summarise(run_id, run_data)

            # Atomic write via temp file
            tmp = _HISTORY_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(history, indent=2, default=str), encoding="utf-8")
            shutil.move(str(tmp), str(_HISTORY_FILE))
        except Exception as e:
            logger.error(f"Could not save run history: {e}")


def delete_run(run_id: str) -> None:
    """Remove a run from history."""
    _ensure_dir()
    with _lock:
        try:
            if not _HISTORY_FILE.exists():
                return
            history = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
            history.pop(run_id, None)
            _HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.error(f"Could not delete run from history: {e}")


def _summarise(run_id: str, run_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a lean summary suitable for the history list."""
    result = run_data.get("result") or {}
    return {
        "run_id": run_id,
        "repo_id": run_data.get("repo_id", ""),
        "repo_name": run_data.get("repo_name", ""),
        "source_language": run_data.get("source_language", "unknown"),
        "target_language": run_data.get("target_language", "python"),
        "status": run_data.get("status", "UNKNOWN"),
        "phase": run_data.get("phase", ""),
        "started_at": run_data.get("started_at", ""),
        "completed_at": run_data.get("completed_at", ""),
        "files_processed": result.get("files_processed", 0),
        "success_rate": round(result.get("success_rate", 0) * 100, 1),
        "token_reduction": result.get("token_reduction", 0),
        "has_artifacts": bool(result.get("output_path")),
        "error": run_data.get("error"),
    }
