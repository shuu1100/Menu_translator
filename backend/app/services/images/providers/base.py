"""Abstract Base Class for Image Search Providers."""

from abc import ABC, abstractmethod
from typing import Optional
from backend.app.schemas.image_search import DishImageInfo, DishImageQuery


class BaseImageProvider(ABC):
    """Abstract interface for image providers (Unsplash, Pexels, Wikimedia, Curated)."""

    name: str = "base"

    @abstractmethod
    async def search_image(self, query: DishImageQuery, timeout_seconds: float = 3.5) -> Optional[DishImageInfo]:
        """Search for a representative food image matching the dish query.

        Returns DishImageInfo if found and confident, or None.
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if this provider is active and has required credentials."""
        pass
