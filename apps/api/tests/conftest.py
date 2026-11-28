"""Pytest fixtures for testing the FastAPI Blog CMS application."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import models  # noqa: F401 - ensure SQLModel metadata includes all tables
from database import get_session
from email_service import InMemoryEmailSender, get_email_sender
from main import app
from storage import InMemoryImageStorage, get_storage


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure deterministic test environment variables."""
    monkeypatch.setenv("API_ADMIN_TOKEN", os.environ.get("API_ADMIN_TOKEN", "test-admin-token"))
    monkeypatch.setenv("JWT_SECRET", os.environ.get("JWT_SECRET", "test-jwt-secret"))
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:4321")


@pytest.fixture()
def db_engine() -> Generator[Engine, None, None]:
    """Create a fresh in-memory SQLite engine per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    try:
        yield engine
    finally:
        SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def session(db_engine: Engine) -> Generator[Session, None, None]:
    """Yield a SQLModel Session for direct test assertions."""
    with Session(db_engine) as db_session:
        yield db_session


@pytest.fixture()
def image_storage() -> InMemoryImageStorage:
    """Return an isolated in-memory R2 storage fake per test."""
    return InMemoryImageStorage()


@pytest.fixture()
def email_sender() -> InMemoryEmailSender:
    """Return an isolated in-memory EmailSender fake per test."""
    return InMemoryEmailSender()


@pytest.fixture()
def client(
    db_engine: Engine,
    image_storage: InMemoryImageStorage,
    email_sender: InMemoryEmailSender,
) -> Generator[TestClient, None, None]:
    """Return a FastAPI TestClient wired to in-memory SQLite, R2 fake, and email fake."""

    async def _override_session() -> Generator[Session, None, None]:
        with Session(db_engine) as db_session:
            yield db_session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_storage] = lambda: image_storage
    app.dependency_overrides[get_email_sender] = lambda: email_sender
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
