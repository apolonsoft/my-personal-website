"""Integration tests for onboarding, login, forgot-password, and reset-password APIs."""

from datetime import datetime, timedelta, timezone
import re

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from email_service import InMemoryEmailSender
from models import PasswordResetToken


def test_onboarding_status_and_one_time_lock(client: TestClient) -> None:
    """Onboarding creates the first admin user and locks subsequent attempts with 409."""
    status_before = client.get("/api/auth/onboarding/status")
    assert status_before.status_code == 200
    assert status_before.json() == {"initialized": False}

    res = client.post(
        "/api/auth/onboarding",
        json={
            "email": "Admin@Apolonsoft.dev",
            "password": "StrongPassword123",
            "full_name": "Ahmad",
            "headline": "Full-stack Engineer",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "admin@apolonsoft.dev"

    status_after = client.get("/api/auth/onboarding/status")
    assert status_after.status_code == 200
    assert status_after.json() == {"initialized": True}

    second = client.post(
        "/api/auth/onboarding",
        json={
            "email": "other@apolonsoft.dev",
            "password": "AnotherPassword123",
            "full_name": "Other",
        },
    )
    assert second.status_code == 409


def test_login_and_jwt_authorizes_cms_routes(client: TestClient) -> None:
    """Login issues a JWT that authorizes protected CMS routes alongside API_ADMIN_TOKEN."""
    client.post(
        "/api/auth/onboarding",
        json={
            "email": "admin@apolonsoft.dev",
            "password": "StrongPassword123",
            "full_name": "Ahmad",
        },
    )

    bad_login = client.post(
        "/api/auth/login",
        json={"email": "admin@apolonsoft.dev", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401

    good_login = client.post(
        "/api/auth/login",
        json={"email": "admin@apolonsoft.dev", "password": "StrongPassword123"},
    )
    assert good_login.status_code == 200
    jwt_token = good_login.json()["access_token"]

    post_res = client.post(
        "/api/posts",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={
            "slug": "jwt-authorized-post",
            "title": "JWT Post",
            "description": "Created using login JWT",
            "content": "Hello",
            "category": "Engineering",
            "hero_image_url": "/images/structure.webp",
        },
    )
    assert post_res.status_code == 201


def test_forgot_and_reset_password_flow(
    client: TestClient,
    session: Session,
    email_sender: InMemoryEmailSender,
) -> None:
    """Forgot-password avoids enumeration and reset-password enforces single-use & expiry."""
    client.post(
        "/api/auth/onboarding",
        json={
            "email": "admin@apolonsoft.dev",
            "password": "OldPassword123",
            "full_name": "Ahmad",
        },
    )

    # Unknown email returns 200 without sending email
    unknown_res = client.post(
        "/api/auth/forgot-password",
        json={"email": "nobody@apolonsoft.dev"},
    )
    assert unknown_res.status_code == 200
    assert len(email_sender.sent) == 0

    # Valid email triggers reset email
    forgot_res = client.post(
        "/api/auth/forgot-password",
        json={"email": "admin@apolonsoft.dev"},
    )
    assert forgot_res.status_code == 200
    assert len(email_sender.sent) == 1
    sent_email = email_sender.sent[0]
    assert sent_email.to == "admin@apolonsoft.dev"
    match = re.search(r"token=([A-Za-z0-9_-]+)", sent_email.text)
    assert match is not None
    raw_token = match.group(1)

    # Reset password succeeds
    reset_res = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPassword456"},
    )
    assert reset_res.status_code == 200

    # Reusing same token fails with 400
    reuse_res = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "AnotherPassword789"},
    )
    assert reuse_res.status_code == 400

    # Old password fails, new password succeeds
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "admin@apolonsoft.dev", "password": "OldPassword123"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "admin@apolonsoft.dev", "password": "NewPassword456"},
        ).status_code
        == 200
    )

    # Expired token fails with 400
    client.post("/api/auth/forgot-password", json={"email": "admin@apolonsoft.dev"})
    latest_email = email_sender.sent[-1]
    expired_raw = re.search(r"token=([A-Za-z0-9_-]+)", latest_email.text).group(1)
    token_row = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.used_at == None)  # noqa: E711
    ).first()
    assert token_row is not None
    token_row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.add(token_row)
    session.commit()

    expired_res = client.post(
        "/api/auth/reset-password",
        json={"token": expired_raw, "new_password": "ExpiredTryPassword"},
    )
    assert expired_res.status_code == 400
