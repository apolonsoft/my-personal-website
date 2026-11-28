"""Bearer token authentication dependency for admin write endpoints."""

import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


def is_admin_authenticated(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> bool:
    """Return True when the Bearer token matches the configured API_ADMIN_TOKEN."""
    settings = get_settings(request)
    if not settings.api_admin_token or credentials is None:
        return False
    if credentials.scheme.lower() != "bearer":
        return False
    return hmac.compare_digest(credentials.credentials, settings.api_admin_token)


def require_admin(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> None:
    """Enforce Bearer token authentication on protected routes."""
    if not is_admin_authenticated(request, credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
