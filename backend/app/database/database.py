"""SQLAlchemy database engine, session, and Base."""
from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


def _create_engine():
    url = settings.database_url
    # SQLite in-memory needs StaticPool so all connections share one DB
    # (otherwise each connection gets its own empty in-memory DB).
    if url.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool

        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.debug and settings.app_env == "development",
    )


def get_engine():
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# Backwards-compatible aliases used by Alembic and imports.
def __getattr__(name):
    if name == "engine":
        return get_engine()
    if name == "SessionLocal":
        return get_session_factory()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
