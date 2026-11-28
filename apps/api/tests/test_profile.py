"""Integration tests for public and authenticated profile endpoints."""

from fastapi.testclient import TestClient

SAMPLE_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"


def test_profile_requires_onboarding_and_auth(client: TestClient) -> None:
    """Public profile returns 404 before onboarding; /me endpoints require JWT."""
    assert client.get("/api/profile").status_code == 404
    assert client.get("/api/profile/me").status_code == 401
    assert client.patch("/api/profile/me", json={"full_name": "Test"}).status_code == 401


def test_view_and_edit_profile_with_r2_avatar(client: TestClient) -> None:
    """Authenticated admin can view/edit profile and link an uploaded R2 avatar."""
    onboard_res = client.post(
        "/api/auth/onboarding",
        json={
            "email": "admin@apolonsoft.dev",
            "password": "StrongPassword123",
            "full_name": "Ahmad",
            "headline": "Software Engineer",
        },
    )
    assert onboard_res.status_code == 201
    jwt_token = onboard_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Upload avatar to R2
    upload_res = client.post(
        "/api/images",
        headers=headers,
        files={"file": ("avatar.png", SAMPLE_PNG, "image/png")},
        data={"object_key": "avatars/admin.png", "alt_text": "Admin avatar"},
    )
    assert upload_res.status_code == 201

    # Invalid avatar_key -> 400
    bad_patch = client.patch(
        "/api/profile/me",
        headers=headers,
        json={"avatar_key": "avatars/missing.png"},
    )
    assert bad_patch.status_code == 400

    # Valid profile update
    patch_res = client.patch(
        "/api/profile/me",
        headers=headers,
        json={
            "full_name": "Ahmad Apolonsoft",
            "headline": "Cloudflare & FastAPI Builder",
            "bio": "Building fast sites on the edge.",
            "avatar_key": "avatars/admin.png",
            "social_links": {
                "github": "https://github.com/apolonsoft",
                "website": "https://www.apolonsoft.dev",
            },
        },
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["full_name"] == "Ahmad Apolonsoft"
    assert updated["avatar_key"] == "avatars/admin.png"
    assert updated["avatar_url"] == "/api/images/avatars/admin.png"
    assert updated["social_links"]["github"] == "https://github.com/apolonsoft"

    # Authenticated /me reflects update
    me_res = client.get("/api/profile/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["bio"] == "Building fast sites on the edge."

    # Public /api/profile reflects update without exposing email
    pub_res = client.get("/api/profile")
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["full_name"] == "Ahmad Apolonsoft"
    assert pub_data["avatar_url"] == "/api/images/avatars/admin.png"
    assert "email" not in pub_data
