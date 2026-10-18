"""Unsplash API Image Provider Adapter.

Follows official Unsplash API Guidelines:
- Sends 'Authorization: Client-ID <ACCESS_KEY>' header from backend environment only.
- Hotlinks image URLs directly from Unsplash CDN.
- Triggers non-blocking download tracking via 'download_location' endpoint.
- Implements required photographer and Unsplash attribution links with UTM parameters.
- Multi-candidate inspection: requests up to 5 candidates, scores relevance, filters non-food
  objects (laptops, people, interiors), and enforces category consistency (drinks vs soups).
- Enforces strict request timeouts, handles rate limits (HTTP 429 and X-Ratelimit-Remaining),
  and returns None conservatively when confidence is insufficient.
"""

import asyncio
from typing import List, Optional
import httpx
from backend.app.core.logging import get_logger
from backend.app.schemas.image_search import DishImageInfo, DishImageQuery
from backend.app.services.images.providers.base import BaseImageProvider
from backend.app.services.images.query_builder import (
    build_image_search_query,
    calculate_match_relevance,
    clean_dish_name,
)

logger = get_logger("image_provider.unsplash")

UNSPLASH_SEARCH_ENDPOINT = "https://api.unsplash.com/search/photos"
APP_NAME = "universal_menu_translator"

# Negative non-food terms to penalize or reject
UNRELATED_TERMS = {
    "laptop", "computer", "phone", "desk", "office", "person", "people", "portrait",
    "selfie", "woman", "man", "model", "crowd", "street", "building", "architecture",
    "interior", "furniture", "chair", "empty table", "scenery", "landscape", "nature",
    "forest", "mountain", "sky", "dog", "cat", "animal", "storefront", "shop", "neon sign"
}


