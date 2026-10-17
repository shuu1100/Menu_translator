"""Pexels API Image Provider Adapter.

Follows official Pexels API guidelines:
- Sends 'Authorization: <API_KEY>' header from backend environment only.
- Implements required attribution linking to photographer and Pexels.
- Enforces strict request timeouts and handles rate limits (HTTP 429).
"""

from typing import Optional
import httpx
from backend.app.core.logging import get_logger
from backend.app.schemas.image_search import DishImageInfo, DishImageQuery
from backend.app.services.images.providers.base import BaseImageProvider
from backend.app.services.images.query_builder import (
    build_image_search_query,
    calculate_match_relevance,
)

logger = get_logger("image_provider.pexels")

PEXELS_SEARCH_ENDPOINT = "https://api.pexels.com/v1/search"


class PexelsImageProvider(BaseImageProvider):
    """Image provider using the official Pexels API."""

    name = "pexels"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def search_image(self, query: DishImageQuery, timeout_seconds: float = 3.5) -> Optional[DishImageInfo]:
        if not self.is_configured():
            return None

        primary_query, fallback_query, category = build_image_search_query(
            dish_name=query.dish_name,
            native_name=query.native_name,
            transliteration=query.transliteration,
            cuisine=query.cuisine,
            section=query.section,
            ingredients=query.ingredients,
        )

        headers = {
            "Authorization": self.api_key,
        }

        queries_to_try = [primary_query]
        if fallback_query and fallback_query.lower() != primary_query.lower():
            queries_to_try.append(fallback_query)

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            for q in queries_to_try:
                try:
                    params = {
                        "query": f"{q} food",
                        "per_page": 1,
                        "orientation": "landscape",
                    }
                    resp = await client.get(PEXELS_SEARCH_ENDPOINT, params=params, headers=headers)

                    if resp.status_code == 429:
                        logger.warning("Pexels API rate limit reached (HTTP 429). Falling back.")
                        return None
                    elif resp.status_code != 200:
                        logger.warning(f"Pexels API returned status {resp.status_code}")
                        continue

                    data = resp.json()
                    photos = data.get("photos", [])
                    if not photos:
                        continue

                    photo = photos[0]
                    src = photo.get("src", {})
                    image_url = src.get("medium") or src.get("large") or src.get("original")
                    thumbnail_url = src.get("small") or src.get("tiny") or image_url

                    if not image_url:
                        continue

                    photographer = photo.get("photographer", "Pexels Creator")
                    photographer_url = photo.get("photographer_url", "https://www.pexels.com")
                    source_url = photo.get("url", "https://www.pexels.com")
                    alt_text = photo.get("alt") or f"Representative food photo of {query.dish_name}"

                    score = calculate_match_relevance(
                        query_dish_name=query.dish_name,
                        query_category=category,
                        candidate_title=alt_text,
                        candidate_tags=[q],
                    )

                    return DishImageInfo(
                        image_url=image_url,
                        thumbnail_url=thumbnail_url,
                        source="pexels",
                        photographer=photographer,
                        photographer_url=photographer_url,
                        source_url=source_url,
                        alt_text=alt_text,
                        relevance_score=score,
                        is_fallback=False,
                        status="available",
                        query_used=q,
                        dish_category=category,
                    )

                except httpx.TimeoutException:
                    logger.warning(f"Pexels request timed out for query '{q}'")
                    continue
                except Exception as e:
                    logger.error(f"Pexels search error for query '{q}': {e}")
                    continue

        return None
