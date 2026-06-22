import logging
from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

logger = logging.getLogger(__name__)

# Columns added to `cases` after initial release. create_all() skips existing
# tables entirely (checkfirst=True), so a DB pulled from remote storage that
# predates one of these columns must be patched here on every boot.
_CASE_COLUMNS_TO_ADD: list[tuple[str, str]] = [
    ("pages_analyzed", "INTEGER"),
    ("is_gated", "BOOLEAN NOT NULL DEFAULT 0"),
]


def _build_engine():
    """Build SQLAlchemy engine, adding check_same_thread for SQLite."""
    settings = get_settings()
    connect_args = (
        {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    return create_engine(settings.DATABASE_URL, connect_args=connect_args)


engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_add_case_columns() -> None:
    """Idempotently add any missing columns to an existing `cases` table.

    Safe to run on every startup: each column is only added if absent, and
    no existing row data is read, modified, or deleted.
    """
    existing = {col["name"] for col in inspect(engine).get_columns("cases")}
    with engine.begin() as conn:
        for column_name, column_def in _CASE_COLUMNS_TO_ADD:
            if column_name in existing:
                continue
            conn.execute(text(f"ALTER TABLE cases ADD COLUMN {column_name} {column_def}"))
            logger.info("Migration: added missing column cases.%s", column_name)


async def init_db() -> None:
    """Create all tables at application startup. Import all models before calling."""
    from models import user, case  # noqa: F401 — registers models with Base

    Base.metadata.create_all(bind=engine, checkfirst=True)
    _migrate_add_case_columns()
    logger.info("Database tables created / verified.")
