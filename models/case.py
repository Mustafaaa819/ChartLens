import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from models.database import Base


class Case(Base):
    """A single medical record analysis job linked to a User."""

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    client_name: Mapped[str] = mapped_column(String, nullable=False)
    case_number: Mapped[str | None] = mapped_column(String, nullable=True)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    # UUID-based path on disk — never the raw original filename
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # values: uploading / processing / complete / failed
    status: Mapped[str] = mapped_column(String, nullable=False, default="uploading")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    chronology_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_report_path: Mapped[str | None] = mapped_column(String, nullable=True)
    excel_report_path: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    # Human-readable status line updated during processing (e.g. "Extracting chunk 3 of 7...")
    progress_message: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    # JSON-encoded list of timestamped log entries for the progress endpoint
    processing_log: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="cases"
    )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CaseCreate(BaseModel):
    """Fields provided by the lawyer when uploading a new case."""

    client_name: str
    case_number: str | None = None


class CaseOut(BaseModel):
    """Case representation returned from API endpoints (file_path excluded)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    client_name: str
    case_number: str | None
    original_filename: str
    page_count: int
    status: str
    progress_percent: int
    created_at: datetime
    completed_at: datetime | None
    chronology_json: str | None
    pdf_report_path: str | None
    excel_report_path: str | None
    error_message: str | None
