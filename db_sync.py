"""
db_sync.py — HF Dataset-backed SQLite persistence.

On startup : pull chartlens.db from the private HF Dataset repo.
After write: push the updated file back up.

This keeps the database alive across HF Spaces container rebuilds
at zero cost, using a private HF Dataset repo as durable storage.
"""

import logging
import os
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────

HF_TOKEN        = os.getenv("HF_TOKEN", "")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "")
DB_FILENAME     = "chartlens.db"
_DATABASE_URL   = os.getenv("DATABASE_URL", "sqlite:////data/chartlens.db")
DB_PATH         = Path(_DATABASE_URL.replace("sqlite:///", ""))
REPO_DB_PATH    = "chartlens.db"   # path inside the dataset repo

_push_lock = threading.Lock()
_enabled   = bool(HF_TOKEN and HF_DATASET_REPO)


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
    """
    Download chartlens.db from the HF Dataset repo to the local path.
    Returns True if successful, False if the file doesn't exist yet
    (first deploy) or if sync is not configured.
    """
    if not _enabled:
        logger.info("db_sync: HF_TOKEN or HF_DATASET_REPO not set — "
                    "running without remote persistence.")
        return False

    api = _get_api()
    if api is None:
        return False

    try:
        local = api.hf_hub_download(
            repo_id=HF_DATASET_REPO,
            filename=REPO_DB_PATH,
            repo_type="dataset",
            local_dir=".",
        )
        # hf_hub_download may write to a cache subdir — move to root if needed
        downloaded = Path(local)
        if downloaded.resolve() != DB_PATH.resolve():
            import shutil
            shutil.copy2(downloaded, DB_PATH)

        logger.info("db_sync: pulled %s from %s (%d bytes)",
                    DB_FILENAME, HF_DATASET_REPO, DB_PATH.stat().st_size)
        return True

    except Exception as exc:
        err = str(exc)
        if "404" in err or "not found" in err.lower() or "EntryNotFoundError" in err:
            logger.info("db_sync: no remote DB found — "
                        "fresh database will be created.")
        else:
            logger.warning("db_sync: pull failed — %s", exc)
        return False


# ── Push after writes ────────────────────────────────────────────────────────

def push_db() -> bool:
    """
    Upload the local chartlens.db to the HF Dataset repo.
    Thread-safe. Non-blocking errors — never raises.
    Returns True if successful.
    """
    if not _enabled:
        return False

    if not DB_PATH.exists():
        logger.warning("db_sync: push called but %s does not exist", DB_PATH)
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
        try:
            api.upload_file(
                path_or_fileobj=str(DB_PATH),
                path_in_repo=REPO_DB_PATH,
                repo_id=HF_DATASET_REPO,
                repo_type="dataset",
                commit_message="chore: sync chartlens.db",
            )
            logger.info("db_sync: pushed %s to %s (%d bytes)",
                        DB_FILENAME, HF_DATASET_REPO,
                        DB_PATH.stat().st_size)
            return True
        except Exception as exc:
            logger.warning("db_sync: push failed — %s", exc)
            return False


# ── Async push (fire-and-forget) ─────────────────────────────────────────────

def push_db_async() -> None:
    """Push in a background thread so web requests are not blocked."""
    t = threading.Thread(target=push_db, daemon=True)
    t.start()