class UnsplashImageProvider(BaseImageProvider):
    """Image provider using the official Unsplash API."""

    name = "unsplash"

    def __init__(self, access_key: Optional[str] = None):
        self.access_key = access_key.strip() if access_key else None
        self._rate_limit_remaining: Optional[int] = None

    def is_configured(self) -> bool:
        return bool(self.access_key and len(self.access_key) > 10)

    async def _track_download(self, download_location: str) -> None:
        """Trigger Unsplash download tracking endpoint asynchronously per API guidelines."""
        if not download_location or not self.is_configured():
            return
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                headers = {
                    "Authorization": f"Client-ID {self.access_key}",
                    "Accept-Version": "v1",
                }
                await client.get(download_location, headers=headers)
        except Exception as e:
            logger.debug(f"Unsplash download tracking ping failed: {e}")

    def _score_candidate(
        self,
        photo: dict,
        dish_name: str,
        native_name: Optional[str],
        category: str,
    ) -> float:
        """Score candidate photo (0.0 - 1.0) based on food relevance and category alignment."""
        desc = (photo.get("description") or "").lower()
        alt_desc = (photo.get("alt_description") or "").lower()
        tags = [t.get("title", "").lower() for t in photo.get("tags", []) if t.get("title")]
        combined_text = f"{desc} {alt_desc} {' '.join(tags)}"

        # 1. Base score from query builder keyword matching (includes category blacklists)
        score = calculate_match_relevance(
            query_dish_name=dish_name,
            query_category=category,
            candidate_title=f"{desc} {alt_desc}",
            candidate_tags=tags,
        )

        if score <= 0.0:
            return 0.0

        # 2. Check for native script tokens if present
        if native_name and native_name.strip():
            clean_native = native_name.strip().lower()
            if clean_native in combined_text:
                score += 0.20

        # 3. Penalize heavily for unrelated non-food scenes
        for term in UNRELATED_TERMS:
            if term in combined_text:
                score -= 0.40

        # 4. Small reward for positive culinary markers if already verified
        if score > 0.3 and any(w in combined_text for w in ["food", "dish", "meal", "recipe", "delicious", "drink", "dessert"]):
            score += 0.05

        return max(0.0, min(1.0, round(score, 2)))

    async def search_image(self, query: DishImageQuery, timeout_seconds: float = 3.5) -> Optional[DishImageInfo]:
        if not self.is_configured():
            return None

        # Check if rate limit was previously exhausted
        if self._rate_limit_remaining is not None and self._rate_limit_remaining <= 1:
            logger.warning("Unsplash API rate limit near exhaustion. Falling back to next provider.")
            return None

        primary_query, fallback_query, category = build_image_search_query(
            dish_name=query.dish_name,
            native_name=query.native_name,
            transliteration=query.transliteration,
            cuisine=query.cuisine,
            section=query.section,
            ingredients=query.ingredients,
        )

        # Conservative: If no reliable food keywords could be identified, do NOT query Unsplash
        # with generic terms like "Korean food" which return random sushi images
        if not primary_query:
            logger.debug(f"Skipping Unsplash search for ambiguous/unrecognized dish '{query.dish_name}'")
            return None

        headers = {
            "Authorization": f"Client-ID {self.access_key}",
            "Accept-Version": "v1",
        }

        # Build clean query list: try primary targeted query, then clean fallback
        queries_to_try = [primary_query]
        if fallback_query and fallback_query.lower() != primary_query.lower() and len(fallback_query) > 3:
            queries_to_try.append(f"{fallback_query} food")

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            for q in queries_to_try:
                try:
                    params = {
                        "query": q,
                        "page": 1,
                        "per_page": 5,
                        "orientation": "landscape",
                        "content_filter": "high",
                    }
                    resp = await client.get(UNSPLASH_SEARCH_ENDPOINT, params=params, headers=headers)

                    # Update rate limit tracking
                    remaining_hdr = resp.headers.get("X-Ratelimit-Remaining")
                    if remaining_hdr and remaining_hdr.isdigit():
                        self._rate_limit_remaining = int(remaining_hdr)

                    if resp.status_code == 429:
                        logger.warning("Unsplash API rate limit reached (HTTP 429).")
                        self._rate_limit_remaining = 0
                        return None
                    elif resp.status_code != 200:
                        logger.warning(f"Unsplash API returned HTTP {resp.status_code} for '{q}'")
                        continue

                    data = resp.json()
                    results: List[dict] = data.get("results", [])
                    if not results:
                        continue

                    # Evaluate candidate photos and select the highest scoring match
                    best_photo: Optional[dict] = None
                    best_score = -1.0

                    for candidate in results:
                        candidate_score = self._score_candidate(
                            photo=candidate,
                            dish_name=query.dish_name,
                            native_name=query.native_name,
                            category=category,
                        )
                        if candidate_score > best_score:
                            best_score = candidate_score
                            best_photo = candidate

                    # Conservative threshold: do not return low-confidence or irrelevant photos
                    if not best_photo or best_score < 0.60:
                        logger.debug(
                            f"Best Unsplash candidate for '{q}' scored {best_score} (< 0.60 threshold). Rejecting."
                        )
                        continue

                    photo = best_photo
                    urls = photo.get("urls", {})
                    user = photo.get("user", {})

                    image_url = urls.get("regular") or urls.get("small")
                    thumbnail_url = urls.get("small") or urls.get("thumb")
                    if not image_url:
                        continue

                    photo_id = photo.get("id")
                    photographer_name = user.get("name") or user.get("username") or "Unsplash Contributor"
                    user_profile = user.get("links", {}).get("html", "https://unsplash.com")
                    utm_photographer = f"{user_profile}?utm_source={APP_NAME}&utm_medium=referral"
                    photo_html = photo.get("links", {}).get("html", "https://unsplash.com")
                    utm_source = f"{photo_html}?utm_source={APP_NAME}&utm_medium=referral"

                    desc_text = photo.get("description") or photo.get("alt_description") or f"Representative photo of {query.dish_name}"
                    download_location = photo.get("links", {}).get("download_location")

                    # Trigger non-blocking download tracking per official Unsplash API Guidelines
                    if download_location:
                        asyncio.create_task(self._track_download(download_location))

                    return DishImageInfo(
                        image_url=image_url,
                        thumbnail_url=thumbnail_url,
                        source="unsplash",
                        photographer=photographer_name,
                        photographer_url=utm_photographer,
                        source_url=utm_source,
                        alt_text=f"Representative photo of {query.dish_name}",
                        relevance_score=best_score,
                        is_fallback=False,
                        status="available",
                        query_used=q,
                        dish_category=category,
                        photo_id=photo_id,
                    )

                except httpx.TimeoutException:
                    logger.warning(f"Unsplash request timed out for query '{q}'")
                    continue
                except Exception as e:
                    logger.error(f"Unsplash search error for query '{q}': {e}")
                    continue

        return None
