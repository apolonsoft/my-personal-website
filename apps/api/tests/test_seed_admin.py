"""Tests for headless default admin onboarding script."""

from fastapi.testclient import TestClient

from scripts.seed_admin import onboard_default_admin


def test_onboard_default_admin_is_idempotent(client: TestClient) -> None:
    """First call creates default admin; second call skips cleanly."""
    created_first = onboard_default_admin(
        client,
        email="admin@apolonsoft.dev",
        password="StrongPassword123",
        full_name="Ahmad",
        headline="Builder",
    )
    assert created_first is True

    created_second = onboard_default_admin(
        client,
        email="admin@apolonsoft.dev",
        password="StrongPassword123",
        full_name="Ahmad",
    )
    assert created_second is False

    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@apolonsoft.dev", "password": "StrongPassword123"},
    )
    assert login_res.status_code == 200
