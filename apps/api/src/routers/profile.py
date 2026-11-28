"""Public and authenticated profile view/edit API router."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from auth import get_current_user
from config import get_settings
from database import get_session
from models import (
    ImageAsset,
    ProfileRead,
    ProfileUpdate,
    PublicProfileRead,
    User,
    utcnow,
)
from routers.auth import user_to_profile_read

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _resolve_avatar_url(request: Request, avatar_key: str) -> str:
    base_url = get_settings(request).r2_public_base_url
    if base_url:
        return f"{base_url}/{avatar_key}"
    return f"/api/images/{avatar_key}"


@router.get("", response_model=PublicProfileRead)
async def get_public_profile(
    session: Annotated[Session, Depends(get_session)],
) -> PublicProfileRead:
    """Return the primary active admin's public profile."""
    user = session.exec(
        select(User)
        .where(User.is_active == True)  # noqa: E712
        .order_by(User.id.asc())
        .limit(1)
    ).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile has not been initialized yet.",
        )

    profile = user_to_profile_read(user)
    return PublicProfileRead(
        full_name=profile.full_name,
        headline=profile.headline,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        social_links=profile.social_links,
    )


@router.get("/me", response_model=ProfileRead)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileRead:
    """Return the authenticated user's full profile."""
    return user_to_profile_read(current_user)


@router.patch("/me", response_model=ProfileRead)
async def update_my_profile(
    payload: ProfileUpdate,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileRead:
    """Partially update the authenticated user's profile."""
    updates = payload.model_dump(exclude_unset=True)

    new_email = updates.get("email")
    if new_email is not None and new_email != current_user.email:
        collision = session.exec(select(User).where(User.email == new_email)).first()
        if collision is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already in use.",
            )
        current_user.email = new_email

    if "avatar_key" in updates:
        avatar_key = updates["avatar_key"]
        if avatar_key is not None:
            asset = session.exec(
                select(ImageAsset).where(ImageAsset.object_key == avatar_key)
            ).first()
            if asset is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Avatar image asset '{avatar_key}' not found.",
                )
            if "avatar_url" not in updates or updates["avatar_url"] is None:
                current_user.avatar_url = _resolve_avatar_url(request, avatar_key)
        current_user.avatar_key = avatar_key

    if "social_links" in updates and updates["social_links"] is not None:
        current_user.social_links_json = json.dumps(
            {str(k): str(v) for k, v in updates["social_links"].items()}
        )

    for field in ("full_name", "headline", "bio", "avatar_url"):
        if field in updates and updates[field] is not None:
            setattr(current_user, field, updates[field])

    current_user.updated_at = utcnow()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return user_to_profile_read(current_user)
