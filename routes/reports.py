"""Report download routes — PDF, Excel, and raw JSON chronology."""
import json
import logging
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session

from models.case import Case
from models.database import get_db
from models.user import User
from routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])

EXCEL_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_filename(name: str) -> str:
    """Return a filesystem-safe version of *name* suitable for Content-Disposition.

    Spaces become underscores; any character that is not alphanumeric, an
    underscore, or a hyphen is removed.
    """
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w\-]", "", name)
    return name or "report"


def _fetch_owned_case(
    case_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Case:
    """Return the Case row, raising 404 or 403 as appropriate.

    Wraps the DB query in try/except so database errors surface as 500.
    """
    try:
        case: Case | None = db.query(Case).filter(Case.id == case_id).first()
    except Exception as exc:
        logger.error("DB error fetching case %s: %s", case_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from exc

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    if case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return case


# ---------------------------------------------------------------------------
# GET /reports/{case_id}/pdf
# ---------------------------------------------------------------------------


@router.get("/{case_id}/pdf")
async def download_pdf_report(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download the PDF chronology report for a completed case.

    Returns 400 if analysis is not yet complete, 404 if the file is missing.
    """
    case = _fetch_owned_case(case_id, current_user, db)

    if case.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report not ready yet",
        )

    if not case.pdf_report_path or not Path(case.pdf_report_path).exists():
        logger.warning("PDF report file missing for case %s", case_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report not found",
        )

    safe_name = _safe_filename(case.client_name)
    filename = f"{safe_name}_chronology.pdf"

    logger.info("Serving PDF report for case %s to user %s", case_id, current_user.email)
    return FileResponse(
        path=case.pdf_report_path,
        media_type="application/pdf",
        filename=filename,
    )


# ---------------------------------------------------------------------------
# GET /reports/{case_id}/excel
# ---------------------------------------------------------------------------


@router.get("/{case_id}/excel")
async def download_excel_report(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download the Excel chronology spreadsheet for a completed case.

    Returns 400 if analysis is not yet complete, 404 if the file is missing.
    """
    case = _fetch_owned_case(case_id, current_user, db)

    if case.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report not ready yet",
        )

    if not case.excel_report_path or not Path(case.excel_report_path).exists():
        logger.warning("Excel report file missing for case %s", case_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Excel report not found",
        )

    safe_name = _safe_filename(case.client_name)
    filename = f"{safe_name}_chronology.xlsx"

    logger.info("Serving Excel report for case %s to user %s", case_id, current_user.email)
    return FileResponse(
        path=case.excel_report_path,
        media_type=EXCEL_MEDIA_TYPE,
        filename=filename,
    )


# ---------------------------------------------------------------------------
# GET /reports/{case_id}/json
# ---------------------------------------------------------------------------


@router.get("/{case_id}/json")
async def download_json_report(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return the raw chronology JSON for any case status.

    Useful for programmatic access and future API integrations. Returns
    whatever is currently stored — may be partial if still processing.
    """
    case = _fetch_owned_case(case_id, current_user, db)

    if case.chronology_json is None:
        return {"status": case.status, "data": None}

    try:
        chronology = json.loads(case.chronology_json)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse chronology_json for case %s: %s", case_id, exc)
        return {"status": case.status, "data": None}

    return {"status": case.status, "data": chronology}
