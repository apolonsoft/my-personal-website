"""Application settings resolved from Cloudflare Worker bindings or os.environ."""

from dataclasses import dataclass
import os
from typing import Any

from fastapi import Request


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the Blog CMS API."""

    api_admin_token: str
    database_url: str
    environment: str
    r2_public_base_url: str


def _read_env_value(env: Any, key: str, default: str = "") -> str:
    """Read a string setting from a Worker env object or fall back to os.environ."""
    if env is not None:
        value = getattr(env, key, None)
        if isinstance(value, str) and value != "":
            return value
    return os.environ.get(key, default)


def get_settings(request: Request | None = None) -> Settings:
    """Resolve Settings from the current request's Worker env or process environment."""
    env = request.scope.get("env") if request is not None else None
    return Settings(
        api_admin_token=_read_env_value(env, "API_ADMIN_TOKEN", ""),
        database_url=_read_env_value(env, "DATABASE_URL", "sqlite:///./local.db"),
        environment=_read_env_value(env, "ENVIRONMENT", "development"),
        r2_public_base_url=_read_env_value(env, "R2_PUBLIC_BASE_URL", "").rstrip("/"),
    )
