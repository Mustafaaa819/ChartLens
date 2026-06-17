"""Case routes — dashboard, upload, list, retrieve, status, delete."""
import json
import logging
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import get_settings
from db_sync import push_db
from core.analyzer import analyze_case
from core.chronology_builder import build_chronology
from core.inconsistency_detector import detect_case_inconsistencies
from core.limiter import limiter
from core.pdf_extractor import validate_pdf
from core.report_generator import generate_excel_report, generate_pdf_report
from models.case import Case, CaseOut
from models.database import SessionLocal, get_db
from models.user import User
from routes.auth import COOKIE_NAME, _decode_token, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cases"])

_BASE_DIR = Path(__file__).parent.parent
_UPLOADS_DIR = _BASE_DIR / "uploads"
_REPORTS_DIR = _BASE_DIR / "reports"


def _ensure_uploads_dir() -> None:
    _UPLOADS_DIR.mkdir(exist_ok=True)


def _date_fmt(dt: datetime) -> str:
    """Format a datetime as 'Month Day, Year' with no zero-padding on the day."""
    return dt.strftime(f"%B {dt.day}, %Y")


def _currency_fmt(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


templates = Jinja2Templates(directory="templates")
templates.env.filters["datefmt"] = _date_fmt
templates.env.filters["currency"] = _currency_fmt


# ---------------------------------------------------------------------------
# Background pipeline
# ---------------------------------------------------------------------------


async def run_analysis_pipeline(case_id: uuid.UUID, pdf_path: str) -> None:
    """Full AI analysis pipeline executed as a FastAPI BackgroundTask.

    Creates its own DB session — the request session is closed before
    this function runs. Writes progress to the Case row at each stage.
    On any exception: marks case as failed, logs full traceback.
    """
    db_bg: Session = SessionLocal()
    case: Case | None = None
    try:
        case = db_bg.query(Case).filter(Case.id == case_id).first()
        if case is None:
            logger.error("run_analysis_pipeline: case %s not found in DB", case_id)
            return

        # Stage: start
        case.status = "processing"
        case.progress_percent = 5
        case.progress_message = "Starting analysis pipeline..."
        db_bg.commit()

        # Async progress callback — bumps progress toward 70% as chunks complete.
        # Each invocation adds 3% and caps at 70 (extraction phase ceiling).
        _call_counter = [0]

        async def _progress_callback(message: str) -> None:
            _call_counter[0] += 1
            case.progress_percent = min(5 + _call_counter[0] * 3, 70)
            case.progress_message = (message or "")[:255]
            db_bg.commit()

        # Stage: extract (5% → 70%)
        analysis_result = await analyze_case(pdf_path, progress_callback=_progress_callback)

        if analysis_result.get("error") and not analysis_result.get("events"):
            raise RuntimeError(f"Extraction failed: {analysis_result['error']}")

        failed = analysis_result.get("failed_chunks", 0)
        total = analysis_result.get("total_chunks", 1)
        if total > 0 and failed > total * 0.5:
            raise RuntimeError(
                f"More than 50% of chunks failed extraction ({failed}/{total})"
            )

        # Stage: chronology (70% → 75%)
        case.progress_percent = 75
        case.progress_message = "Building chronology..."
        db_bg.commit()

        chronology_result = build_chronology(analysis_result)
        if "error" in chronology_result and not chronology_result.get("chronology"):
            raise RuntimeError(f"Chronology build failed: {chronology_result['error']}")

        # Stage: inconsistency detection (75% → 85%)
        case.progress_percent = 85
        case.progress_message = "Detecting inconsistencies..."
        db_bg.commit()

        inconsistency_result = detect_case_inconsistencies(chronology_result)

        # Stage: PDF report (85% → 90%)
        case.progress_percent = 90
        case.progress_message = "Generating PDF report..."
        db_bg.commit()

        case_data = {"client_name": case.client_name, "case_number": case.case_number}
        reports_dir = _REPORTS_DIR / str(case.id)
        reports_dir.mkdir(parents=True, exist_ok=True)

        pdf_output = str(reports_dir / "report.pdf")
        pdf_result = generate_pdf_report(case_data, chronology_result, inconsistency_result, pdf_output)
        if pdf_result:
            case.pdf_report_path = pdf_result

        # Stage: Excel report (90% → 95%)
        case.progress_percent = 95
        case.progress_message = "Generating Excel report..."
        db_bg.commit()

        excel_output = str(reports_dir / "report.xlsx")
        excel_result = generate_excel_report(case_data, chronology_result, inconsistency_result, excel_output)
        if excel_result:
            case.excel_report_path = excel_result

        # Stage: complete — embed inconsistency_result so results page reads both from one field
        combined_data = dict(chronology_result)
        combined_data["inconsistency_result"] = inconsistency_result
        case.chronology_json = json.dumps(combined_data)
        case.status = "complete"
        case.completed_at = datetime.utcnow()
        case.progress_percent = 100
        case.progress_message = "Analysis complete."
        db_bg.commit()
        push_db()

        logger.info(
            "run_analysis_pipeline complete: case=%s events=%d",
            case_id,
            chronology_result.get("total_events", 0),
        )

    except Exception as exc:
        logger.error(
            "run_analysis_pipeline FAILED: case=%s\n%s",
            case_id,
            traceback.format_exc(),
        )
        try:
            db_bg.rollback()
            target = case if case is not None else db_bg.query(Case).filter(Case.id == case_id).first()
            if target is not None:
                target.status = "failed"
                target.error_message = str(exc)[:500]
                target.progress_percent = 0
                target.progress_message = "Analysis failed."
                db_bg.commit()
        except Exception as db_exc:
            logger.error("Could not write failure state to DB for case %s: %s", case_id, db_exc)
    finally:
        db_bg.close()


# ---------------------------------------------------------------------------
# GET /dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Render the case list dashboard for the authenticated user."""
    try:
        current_user: User = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    cases: list[Case] = (
        db.query(Case)
        .filter(Case.user_id == current_user.id)
        .order_by(Case.created_at.desc())
        .all()
    )

    has_active_cases: bool = any(
        c.status in ("uploading", "processing") for c in cases
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "cases": cases,
            "has_active_cases": has_active_cases,
        },
    )


