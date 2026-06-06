import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

logger = logging.getLogger(__name__)


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


async def init_db() -> None:
    """Create all tables at application startup. Import all models before calling."""
    from models import user, case  # noqa: F401 — registers models with Base

    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info("Database tables created / verified.")
