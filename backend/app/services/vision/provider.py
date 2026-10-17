"""Abstract base interface for Menu Vision Providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from backend.app.schemas.extraction import MenuExtractionResult


class MenuVisionProvider(ABC):
    """Abstract interface for local and modular Vision-Language Model inference."""

    @abstractmethod
    async def check_health(self) -> bool:
        """Check if the vision provider runtime and configured model are operational."""
        pass

    @abstractmethod
    async def extract_menu(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        metadata: Optional[Dict[str, Any]] = None,
        apply_clahe: bool = False,
        rotation: int = 0,
    ) -> MenuExtractionResult:
        """
        Execute visual extraction on menu image bytes.
        Returns validated MenuExtractionResult without allergen or recipe claims.
        """
        pass