# ---------------------------------------------------------------------------
# GET /upload
# ---------------------------------------------------------------------------


@router.get("/upload")
async def upload_page(request: Request, db: Session = Depends(get_db)):
    """Render the PDF upload page, or redirect to billing if access is blocked."""
    try:
        current_user: User = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    access_error = _check_upload_access(current_user)
    if access_error:
        return RedirectResponse(url="/billing", status_code=302)

    return templates.TemplateResponse(
        "upload.html",
        {"request": request, "current_user": current_user, "error": None},
    )


# ---------------------------------------------------------------------------
# POST /cases/upload
# ---------------------------------------------------------------------------


def _check_upload_access(user: User) -> str | None:
    """Return an error message string if the user cannot upload, else None."""
    status = user.subscription_status

    if status in ("cancelled", "canceled"):
        return "Your subscription is cancelled. Resubscribe to continue uploading cases."

    if status == "past_due":
        return "Your subscription payment failed. Please update your billing details."

    if status == "trial" and user.trial_cases_used >= 3:
        return "Your free trial has ended. Upgrade to ChartLens Pro to continue."

    if status not in ("trial", "active", "cancelled", "canceled", "past_due"):
        logger.warning(
            "Unknown subscription_status '%s' for user %s — allowing upload.",
            status,
            user.id,
        )

    return None  # access granted


