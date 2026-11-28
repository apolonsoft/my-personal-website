"""Authentication dependencies supporting both API_ADMIN_TOKEN and HS256 JWTs."""

import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from config import get_settings
from database import get_session
from models import User
from security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


def is_admin_authenticated(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> bool:
    """Return True if Bearer token matches API_ADMIN_TOKEN or is a valid admin JWT."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        return False

    settings = get_settings(request)
    token = credentials.credentials

    if settings.api_admin_token and hmac.compare_digest(token, settings.api_admin_token):
        return True

    if settings.jwt_secret:
        payload = decode_access_token(token, settings.jwt_secret)
        if payload is not None and payload.get("role") == "admin":
            return True

    return False


async def require_admin(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> None:
    """Enforce admin Bearer authentication (API_ADMIN_TOKEN or admin JWT)."""
    if not is_admin_authenticated(request, credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    """Authenticate a Bearer JWT and return the active User record."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings(request)
    payload = decode_access_token(credentials.credentials, settings.jwt_secret)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
