"""Integration tests for the Cloudflare R2 image storage endpoints."""

from fastapi.testclient import TestClient

from src.routers.images import MAX_IMAGE_BYTES

AUTH_HEADERS = {"Authorization": "Bearer test-admin-token"}
SAMPLE_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"


def test_upload_requires_auth(client: TestClient) -> None:
    """Unauthenticated POST /api/images returns 401."""
    res = client.post(
        "/api/images",
        files={"file": ("hero.png", SAMPLE_PNG, "image/png")},
    )
    assert res.status_code == 401


def test_upload_get_and_delete_image(client: TestClient) -> None:
    """Authenticated upload persists to R2 and D1, serves immutable headers, and deletes cleanly."""
    upload_res = client.post(
        "/api/images",
        headers=AUTH_HEADERS,
        files={"file": ("hero.png", SAMPLE_PNG, "image/png")},
        data={"alt_text": "Hero graphic", "object_key": "blog/hero.png"},
    )
    assert upload_res.status_code == 201
    body = upload_res.json()
    assert body["object_key"] == "blog/hero.png"
    assert body["content_type"] == "image/png"
    assert body["size_bytes"] == len(SAMPLE_PNG)
    assert body["alt_text"] == "Hero graphic"
    assert body["url"] == "/api/images/blog/hero.png"

    # Fetch image
    get_res = client.get("/api/images/blog/hero.png")
    assert get_res.status_code == 200
    assert get_res.content == SAMPLE_PNG
    assert get_res.headers["content-type"] == "image/png"
    assert get_res.headers["cache-control"] == "public, max-age=31536000, immutable"

    # Delete requires auth
    assert client.delete("/api/images/blog/hero.png").status_code == 401

    # Delete succeeds with auth
    del_res = client.delete("/api/images/blog/hero.png", headers=AUTH_HEADERS)
    assert del_res.status_code == 204

    # Subsequent GET returns 404
    assert client.get("/api/images/blog/hero.png").status_code == 404


def test_upload_validation_errors(client: TestClient) -> None:
    """Unsupported MIME, empty files, and oversized payloads are rejected."""
    bad_mime = client.post(
        "/api/images",
        headers=AUTH_HEADERS,
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert bad_mime.status_code == 415

    empty_file = client.post(
        "/api/images",
        headers=AUTH_HEADERS,
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert empty_file.status_code == 400

    oversized = client.post(
        "/api/images",
        headers=AUTH_HEADERS,
        files={"file": ("huge.webp", b"x" * (MAX_IMAGE_BYTES + 1), "image/webp")},
    )
    assert oversized.status_code == 413
