"""Idempotent seeding script to migrate Astro Markdown blog posts into FastAPI CMS."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import mimetypes
import os
from pathlib import Path
from typing import Any, Optional

import httpx

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BLOG_DIR = REPO_ROOT / "apps" / "web" / "src" / "content" / "blog"
DEFAULT_PUBLIC_DIR = REPO_ROOT / "apps" / "web" / "public"


@dataclass(frozen=True)
class ParsedPost:
    """Structured representation of a Markdown blog post and its frontmatter."""

    slug: str
    title: str
    description: str
    pub_date: str
    updated_date: Optional[str]
    category: str
    hero_image: str
    image_alt: str
    content: str


@dataclass
class SeedReport:
    """Summary of seeding results."""

    created: int = 0
    skipped: int = 0
    uploaded_images: int = 0


def _unquote(value: str) -> str:
    """Strip matching surrounding single or double quotes from a YAML scalar."""
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in ('"', "'"):
        return stripped[1:-1]
    return stripped


def _normalize_iso_date(raw_date: str) -> str:
    """Normalize a YYYY-MM-DD or ISO-8601 date string to UTC ISO-8601."""
    cleaned = _unquote(raw_date)
    if len(cleaned) == 10:
        dt = datetime.strptime(cleaned, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).isoformat()


def parse_markdown_post(path: Path) -> ParsedPost:
    """Parse YAML-style frontmatter and Markdown body from `path`."""
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Missing frontmatter start delimiter in {path}")

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        raise ValueError(f"Missing frontmatter end delimiter in {path}")

    meta: dict[str, str] = {}
    for line in lines[1:end_idx]:
        if not line.strip() or ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip()] = _unquote(val)

    body = "\n".join(lines[end_idx + 1 :]).strip()
    updated_raw = meta.get("updatedDate")
    return ParsedPost(
        slug=path.stem,
        title=meta["title"],
        description=meta["description"],
        pub_date=_normalize_iso_date(meta["pubDate"]),
        updated_date=_normalize_iso_date(updated_raw) if updated_raw else None,
        category=meta["category"],
        hero_image=meta["heroImage"],
        image_alt=meta.get("imageAlt", ""),
        content=body,
    )


def _upload_image_if_needed(
    client: Any,
    public_dir: Path,
    hero_image: str,
    alt_text: str,
    headers: dict[str, str],
) -> tuple[Optional[str], str, bool]:
    """Upload a local image from `public_dir` to `/api/images` if it exists."""
    relative = hero_image.lstrip("/")
    local_path = public_dir / relative
    if not local_path.is_file():
        return None, hero_image, False

    object_key = f"seed/{local_path.name}"
    mime_type, _ = mimetypes.guess_type(local_path.name)
    content_type = mime_type or "image/webp"

    with local_path.open("rb") as fh:
        res = client.post(
            "/api/images",
            headers=headers,
            files={"file": (local_path.name, fh.read(), content_type)},
            data={"alt_text": alt_text, "object_key": object_key},
        )

    if res.status_code == 201:
        data = res.json()
        return data["object_key"], data["url"], True
    if res.status_code == 409:
        return object_key, f"/api/images/{object_key}", False

    res.raise_for_status()
    return object_key, f"/api/images/{object_key}", False


def seed_from_directory(
    client: Any,
    blog_dir: Path,
    public_dir: Path,
    admin_token: str,
) -> SeedReport:
    """Seed all Markdown posts in `blog_dir` into the FastAPI CMS idempotently."""
    report = SeedReport()
    headers = {"Authorization": f"Bearer {admin_token}"}
    post_files = sorted(
        p for p in blog_dir.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".mdx"}
    )

    for post_path in post_files:
        parsed = parse_markdown_post(post_path)
        existing = client.get(f"/api/posts/{parsed.slug}")
        if existing.status_code == 200:
            report.skipped += 1
            continue

        image_key, image_url, uploaded = _upload_image_if_needed(
            client,
            public_dir,
            parsed.hero_image,
            parsed.image_alt,
            headers,
        )
        if uploaded:
            report.uploaded_images += 1

        payload: dict[str, Any] = {
            "slug": parsed.slug,
            "title": parsed.title,
            "description": parsed.description,
            "content": parsed.content,
            "category": parsed.category,
            "hero_image_key": image_key,
            "hero_image_url": image_url,
            "image_alt": parsed.image_alt,
            "published": True,
            "pub_date": parsed.pub_date,
        }
        if parsed.updated_date is not None:
            payload["updated_date"] = parsed.updated_date

        create_res = client.post("/api/posts", json=payload, headers=headers)
        create_res.raise_for_status()
        report.created += 1

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Markdown blog posts into FastAPI CMS.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8787")
    parser.add_argument("--token", default=os.environ.get("API_ADMIN_TOKEN", ""))
    parser.add_argument("--blog-dir", type=Path, default=DEFAULT_BLOG_DIR)
    parser.add_argument("--public-dir", type=Path, default=DEFAULT_PUBLIC_DIR)
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("API_ADMIN_TOKEN or --token is required.")

    with httpx.Client(base_url=args.api_url, timeout=30.0) as client:
        report = seed_from_directory(client, args.blog_dir, args.public_dir, args.token)

    print(
        f"Seeding complete: created={report.created}, "
        f"skipped={report.skipped}, uploaded_images={report.uploaded_images}"
    )


if __name__ == "__main__":
    main()
