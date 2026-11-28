"""Pytest fixtures for testing the FastAPI Blog CMS application."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure deterministic test environment variables."""
    monkeypatch.setenv("API_ADMIN_TOKEN", os.environ.get("API_ADMIN_TOKEN", "test-admin-token"))
    monkeypatch.setenv("ENVIRONMENT", "test")


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Return a FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client
