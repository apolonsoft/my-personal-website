"""FastAPI application and Cloudflare Python Worker ASGI entrypoint."""

from typing import Any

_cached_app: Any = None


def create_app() -> Any:
    """Build and configure the FastAPI application."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from src.routers import health, images, posts

    application = FastAPI(
        title="Personal Website Blog CMS API",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(posts.router)
    application.include_router(images.router)
    return application


def _get_app() -> Any:
    """Lazily initialize and cache the FastAPI app on first Worker request."""
    global _cached_app
    if _cached_app is None:
        _cached_app = create_app()
    return _cached_app


try:
    from workers import WorkerEntrypoint, asgi

    class Default(WorkerEntrypoint):
        """Cloudflare Python Worker entrypoint that defers heavy imports until first fetch."""

        async def fetch(self, request: Any) -> Any:
            return await asgi.fetch(_get_app(), request, self.env, self.ctx)

except ImportError:
    # Local pytest / uvicorn imports run outside the Cloudflare Workers runtime.
    Default = None
    app = create_app()
