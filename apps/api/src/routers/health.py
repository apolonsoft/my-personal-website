"""Health check router."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return basic service health status."""
    return {"status": "ok", "service": "api"}
