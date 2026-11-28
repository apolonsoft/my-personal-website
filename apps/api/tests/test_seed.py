"""Tests for Markdown frontmatter parsing and idempotent CMS seeding."""

from pathlib import Path

from fastapi.testclient import TestClient

from scripts.seed_posts import parse_markdown_post, seed_from_directory

SAMPLE_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"


def test_parse_markdown_post(tmp_path: Path) -> None:
    """parse_markdown_post extracts frontmatter fields and Markdown body."""
    md = tmp_path / "hello-world.md"
    md.write_text(
        '---\ntitle: "Hello World"\ndescription: "Intro post"\n'
        "pubDate: 2026-09-12\ncategory: Design\nheroImage: /images/hero.png\n"
        'imageAlt: "Hero alt"\n---\n\n## Section\n\nBody copy.\n',
        encoding="utf-8",
    )

    parsed = parse_markdown_post(md)
    assert parsed.slug == "hello-world"
    assert parsed.title == "Hello World"
    assert parsed.category == "Design"
    assert parsed.pub_date == "2026-09-12T00:00:00+00:00"
    assert parsed.content == "## Section\n\nBody copy."


def test_seed_from_directory_is_idempotent(client: TestClient, tmp_path: Path) -> None:
    """First run uploads images and creates posts; second run skips existing posts."""
    blog_dir = tmp_path / "blog"
    public_dir = tmp_path / "public"
    (public_dir / "images").mkdir(parents=True)
    blog_dir.mkdir(parents=True)

    (public_dir / "images" / "hero.png").write_bytes(SAMPLE_PNG)
    (blog_dir / "sample-post.md").write_text(
        '---\ntitle: "Sample"\ndescription: "Summary"\n'
        "pubDate: 2026-10-01\ncategory: Engineering\n"
        "heroImage: /images/hero.png\nimageAlt: Sample alt\n---\n\nHello.\n",
        encoding="utf-8",
    )

    first = seed_from_directory(client, blog_dir, public_dir, "test-admin-token")
    assert first.created == 1
    assert first.skipped == 0
    assert first.uploaded_images == 1

    post_res = client.get("/api/posts/sample-post")
    assert post_res.status_code == 200
    assert post_res.json()["hero_image_url"] == "/api/images/seed/hero.png"

    second = seed_from_directory(client, blog_dir, public_dir, "test-admin-token")
    assert second.created == 0
    assert second.skipped == 1
    assert second.uploaded_images == 0
