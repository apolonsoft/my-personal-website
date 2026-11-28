"""Blog Posts CRUD API router."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from src.auth import is_admin_authenticated, require_admin
from src.config import get_settings
from src.database import get_session
from src.models import (
    ImageAsset,
    Post,
    PostCreate,
    PostRead,
    PostUpdate,
    utcnow,
)

router = APIRouter(prefix="/api/posts", tags=["posts"])
_optional_bearer = HTTPBearer(auto_error=False)


def _resolve_hero_image_url(
    request: Request,
    hero_image_key: Optional[str],
    hero_image_url: Optional[str],
) -> str:
    """Resolve the public hero image URL from explicit input or an R2 object key."""
    if hero_image_url:
        return hero_image_url
    if hero_image_key:
        base_url = get_settings(request).r2_public_base_url
        if base_url:
            return f"{base_url}/{hero_image_key}"
        return f"/api/images/{hero_image_key}"
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Either hero_image_url or hero_image_key must be provided.",
    )


def _validate_image_asset_exists(session: Session, object_key: Optional[str]) -> None:
    """Verify a referenced ImageAsset exists in the database."""
    if object_key is None:
        return
    asset = session.exec(
        select(ImageAsset).where(ImageAsset.object_key == object_key)
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image asset '{object_key}' not found.",
        )


@router.get("", response_model=list[PostRead])
def list_posts(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_optional_bearer)],
    category: Optional[str] = None,
    include_drafts: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Post]:
    """List blog posts ordered newest-first."""
    if include_drafts and not is_admin_authenticated(request, credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    statement = select(Post)
    if not include_drafts:
        statement = statement.where(Post.published == True)  # noqa: E712
    if category is not None:
        statement = statement.where(Post.category == category)

    statement = statement.order_by(Post.pub_date.desc()).offset(offset).limit(limit)
    return list(session.exec(statement).all())


@router.get("/{slug}", response_model=PostRead)
def get_post(
    slug: str,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_optional_bearer)],
) -> Post:
    """Fetch a single blog post by slug."""
    post = session.exec(select(Post).where(Post.slug == slug)).first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if not post.published and not is_admin_authenticated(request, credentials):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[None, Depends(require_admin)],
) -> Post:
    """Create a new blog post (admin only)."""
    existing = session.exec(select(Post).where(Post.slug == payload.slug)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post with slug '{payload.slug}' already exists.",
        )

    _validate_image_asset_exists(session, payload.hero_image_key)
    resolved_url = _resolve_hero_image_url(
        request,
        payload.hero_image_key,
        payload.hero_image_url,
    )

    post = Post(
        slug=payload.slug,
        title=payload.title,
        description=payload.description,
        content=payload.content,
        category=payload.category,
        hero_image_key=payload.hero_image_key,
        hero_image_url=resolved_url,
        image_alt=payload.image_alt,
        published=payload.published,
        pub_date=payload.pub_date or utcnow(),
        updated_date=payload.updated_date,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@router.patch("/{slug}", response_model=PostRead)
def update_post(
    slug: str,
    payload: PostUpdate,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[None, Depends(require_admin)],
) -> Post:
    """Partially update an existing blog post (admin only)."""
    post = session.exec(select(Post).where(Post.slug == slug)).first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    updates = payload.model_dump(exclude_unset=True)
    new_slug = updates.get("slug")
    if new_slug is not None and new_slug != post.slug:
        collision = session.exec(select(Post).where(Post.slug == new_slug)).first()
        if collision is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Post with slug '{new_slug}' already exists.",
            )

    if "hero_image_key" in updates:
        _validate_image_asset_exists(session, updates["hero_image_key"])

    for field, value in updates.items():
        setattr(post, field, value)

    if "updated_date" not in updates:
        post.updated_date = utcnow()

    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    slug: str,
    session: Annotated[Session, Depends(get_session)],
    _admin: Annotated[None, Depends(require_admin)],
) -> Response:
    """Delete a blog post by slug (admin only)."""
    post = session.exec(select(Post).where(Post.slug == slug)).first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    session.delete(post)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
