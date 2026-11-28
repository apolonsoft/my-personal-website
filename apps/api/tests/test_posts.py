"""Integration tests for the Blog Posts CRUD endpoints."""

from fastapi.testclient import TestClient

AUTH_HEADERS = {"Authorization": "Bearer test-admin-token"}


def _sample_post_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "slug": "first-post",
        "title": "First Post",
        "description": "A short summary of the first post.",
        "content": "# Hello\n\nThis is markdown content.",
        "category": "Engineering",
        "hero_image_url": "/images/structure.webp",
        "image_alt": "Minimal architectural structure",
        "published": True,
        "pub_date": "2026-10-01T12:00:00Z",
    }
    base.update(overrides)
    return base


def test_create_post_requires_auth(client: TestClient) -> None:
    """Unauthenticated POST /api/posts returns 401."""
    res = client.post("/api/posts", json=_sample_post_payload())
    assert res.status_code == 401


def test_create_get_update_delete_post_lifecycle(client: TestClient) -> None:
    """Full CRUD lifecycle works for an authenticated admin."""
    # Create
    create_res = client.post("/api/posts", json=_sample_post_payload(), headers=AUTH_HEADERS)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["slug"] == "first-post"
    assert created["title"] == "First Post"
    assert created["updated_date"] is None

    # Duplicate slug -> 409
    dup_res = client.post("/api/posts", json=_sample_post_payload(), headers=AUTH_HEADERS)
    assert dup_res.status_code == 409

    # Get by slug
    get_res = client.get("/api/posts/first-post")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == created["id"]

    # Partial update
    patch_res = client.patch(
        "/api/posts/first-post",
        json={"title": "Updated First Post"},
        headers=AUTH_HEADERS,
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["title"] == "Updated First Post"
    assert patched["updated_date"] is not None

    # Delete
    del_res = client.delete("/api/posts/first-post", headers=AUTH_HEADERS)
    assert del_res.status_code == 204

    # Confirm deleted -> 404
    missing_res = client.get("/api/posts/first-post")
    assert missing_res.status_code == 404


def test_list_posts_ordering_filtering_and_draft_visibility(client: TestClient) -> None:
    """Listing sorts newest-first, filters by category, and hides drafts publicly."""
    client.post(
        "/api/posts",
        json=_sample_post_payload(
            slug="older-design",
            title="Older Design",
            category="Design",
            pub_date="2026-09-01T12:00:00Z",
        ),
        headers=AUTH_HEADERS,
    )
    client.post(
        "/api/posts",
        json=_sample_post_payload(
            slug="newer-eng",
            title="Newer Engineering",
            category="Engineering",
            pub_date="2026-10-15T12:00:00Z",
        ),
        headers=AUTH_HEADERS,
    )
    client.post(
        "/api/posts",
        json=_sample_post_payload(
            slug="secret-draft",
            title="Secret Draft",
            category="Design",
            published=False,
            pub_date="2026-11-01T12:00:00Z",
        ),
        headers=AUTH_HEADERS,
    )

    # Public list excludes drafts and sorts newest-first
    public_res = client.get("/api/posts")
    assert public_res.status_code == 200
    public_slugs = [p["slug"] for p in public_res.json()]
    assert public_slugs == ["newer-eng", "older-design"]

    # Category filter
    design_res = client.get("/api/posts", params={"category": "Design"})
    assert design_res.status_code == 200
    assert [p["slug"] for p in design_res.json()] == ["older-design"]

    # Draft hidden from public GET /api/posts/{slug}
    assert client.get("/api/posts/secret-draft").status_code == 404
    # Draft visible to admin
    assert client.get("/api/posts/secret-draft", headers=AUTH_HEADERS).status_code == 200

    # include_drafts=true requires auth
    assert client.get("/api/posts", params={"include_drafts": "true"}).status_code == 401
    admin_res = client.get(
        "/api/posts",
        params={"include_drafts": "true"},
        headers=AUTH_HEADERS,
    )
    assert admin_res.status_code == 200
    assert [p["slug"] for p in admin_res.json()] == [
        "secret-draft",
        "newer-eng",
        "older-design",
    ]
