"""Wikimedia Commons & Wikipedia REST API Image Provider Adapter.

Permitted open educational knowledge API:
- Zero API keys required.
- Provides public domain and Creative Commons food images.
- Enforces strict request timeouts and user-agent compliance.
"""

from typing import Optional
import urllib.parse
import httpx
from backend.app.core.logging import get_logger
from backend.app.schemas.image_search import DishImageInfo, DishImageQuery
from backend.app.services.images.providers.base import BaseImageProvider
from backend.app.services.images.query_builder import (
    clean_dish_name,
    infer_dish_category,
)

logger = get_logger("image_provider.wikimedia")

WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
USER_AGENT = "UniversalMenuTranslator/0.1.0 (culinary-rag@universalmenutranslator.org)"


class WikimediaImageProvider(BaseImageProvider):
    """Image provider querying Wikipedia / Wikimedia Commons summaries."""

    name = "wikimedia"

    def is_configured(self) -> bool:
        return True

    async def search_image(self, query: DishImageQuery, timeout_seconds: float = 3.5) -> Optional[DishImageInfo]:
        cleaned = clean_dish_name(query.dish_name)
        if not cleaned:
            return None

        category = infer_dish_category(cleaned, query.section, query.ingredients)

        # Title candidates: English title, original transliteration
        candidates = [cleaned.title()]
        if query.transliteration and query.transliteration.strip():
            candidates.append(query.transliteration.strip().title())

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            for cand in candidates:
                encoded = urllib.parse.quote(cand.replace(" ", "_"))
                url = f"{WIKIPEDIA_SUMMARY_URL}/{encoded}"
                try:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    originalimage = data.get("originalimage")
                    thumbnail = data.get("thumbnail")

                    if not originalimage and not thumbnail:
                        continue

                    image_url = originalimage.get("source") if originalimage else thumbnail.get("source")
                    thumb_url = thumbnail.get("source") if thumbnail else image_url
                    description = data.get("description") or data.get("extract") or cand

                    # Filter out non-food pages (e.g. cities, people, music)
                    desc_lower = description.lower()
                    food_markers = ["dish", "food", "cuisine", "soup", "noodle", "pasta", "bread", "dessert", "drink", "tea", "rice", "curry", "meat", "pastry"]
                    if not any(m in desc_lower for m in food_markers):
                        continue

                    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded}")

                    return DishImageInfo(
                        image_url=image_url,
                        thumbnail_url=thumb_url,
                        source="wikimedia",
                        photographer="Wikimedia Commons Contributors",
                        photographer_url=page_url,
                        source_url=page_url,
                        alt_text=f"Representative photograph of {query.dish_name} from Wikimedia Commons",
                        relevance_score=0.88,
                        is_fallback=False,
                        status="available",
                        query_used=cand,
                        dish_category=category,
                    )
                except httpx.TimeoutException:
                    logger.warning(f"Wikimedia summary timed out for '{cand}'")
                    continue
                except Exception as e:
                    logger.debug(f"Wikimedia summary check failed for '{cand}': {e}")
                    continue

        return None
