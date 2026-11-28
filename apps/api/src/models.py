"""SQLModel database entities and Pydantic request/response schemas."""

from datetime import datetime, timezone
import re
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class ImageAsset(SQLModel, table=True):
    """Metadata record for an image stored in Cloudflare R2."""

    __tablename__ = "image_assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    object_key: str = Field(unique=True, index=True, max_length=512)
    filename: str = Field(max_length=255)
    content_type: str = Field(max_length=128)
    size_bytes: int
    alt_text: str = Field(default="", max_length=500)
    created_at: datetime = Field(default_factory=utcnow)


class Post(SQLModel, table=True):
    """Blog post stored in Cloudflare D1 / SQLite."""

    __tablename__ = "posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True, max_length=200)
    title: str = Field(max_length=300)
    description: str = Field(max_length=1000)
    content: str
    category: str = Field(index=True, max_length=100)
    hero_image_key: Optional[str] = Field(
        default=None,
        foreign_key="image_assets.object_key",
        max_length=512,
    )
    hero_image_url: str = Field(max_length=1024)
    image_alt: str = Field(default="", max_length=500)
    published: bool = Field(default=True, index=True)
    pub_date: datetime = Field(index=True)
    updated_date: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utcnow)


class PostCreate(SQLModel):
    """Payload for creating a new blog post."""

    slug: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=1000)
    content: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=100)
    hero_image_key: Optional[str] = Field(default=None, max_length=512)
    hero_image_url: Optional[str] = Field(default=None, max_length=1024)
    image_alt: str = Field(default="", max_length=500)
    published: bool = True
    pub_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        """Ensure slug is URL-safe lowercase alphanumeric with hyphens."""
        if not SLUG_PATTERN.match(value):
            raise ValueError("slug must match ^[a-z0-9]+(?:-[a-z0-9]+)*$")
        return value


class PostUpdate(SQLModel):
    """Payload for partially updating an existing blog post."""

    slug: Optional[str] = Field(default=None, min_length=1, max_length=200)
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    content: Optional[str] = Field(default=None, min_length=1)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    hero_image_key: Optional[str] = Field(default=None, max_length=512)
    hero_image_url: Optional[str] = Field(default=None, max_length=1024)
    image_alt: Optional[str] = Field(default=None, max_length=500)
    published: Optional[bool] = None
    pub_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: Optional[str]) -> Optional[str]:
        """Ensure updated slug is URL-safe when provided."""
        if value is not None and not SLUG_PATTERN.match(value):
            raise ValueError("slug must match ^[a-z0-9]+(?:-[a-z0-9]+)*$")
        return value


class PostRead(SQLModel):
    """Public representation of a blog post."""

    id: int
    slug: str
    title: str
    description: str
    content: str
    category: str
    hero_image_key: Optional[str]
    hero_image_url: str
    image_alt: str
    published: bool
    pub_date: datetime
    updated_date: Optional[datetime]
    created_at: datetime


class ImageAssetRead(SQLModel):
    """Public representation of an uploaded image asset."""

    id: int
    object_key: str
    filename: str
    content_type: str
    size_bytes: int
    alt_text: str
    url: str
    created_at: datetime
