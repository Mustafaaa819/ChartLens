"""
db_sync.py — HF Dataset-backed SQLite persistence.

On startup : pull chartlens.db from the private HF Dataset repo.
After write: push the updated file back up (synchronous, with retry).
"""

import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────

HF_TOKEN        = os.getenv("HF_TOKEN", "")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "")
DB_FILENAME     = "chartlens.db"
REPO_DB_PATH    = "chartlens.db"   # path inside the dataset repo

_push_lock = threading.Lock()
_enabled   = bool(HF_TOKEN and HF_DATASET_REPO)


def _get_db_path() -> Path:
    """Derive the local DB file path from app settings — same source SQLAlchemy uses.

    Called at runtime (not module import time) so pydantic-settings has already
    loaded .env and the result is guaranteed to match the SQLAlchemy engine path.
    """
    from config import get_settings
    url = get_settings().DATABASE_URL
    # sqlite:///./foo.db      →  ./foo.db    (relative to working dir)
    # sqlite:////data/foo.db  →  /data/foo.db  (absolute — HF Spaces persistent volume)
    return Path(url.replace("sqlite:///", ""))


def _get_api():
    """Return an authenticated HfApi instance, or None if not configured."""
    if not _enabled:
        return None
    try:
        from huggingface_hub import HfApi
        return HfApi(token=HF_TOKEN)
    except Exception as exc:
        logger.warning("db_sync: huggingface_hub not available — %s", exc)
        return None


# ── Pull on startup ─────────────────────────────────────────────────────────

def pull_db() -> bool:
    """Download chartlens.db from the HF Dataset repo to the local path.

    Returns True if successful, False if the file doesn't exist yet (first
    deploy) or if sync is not configured.
    """
    if not _enabled:
        logger.info("db_sync: HF_TOKEN or HF_DATASET_REPO not set — "
                    "running without remote persistence.")
        return False

    api = _get_api()
    if api is None:
        return False

    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("db_sync: pulling to %s", db_path.resolve())

    try:
        local = api.hf_hub_download(
            repo_id=HF_DATASET_REPO,
            filename=REPO_DB_PATH,
            repo_type="dataset",
            local_dir=str(db_path.parent),
        )
        downloaded = Path(local)
        if downloaded.resolve() != db_path.resolve():
            import shutil
            shutil.copy2(downloaded, db_path)

        logger.info("db_sync: pulled %s from %s (%d bytes)",
                    DB_FILENAME, HF_DATASET_REPO, db_path.stat().st_size)
        return True

    except Exception as exc:
        err = str(exc)
        if "404" in err or "not found" in err.lower() or "EntryNotFoundError" in err:
            logger.info("db_sync: no remote DB found — fresh database will be created.")
        else:
            logger.warning("db_sync: pull failed — %s", exc)
        return False


# ── Push after writes ────────────────────────────────────────────────────────

def push_db() -> bool:
    """Upload the local chartlens.db to the HF Dataset repo.

    Synchronous. Thread-safe. Retries up to 3 attempts with 2-second waits.
    Returns True if the push succeeded, False otherwise (never raises).
    """
    if not _enabled:
        return False

    db_path = _get_db_path()
    if not db_path.exists():
        logger.warning("db_sync: push called but %s does not exist", db_path)
        return False

    api = _get_api()
    if api is None:
        return False

    try:
        from models.database import engine
        engine.dispose()
    except Exception as exc:
        logger.warning("db_sync: engine.dispose() failed — %s", exc)

    with _push_lock:
        for attempt in range(1, 4):
            try:
                api.upload_file(
                    path_or_fileobj=str(db_path),
                    path_in_repo=REPO_DB_PATH,
                    repo_id=HF_DATASET_REPO,
                    repo_type="dataset",
                    commit_message="chore: sync chartlens.db",
                )
                logger.info("db_sync: pushed %s to %s (%d bytes)",
                            DB_FILENAME, HF_DATASET_REPO, db_path.stat().st_size)
                return True
            except Exception as exc:
                logger.warning("db_sync: push attempt %d/3 failed — %s", attempt, exc)
                if attempt < 3:
                    time.sleep(2)

        logger.error("db_sync: all 3 push attempts failed — DB not saved remotely")
        return False
