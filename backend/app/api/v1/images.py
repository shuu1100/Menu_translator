"""API endpoints for food image discovery and matching."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from backend.app.schemas.image_search import (
    BatchImageSearchRequest,
    BatchImageSearchResponse,
    DishImageInfo,
    DishImageQuery,
)
from backend.app.services.images.service import (
    ImageSearchService,
    get_image_search_service,
)

router = APIRouter(prefix="/images", tags=["Images"])


@router.get(
    "/search",
    response_model=DishImageInfo,
    status_code=status.HTTP_200_OK,
    summary="Search for a representative food image for a single dish",
)
async def search_dish_image(
    dish_name: str = Query(..., description="Translated or primary dish name (e.g. 'Tonkotsu Ramen')"),
    dish_id: str = Query(default="single_query", description="Optional dish identifier"),
    native_name: Optional[str] = Query(default=None, description="Original name in native script"),
    transliteration: Optional[str] = Query(default=None, description="Phonetic transliteration"),
    cuisine: Optional[str] = Query(default=None, description="Cuisine or regional hint"),
    section: Optional[str] = Query(default=None, description="Menu section / category"),
    service: ImageSearchService = Depends(get_image_search_service),
) -> DishImageInfo:
    """Find a representative food photograph using intelligent semantic matching."""
    query = DishImageQuery(
        dish_id=dish_id,
        dish_name=dish_name,
        native_name=native_name,
        transliteration=transliteration,
        cuisine=cuisine,
        section=section,
    )
    return await service.search_single_dish(query)


@router.post(
    "/batch-search",
    response_model=BatchImageSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch search representative food images for multiple menu dishes",
)
async def batch_search_dish_images(
    request: BatchImageSearchRequest,
    service: ImageSearchService = Depends(get_image_search_service),
) -> BatchImageSearchResponse:
    """Find representative food photographs for an entire extracted menu in a single non-blocking request."""
    return await service.search_batch(request)
