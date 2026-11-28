"""FastAPI application and Cloudflare Python Worker ASGI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import health

app = FastAPI(
    title="Personal Website Blog CMS API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router)

try:
    from workers import asgi

    Default = asgi.entrypoint(app)
except ImportError:
    # Local pytest / uvicorn imports run outside the Cloudflare Workers runtime.
    Default = None
