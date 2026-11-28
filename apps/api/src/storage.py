"""Cloudflare R2 object storage abstraction and in-memory test implementation."""

from dataclasses import dataclass
from typing import Any, Optional, Protocol

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class StoredObject:
    """Binary object payload and content type retrieved from storage."""

    data: bytes
    content_type: str


class ImageStorage(Protocol):
    """Storage interface for image assets."""

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        """Store `data` at `key` with the given MIME `content_type`."""
        ...

    async def get(self, key: str) -> Optional[StoredObject]:
        """Fetch an object by `key`, or return None if missing."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete an object by `key`. Return True if deleted or absent."""
        ...


class R2ImageStorage:
    """Adapter over a Cloudflare Workers R2 bucket binding."""

    def __init__(self, bucket: Any) -> None:
        self._bucket = bucket

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await self._bucket.put(
            key,
            data,
            httpMetadata={"contentType": content_type},
        )

    async def get(self, key: str) -> Optional[StoredObject]:
        obj = await self._bucket.get(key)
        if obj is None:
            return None
        raw = await obj.arrayBuffer()
        data = bytes(raw.to_py()) if hasattr(raw, "to_py") else bytes(raw)
        http_meta = getattr(obj, "httpMetadata", None)
        content_type = (
            getattr(http_meta, "contentType", None)
            or (http_meta.get("contentType") if isinstance(http_meta, dict) else None)
            or "application/octet-stream"
        )
        return StoredObject(data=data, content_type=content_type)

    async def delete(self, key: str) -> bool:
        await self._bucket.delete(key)
        return True


class InMemoryImageStorage:
    """In-memory object store used by unit and integration tests."""

    def __init__(self) -> None:
        self._objects: dict[str, StoredObject] = {}

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self._objects[key] = StoredObject(data=data, content_type=content_type)

    async def get(self, key: str) -> Optional[StoredObject]:
        return self._objects.get(key)

    async def delete(self, key: str) -> bool:
        return self._objects.pop(key, None) is not None


async def get_storage(request: Request) -> ImageStorage:
    """Resolve the R2 bucket binding from the Cloudflare Worker environment."""
    env = request.scope.get("env")
    bucket = getattr(env, "IMAGES_BUCKET", None) if env is not None else None
    if bucket is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="R2 IMAGES_BUCKET binding is not configured.",
        )
    return R2ImageStorage(bucket)
