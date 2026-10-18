"""API v1 routers."""

from fastapi import APIRouter
from backend.app.api.v1.config import router as config_router
from backend.app.api.v1.extract import router as extract_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.images import router as images_router
from backend.app.api.v1.menus import router as menus_router
from backend.app.api.v1.translate import router as translate_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, prefix="")
api_v1_router.include_router(extract_router, prefix="")
api_v1_router.include_router(menus_router, prefix="")
api_v1_router.include_router(config_router, prefix="")
api_v1_router.include_router(images_router, prefix="")
api_v1_router.include_router(translate_router, prefix="")

__all__ = ["api_v1_router"]
