"""Main FastAPI application entry point for Menu Translator."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1 import api_v1_router
from backend.app.api.v1.health import router as health_router
from backend.app.core.config import get_settings
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifespan manager."""
    settings = get_settings()
    logger = setup_logging(level=settings.log_level)
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"[env={settings.environment}, model={settings.vision_model}]"
    )
    yield
    logger.info(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Privacy-preserving, locally deployable restaurant menu translator backend. "
            "Integrates local VLM (Ollama), SQLite culinary knowledge base, and dietary safety."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Register central exception handlers
    register_exception_handlers(app)

    # Configure CORS for local Next.js frontend (supports localhost, 127.0.0.1, LAN IPs, and any local ports)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root_info() -> JSONResponse:
        return JSONResponse(
            content={
                "name": settings.app_name,
                "version": settings.app_version,
                "status": "online",
                "docs": "/docs",
                "health": "/health",
                "api_v1_health": "/api/v1/health",
            }
        )

    # Mount /health at root level
    app.include_router(health_router, prefix="", tags=["Health"])

    # Mount /api/v1 routes
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug or settings.environment == "development",
    )
