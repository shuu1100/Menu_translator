"""ImageSearchService orchestrating multi-provider food image discovery, caching, and fallback."""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.schemas.image_search import (
    BatchImageSearchRequest,
    BatchImageSearchResponse,
    DishImageInfo,
    DishImageQuery,
)
from backend.app.services.images.providers.base import BaseImageProvider
from backend.app.services.images.providers.curated import CuratedImageProvider
from backend.app.services.images.providers.pexels import PexelsImageProvider
from backend.app.services.images.providers.unsplash import UnsplashImageProvider
from backend.app.services.images.providers.wikimedia import WikimediaImageProvider
from backend.app.services.images.query_builder import (
    clean_dish_name,
    infer_dish_category,
)

logger = get_logger("services.image_search")


class ImageSearchService:
    """Orchestrates caching, concurrency, and provider fallbacks for food image discovery."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._cache: Dict[str, Tuple[DishImageInfo, float]] = {}  # key -> (info, expire_timestamp)
        self._semaphore = asyncio.Semaphore(self.settings.image_search_max_concurrency)

        # Initialize provider adapters
        self.unsplash = UnsplashImageProvider(access_key=self.settings.unsplash_access_key)
        self.pexels = PexelsImageProvider(api_key=self.settings.pexels_api_key)
        self.wikimedia = WikimediaImageProvider()
        self.curated = CuratedImageProvider()

    def _make_cache_key(self, query: DishImageQuery) -> str:
        """Create normalized cache key from dish name, cuisine, and category."""
        clean_name = clean_dish_name(query.dish_name)
        cuisine = (query.cuisine or "").lower().strip()
        section = (query.section or "").lower().strip()
        category = infer_dish_category(clean_name, section, query.ingredients)
        return f"{cuisine}:{category}:{clean_name}"

    def get_cached(self, cache_key: str) -> Optional[DishImageInfo]:
        """Retrieve result from cache if present and not expired."""
        if cache_key in self._cache:
            info, expires_at = self._cache[cache_key]
            if time.time() < expires_at:
                return info
            else:
                del self._cache[cache_key]
        return None

    def set_cache(self, cache_key: str, info: DishImageInfo) -> None:
        """Store result in cache with configured TTL."""
        # Evict oldest entries if cache exceeds 1000 items
        if len(self._cache) > 1000:
            oldest_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])[:100]
            for k in oldest_keys:
                self._cache.pop(k, None)

        expires_at = time.time() + self.settings.image_cache_ttl_seconds
        self._cache[cache_key] = (info, expires_at)

    async def search_single_dish(self, query: DishImageQuery) -> DishImageInfo:
        """Search for a representative food image with fallback cascade and bounded concurrency."""
        cache_key = self._make_cache_key(query)
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        async with self._semaphore:
            # Check cache again inside semaphore in case another task populated it
            cached = self.get_cached(cache_key)
            if cached:
                return cached

            timeout = self.settings.image_search_timeout_seconds
            chosen_info: Optional[DishImageInfo] = None

            # 1. If Unsplash configured and selected/auto, try Unsplash
            if self.unsplash.is_configured() and self.settings.image_search_provider in ("auto", "unsplash"):
                try:
                    chosen_info = await self.unsplash.search_image(query, timeout_seconds=timeout)
                except Exception as e:
                    logger.debug(f"Unsplash provider failed for '{query.dish_name}': {e}")

            # 2. If Pexels configured and selected/auto, try Pexels
            if not chosen_info and self.pexels.is_configured() and self.settings.image_search_provider in ("auto", "pexels"):
                try:
                    chosen_info = await self.pexels.search_image(query, timeout_seconds=timeout)
                except Exception as e:
                    logger.debug(f"Pexels provider failed for '{query.dish_name}': {e}")

            # 3. Check curated culinary photo directory (high quality, verified dishes)
            if not chosen_info:
                try:
                    curated_candidate = await self.curated.search_image(query, timeout_seconds=timeout)
                    if curated_candidate and not curated_candidate.is_fallback:
                        chosen_info = curated_candidate
                except Exception as e:
                    logger.debug(f"Curated provider failed for '{query.dish_name}': {e}")

            # 4. Check Wikimedia Commons summary
            if not chosen_info:
                try:
                    chosen_info = await self.wikimedia.search_image(query, timeout_seconds=timeout)
                except Exception as e:
                    logger.debug(f"Wikimedia provider failed for '{query.dish_name}': {e}")

            # 5. Fallback: generate neutral cuisine SVG placeholder
            if not chosen_info:
                chosen_info = await self.curated.search_image(query, timeout_seconds=timeout)

            # Store in cache
            if chosen_info:
                self.set_cache(cache_key, chosen_info)

            return chosen_info

    async def search_batch(self, request: BatchImageSearchRequest) -> BatchImageSearchResponse:
        """Process batch of dish queries asynchronously with deduplication."""
        results: Dict[str, DishImageInfo] = {}
        unique_tasks: Dict[str, asyncio.Task] = {}
        dish_to_key: Dict[str, str] = {}

        for dish in request.dishes:
            # Propagate request-level cuisine if not explicitly provided on dish
            if not dish.cuisine and request.cuisine:
                dish.cuisine = request.cuisine

            cache_key = self._make_cache_key(dish)
            dish_to_key[dish.dish_id] = cache_key

            # Deduplicate identical query strings
            if cache_key not in unique_tasks:
                task = asyncio.create_task(self.search_single_dish(dish))
                unique_tasks[cache_key] = task

        # Await all unique lookups concurrently
        key_results: Dict[str, DishImageInfo] = {}
        for key, task in unique_tasks.items():
            try:
                info = await task
                key_results[key] = info
            except Exception as e:
                logger.error(f"Error fetching image for key '{key}': {e}")
                # Fallback neutral placeholder
                key_results[key] = await self.curated.search_image(
                    DishImageQuery(dish_id="err", dish_name=key.split(":")[-1])
                )

        # Map back to each dish_id
        matched_count = 0
        provider_counts: Dict[str, int] = {}
        for dish_id, key in dish_to_key.items():
            res = key_results.get(key)
            if res:
                results[dish_id] = res
                if not res.is_fallback and res.status == "available":
                    matched_count += 1
                provider_counts[res.source] = provider_counts.get(res.source, 0) + 1

        primary_provider = max(provider_counts.items(), key=lambda x: x[1])[0] if provider_counts else "curated"

        return BatchImageSearchResponse(
            results=results,
            total_requested=len(request.dishes),
            total_matched=matched_count,
            provider_used=primary_provider,
        )


_service_instance: Optional[ImageSearchService] = None


def get_image_search_service() -> ImageSearchService:
    """Return singleton ImageSearchService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ImageSearchService()
    return _service_instance
