"""Cloudflare R2 image upload, delivery, and deletion router."""

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlmodel import Session, select

from src.auth import require_admin
from src.config import get_settings
from src.database import get_session
from src.models import ImageAsset, ImageAssetRead
from src.storage import ImageStorage, get_storage

router = APIRouter(prefix="/api/images", tags=["images"])

ALLOWED_IMAGE_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/avif": ".avif",
    "image/gif": ".gif",
}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
_SAFE_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/-]*$")


def _validate_object_key(key: str) -> str:
    """Reject path traversal or unsafe R2 object keys."""
    normalized = key.lstrip("/")
    if not normalized or ".." in normalized or not _SAFE_KEY_PATTERN.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image object key.",
        )
    return normalized


def _build_public_url(request: Request, object_key: str) -> str:
    """Return the public delivery URL for a stored image key."""
    base_url = get_settings(request).r2_public_base_url
    if base_url:
        return f"{base_url}/{object_key}"
    return f"/api/images/{object_key}"


def _to_asset_read(request: Request, asset: ImageAsset) -> ImageAssetRead:
    """Map an ImageAsset ORM row to ImageAssetRead."""
    return ImageAssetRead(
        id=asset.id or 0,
        object_key=asset.object_key,
        filename=asset.filename,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        alt_text=asset.alt_text,
        url=_build_public_url(request, asset.object_key),
        created_at=asset.created_at,
    )


@router.post("", response_model=ImageAssetRead, status_code=status.HTTP_201_CREATED)
async def upload_image(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    storage: Annotated[ImageStorage, Depends(get_storage)],
    _admin: Annotated[None, Depends(require_admin)],
    file: UploadFile = File(...),
    alt_text: str = Form(default=""),
    object_key: Optional[str] = Form(default=None),
) -> ImageAssetRead:
    """Validate and upload an image to Cloudflare R2 and record its metadata in D1."""
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{content_type}'.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Image exceeds maximum size of {MAX_IMAGE_BYTES} bytes.",
        )

    if object_key:
        resolved_key = _validate_object_key(object_key)
    else:
        now = datetime.now(timezone.utc)
        ext = ALLOWED_IMAGE_TYPES[content_type]
        resolved_key = f"uploads/{now:%Y}/{now:%m}/{uuid4().hex}{ext}"

    existing = session.exec(
        select(ImageAsset).where(ImageAsset.object_key == resolved_key)
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Image asset '{resolved_key}' already exists.",
        )

    safe_filename = Path(file.filename or f"image{ALLOWED_IMAGE_TYPES[content_type]}").name
    await storage.put(resolved_key, data, content_type)

    asset = ImageAsset(
        object_key=resolved_key,
        filename=safe_filename,
        content_type=content_type,
        size_bytes=len(data),
        alt_text=alt_text,
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return _to_asset_read(request, asset)


@router.get("/{key:path}")
async def get_image(
    key: str,
    storage: Annotated[ImageStorage, Depends(get_storage)],
) -> Response:
    """Stream an image object from R2 with immutable caching headers."""
    resolved_key = _validate_object_key(key)
    stored = await storage.get(resolved_key)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    return Response(
        content=stored.data,
        media_type=stored.content_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.delete("/{key:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    key: str,
    session: Annotated[Session, Depends(get_session)],
    storage: Annotated[ImageStorage, Depends(get_storage)],
    _admin: Annotated[None, Depends(require_admin)],
) -> Response:
    """Delete an image from R2 and remove its ImageAsset record (admin only)."""
    resolved_key = _validate_object_key(key)
    asset = session.exec(
        select(ImageAsset).where(ImageAsset.object_key == resolved_key)
    ).first()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    await storage.delete(resolved_key)
    session.delete(asset)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
