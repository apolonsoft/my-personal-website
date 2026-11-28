"""Application settings resolved from Cloudflare Worker bindings or os.environ."""

from dataclasses import dataclass
import os
from typing import Any

from fastapi import Request


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the Blog CMS API."""

    api_admin_token: str
    jwt_secret: str
    jwt_expires_seconds: int
    database_url: str
    environment: str
    r2_public_base_url: str
    email_from: str
    email_from_name: str
    frontend_url: str


def _read_env_value(env: Any, key: str, default: str = "") -> str:
    """Read a string setting from a Worker env object or fall back to os.environ."""
    if env is not None:
        value = getattr(env, key, None)
        if isinstance(value, str) and value != "":
            return value
    return os.environ.get(key, default)


def _read_int_env(env: Any, key: str, default: int) -> int:
    raw = _read_env_value(env, key, str(default))
    try:
        parsed = int(raw)
        return parsed if parsed > 0 else default
    except ValueError:
        return default


def get_settings(request: Request | None = None) -> Settings:
    """Resolve Settings from the current request's Worker env or process environment."""
    env = request.scope.get("env") if request is not None else None
    api_admin_token = _read_env_value(env, "API_ADMIN_TOKEN", "")
    jwt_secret = _read_env_value(env, "JWT_SECRET", "") or api_admin_token
    return Settings(
        api_admin_token=api_admin_token,
        jwt_secret=jwt_secret,
        jwt_expires_seconds=_read_int_env(env, "JWT_EXPIRES_SECONDS", 86_400),
        database_url=_read_env_value(env, "DATABASE_URL", "sqlite:///./local.db"),
        environment=_read_env_value(env, "ENVIRONMENT", "development"),
        r2_public_base_url=_read_env_value(env, "R2_PUBLIC_BASE_URL", "").rstrip("/"),
        email_from=_read_env_value(env, "EMAIL_FROM", "noreply@apolonsoft.dev"),
        email_from_name=_read_env_value(env, "EMAIL_FROM_NAME", "Apolonsoft"),
        frontend_url=_read_env_value(env, "FRONTEND_URL", "https://www.apolonsoft.dev").rstrip("/"),
    )
