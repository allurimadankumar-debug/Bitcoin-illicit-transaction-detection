"""Database engine, session factory and initialization helpers."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

_settings = get_settings()


def _engine_kwargs() -> dict:
    url = _settings.sqlalchemy_url
    if url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    return {"pool_pre_ping": True}


engine = create_engine(_settings.sqlalchemy_url, echo=False, future=True, **_engine_kwargs())
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables. Importing models here registers all mappers."""
    from app.models import Base  # noqa: F401

    Path(_settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def reset_engine_for_tests(database_path: Path) -> None:
    """Point global engine/session at a temporary SQLite file (test helper)."""
    global engine, SessionLocal
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
