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


_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(value: str) -> str:
    cleaned = value.strip().lower()
    if not _EMAIL_PATTERN.match(cleaned):
        raise ValueError("Invalid email address.")
    return cleaned


class User(SQLModel, table=True):
    """Admin user account and public profile stored in Cloudflare D1 / SQLite."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=512)
    role: str = Field(default="admin", max_length=32)
    is_active: bool = Field(default=True, index=True)
    full_name: str = Field(max_length=200)
    headline: str = Field(default="", max_length=300)
    bio: str = Field(default="", max_length=4000)
    avatar_key: Optional[str] = Field(
        default=None,
        foreign_key="image_assets.object_key",
        max_length=512,
    )
    avatar_url: str = Field(default="", max_length=1024)
    social_links_json: str = Field(default="{}", max_length=4000)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class PasswordResetToken(SQLModel, table=True):
    """Single-use expiring password reset token (stored as SHA-256 hex digest)."""

    __tablename__ = "password_reset_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(unique=True, index=True, max_length=64)
    expires_at: datetime = Field(index=True)
    used_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utcnow)


class OnboardingStatusResponse(SQLModel):
    """Whether an initial admin user has already been created."""

    initialized: bool


class OnboardingRequest(SQLModel):
    """Payload for one-time default admin user onboarding."""

    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    headline: str = Field(default="", max_length=300)
    bio: str = Field(default="", max_length=4000)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class LoginRequest(SQLModel):
    """Email and password credentials for login."""

    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class ForgotPasswordRequest(SQLModel):
    """Payload for requesting a password reset email."""

    email: str = Field(max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class ResetPasswordRequest(SQLModel):
    """Payload for completing a password reset using a single-use token."""

    token: str = Field(min_length=16, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(SQLModel):
    """Generic status message response."""

    message: str


class PublicProfileRead(SQLModel):
    """Public profile exposed to the Astro frontend."""

    full_name: str
    headline: str
    bio: str
    avatar_url: str
    social_links: dict[str, str]


class ProfileRead(SQLModel):
    """Authenticated admin profile."""

    id: int
    email: str
    role: str
    full_name: str
    headline: str
    bio: str
    avatar_key: Optional[str]
    avatar_url: str
    social_links: dict[str, str]
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(SQLModel):
    """Partial update payload for PATCH /api/profile/me."""

    email: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    headline: Optional[str] = Field(default=None, max_length=300)
    bio: Optional[str] = Field(default=None, max_length=4000)
    avatar_key: Optional[str] = Field(default=None, max_length=512)
    avatar_url: Optional[str] = Field(default=None, max_length=1024)
    social_links: Optional[dict[str, str]] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_email(value) if value is not None else None


class AuthTokenResponse(SQLModel):
    """JWT access token response returned by onboarding and login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: ProfileRead
