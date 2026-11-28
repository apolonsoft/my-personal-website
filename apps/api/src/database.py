"""Dual database engine supporting Cloudflare D1 bindings and local SQLite."""

from collections.abc import Generator
from functools import lru_cache

from fastapi import Request
from sqlalchemy import Engine
from sqlalchemy_cloudflare_d1 import create_engine_from_binding
from sqlmodel import Session, create_engine

from src.config import get_settings


@lru_cache(maxsize=4)
def _get_local_engine(database_url: str) -> Engine:
    """Create and cache a local SQLite engine for development or CLI tools."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def get_engine_for_request(request: Request) -> Engine:
    """Resolve the SQLAlchemy Engine for the incoming request.

    Uses the Cloudflare D1 binding (`env.DB`) inside Workers, falling back to
    a local SQLite database URL when running outside Workers.
    """
    env = request.scope.get("env")
    d1_binding = getattr(env, "DB", None) if env is not None else None
    if d1_binding is not None:
        return create_engine_from_binding(d1_binding)

    settings = get_settings(request)
    return _get_local_engine(settings.database_url)


def get_session(request: Request) -> Generator[Session, None, None]:
    """Yield a SQLModel Session bound to the resolved database engine."""
    engine = get_engine_for_request(request)
    with Session(engine) as session:
        yield session