@router.post("/cases/upload")
@limiter.limit("10/hour")
async def upload_case(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    client_name: str = Form(...),
    case_number: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Validate upload, persist PDF with UUID filename, create Case row,
    increment trial counter, then launch the AI analysis pipeline."""
    settings = get_settings()

    # Step 1a — require authentication
    try:
        current_user: User = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    def _upload_error(msg: str):
        # Return JSON so the fetch()-based upload.js can display the exact message
        return JSONResponse({"detail": msg}, status_code=400)

    # Step 1b — subscription access check
    access_error = _check_upload_access(current_user)
    if access_error:
        return _upload_error(access_error)

    # Step 1c — file type guard (content-type + extension)
    filename = file.filename or ""
    if file.content_type != "application/pdf" or not filename.lower().endswith(".pdf"):
        return _upload_error("Only PDF files are accepted.")

    # Step 1d — read file and check size before touching disk
    try:
        file_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        return _upload_error("Failed to read uploaded file.")

    if len(file_bytes) == 0:
        return _upload_error("Uploaded file is empty.")

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        return _upload_error(f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB upload limit.")

    # Step 2 — save to disk with UUID filename
    _ensure_uploads_dir()
    disk_filename = f"{uuid.uuid4()}.pdf"
    file_path = _UPLOADS_DIR / disk_filename

    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)
    except Exception as exc:
        logger.error("Failed to write file to disk: %s", exc)
        return _upload_error("Failed to save uploaded file.")

    # Step 1e — PDF validation (requires file on disk)
    validation = validate_pdf(file_path)
    if not validation["valid"]:
        file_path.unlink(missing_ok=True)
        return _upload_error(validation["error"])

    page_count: int = validation["page_count"]
    original_filename = filename or disk_filename

    # Step 3 — create Case row
    try:
        case = Case(
            id=uuid.uuid4(),
            user_id=current_user.id,
            client_name=client_name,
            case_number=case_number or None,
            original_filename=original_filename,
            file_path=str(file_path),
            page_count=page_count,
            status="uploading",
            progress_percent=0,
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        push_db()
    except Exception as exc:
        logger.error("Database error creating case: %s", exc)
        db.rollback()
        file_path.unlink(missing_ok=True)
        return _upload_error("Failed to create case record.")

    # Step 4 — increment trial_cases_used
    try:
        current_user.trial_cases_used += 1
        db.commit()
        push_db()
    except Exception as exc:
        logger.warning("Failed to increment trial_cases_used for user %s: %s", current_user.id, exc)
        db.rollback()

    # Step 5 — launch background pipeline
    background_tasks.add_task(
        run_analysis_pipeline,
        case_id=case.id,
        pdf_path=str(file_path),
    )

    # Step 6 — redirect to results page
    return RedirectResponse(url=f"/cases/{case.id}", status_code=302)


# ---------------------------------------------------------------------------
# DELETE /cases/{case_id}
# ---------------------------------------------------------------------------


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Delete a case, its uploaded PDF, and any generated reports.
    Restricted to the case owner."""
    try:
        current_user: User = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    case: Case | None = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    if case.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Remove all files associated with this case
    for path_attr in ("file_path", "pdf_report_path", "excel_report_path"):
        path_val: str | None = getattr(case, path_attr)
        if path_val:
            try:
                Path(path_val).unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("Could not delete file '%s': %s", path_val, exc)

    try:
        db.delete(case)
        db.commit()
        push_db()
    except Exception as exc:
        logger.error("DB error deleting case %s: %s", case_id, exc)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete case.")

    return RedirectResponse(url="/dashboard", status_code=302)


# ---------------------------------------------------------------------------
# GET /cases
# ---------------------------------------------------------------------------


@router.get("/cases", response_model=list[CaseOut])
def list_cases(request: Request, db: Session = Depends(get_db)) -> list[Case]:
    """Return all cases for the authenticated user, newest first."""
    try:
        current_user: User = get_current_user(request, db)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return (
        db.query(Case)
        .filter(Case.user_id == current_user.id)
        .order_by(Case.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# GET /cases/{case_id}
# ---------------------------------------------------------------------------


@router.get("/cases/{case_id}")
async def get_case(case_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    """Render the results page for a case (processing / failed / complete states)."""
    try:
        current_user: User = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    case: Case | None = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if case.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    chronology: dict | None = None
    inconsistencies: dict | None = None

    if case.status == "complete" and case.chronology_json:
        try:
            chronology = json.loads(case.chronology_json)
            inconsistencies = chronology.get("inconsistency_result")
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid chronology_json for case %s", case_id)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "current_user": current_user,
            "case": case,
            "chronology": chronology,
            "inconsistencies": inconsistencies,
        },
    )


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/status
# ---------------------------------------------------------------------------


@router.get("/cases/{case_id}/status")
def get_case_status(case_id: uuid.UUID, db: Session = Depends(get_db)) -> JSONResponse:
    """Return status and progress percent for polling the UI spinner."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return JSONResponse(
        content={
            "case_id": str(case.id),
            "status": case.status,
            "progress_percent": case.progress_percent,
        }
    )


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/progress
# ---------------------------------------------------------------------------


@router.get("/cases/{case_id}/progress")
def get_case_progress(case_id: uuid.UUID, db: Session = Depends(get_db)) -> JSONResponse:
    """Return detailed progress info including the processing log."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    try:
        processing_log = json.loads(case.processing_log) if case.processing_log else []
    except (json.JSONDecodeError, TypeError):
        logger.warning("Invalid JSON in processing_log for case %s — returning empty list", case_id)
        processing_log = []

    return JSONResponse(
        content={
            "case_id": str(case.id),
            "status": case.status,
            "progress_message": case.progress_message,
            "processing_log": processing_log,
        }
    )
