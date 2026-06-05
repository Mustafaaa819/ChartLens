"""PDF extraction utilities — PyMuPDF text and metadata extraction."""
import logging
from pathlib import Path

import fitz  # PyMuPDF

from config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Error message constants — exact wording required by Section 12
# ---------------------------------------------------------------------------

_ERR_INVALID_PDF = "Invalid or corrupted PDF file"
_ERR_SCANNED_PDF = "This PDF appears to be scanned. Scanned PDF support coming soon."
_ERR_PAGE_LIMIT = "PDF exceeds 500 page limit for MVP"
_ERR_SIZE_LIMIT = "File exceeds {limit}MB upload limit"

# Pages to sample when probing for extractable text (spread across document)
_SCAN_SAMPLE_SIZE = 20


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sample_indices(total: int, n: int) -> list[int]:
    """Return up to n page indices spread evenly across total pages."""
    if total <= n:
        return list(range(total))
    step = total // n
    return [i * step for i in range(n)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_pdf(file_path: Path) -> dict:
    """Validate a PDF file before any processing begins.

    Checks file existence, size limit, page count limit, and that the PDF
    contains extractable text (rules out scanned-only documents).
    Never raises — always returns a result dict.

    Args:
        file_path: Absolute path to the candidate PDF file.

    Returns:
        Success: {"valid": True, "page_count": int, "file_size_mb": float}
        Failure: {"valid": False, "error": str}
    """
    file_path = Path(file_path)
    settings = get_settings()

    if not file_path.exists():
        return {"valid": False, "error": _ERR_INVALID_PDF}

    file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        return {
            "valid": False,
            "error": _ERR_SIZE_LIMIT.format(limit=settings.MAX_UPLOAD_SIZE_MB),
        }

    try:
        doc = fitz.open(str(file_path))
    except Exception as exc:
        logger.error("fitz.open failed for '%s': %s", file_path.name, exc)
        return {"valid": False, "error": _ERR_INVALID_PDF}

    try:
        page_count = len(doc)
        if page_count > settings.MAX_PAGES_MVP:
            return {"valid": False, "error": _ERR_PAGE_LIMIT}

        indices = _sample_indices(page_count, _SCAN_SAMPLE_SIZE)
        has_text = any(bool(doc[i].get_text("text").strip()) for i in indices)
        if not has_text:
            return {"valid": False, "error": _ERR_SCANNED_PDF}

        return {"valid": True, "page_count": page_count, "file_size_mb": file_size_mb}
    except Exception as exc:
        logger.error("Validation error for '%s': %s", file_path.name, exc)
        return {"valid": False, "error": _ERR_INVALID_PDF}
    finally:
        doc.close()


def extract_text_by_page(file_path: Path) -> list[dict]:
    """Extract plain text from every page of a PDF.

    Pages with no text are still included (empty string, char_count 0) so
    downstream chunking always has a contiguous 1-indexed page list.
    Never logs page text — patient data must not appear in logs (Section 13).

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        [{"page_number": int, "text": str, "char_count": int}, ...]
        Returns empty list on failure.
    """
    file_path = Path(file_path)
    try:
        doc = fitz.open(str(file_path))
    except Exception as exc:
        logger.error("Cannot open PDF for extraction '%s': %s", file_path.name, exc)
        return []

    pages: list[dict] = []
    try:
        for page_index in range(len(doc)):
            text = doc[page_index].get_text("text")
            pages.append(
                {
                    "page_number": page_index + 1,  # 1-indexed
                    "text": text,
                    "char_count": len(text),
                }
            )
    except Exception as exc:
        logger.error("Text extraction failed for '%s': %s", file_path.name, exc)
    finally:
        doc.close()

    return pages


def get_pdf_metadata(file_path: Path) -> dict:
    """Return structural metadata about a PDF without extracting full text.

    All fields are always present; missing metadata fields use None.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        {
            "page_count": int,
            "file_size_mb": float,
            "has_text": bool,
            "title": str | None,
            "author": str | None,
        }
    """
    file_path = Path(file_path)
    file_size_mb = (
        round(file_path.stat().st_size / (1024 * 1024), 2) if file_path.exists() else 0.0
    )
    base: dict = {
        "page_count": 0,
        "file_size_mb": file_size_mb,
        "has_text": False,
        "title": None,
        "author": None,
    }

    try:
        doc = fitz.open(str(file_path))
    except Exception as exc:
        logger.error("Cannot open PDF for metadata '%s': %s", file_path.name, exc)
        return base

    try:
        page_count = len(doc)
        meta = doc.metadata or {}
        indices = _sample_indices(page_count, _SCAN_SAMPLE_SIZE)
        has_text = any(bool(doc[i].get_text("text").strip()) for i in indices)
        return {
            "page_count": page_count,
            "file_size_mb": file_size_mb,
            "has_text": has_text,
            "title": meta.get("title") or None,
            "author": meta.get("author") or None,
        }
    except Exception as exc:
        logger.error("Metadata extraction error for '%s': %s", file_path.name, exc)
        return base
    finally:
        doc.close()
