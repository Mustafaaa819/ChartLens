import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from models.database import Base


class User(Base):
    """Registered lawyer account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    firm_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    lemon_customer_id: Mapped[str | None] = mapped_column(
        String, nullable=True, unique=True
    )
    lemon_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # values: trial / active / cancelled / past_due / canceled
    subscription_status: Mapped[str] = mapped_column(
        String, nullable=False, default="trial"
    )
    trial_cases_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cases: Mapped[list["Case"]] = relationship(  # type: ignore[name-defined]
        "Case", back_populates="user", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Fields required to register a new user."""

    email: str
    password: str
    firm_name: str


class UserOut(BaseModel):
    """Safe user representation returned from API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    firm_name: str
    subscription_status: str
    trial_cases_used: int
