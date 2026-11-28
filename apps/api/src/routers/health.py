"""Health check router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from src.database import get_session

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check(session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    """Verify service and database connectivity."""
    session.exec(text("SELECT 1")).first()
    return {"status": "ok", "service": "api", "database": "ok"}
