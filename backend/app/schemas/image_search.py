"""Schemas for automatic food image search and matching."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DishImageQuery(BaseModel):
    """Input query to search for a representative food image."""

    dish_id: str = Field(description="Unique identifier of the dish")
    dish_name: str = Field(description="Translated or primary dish name (e.g. 'Tonkotsu Ramen')")
    native_name: Optional[str] = Field(default=None, description="Original dish name in native script (e.g. '特製豚骨ラーメン')")
    transliteration: Optional[str] = Field(default=None, description="Phonetic romanization if available")
    cuisine: Optional[str] = Field(default=None, description="Cuisine or regional style (e.g. 'Japanese', 'Korean', 'Italian')")
    section: Optional[str] = Field(default=None, description="Menu section/category (e.g. 'Ramen', 'Dessert', 'Beverages')")
    ingredients: List[str] = Field(default_factory=list, description="Verified key ingredients")


class DishImageInfo(BaseModel):
    """Representative food photograph metadata with licensing & attribution."""

    image_url: str = Field(description="Primary image URL (optimized for card/drawer display)")
    thumbnail_url: Optional[str] = Field(default=None, description="Compact thumbnail URL")
    source: str = Field(default="curated", description="Image provider: 'unsplash', 'pexels', 'wikimedia', 'curated', or 'placeholder'")
    photographer: Optional[str] = Field(default=None, description="Photographer / creator credit")
    photographer_url: Optional[str] = Field(default=None, description="Link to photographer profile or source page")
    source_url: Optional[str] = Field(default=None, description="Link to source page on provider website")
    alt_text: str = Field(description="Descriptive alt text for accessibility")
    relevance_score: float = Field(default=1.0, description="Confidence score of dish-to-image match (0.0 to 1.0)")
    is_fallback: bool = Field(default=False, description="True if a neutral placeholder or generic category image was used")
    status: str = Field(default="available", description="'available', 'unavailable', or 'error'")
    query_used: Optional[str] = Field(default=None, description="Search query string that matched this image")
    dish_category: Optional[str] = Field(default=None, description="Inferred dish type (e.g. soup, noodles, dessert, beverage)")
    photo_id: Optional[str] = Field(default=None, description="Provider photo ID for download tracking or reference")


class BatchImageSearchRequest(BaseModel):
    """Batch search request for multiple dishes extracted from a menu."""

    dishes: List[DishImageQuery] = Field(description="List of dishes to find images for")
    cuisine: Optional[str] = Field(default=None, description="Global cuisine hint for the menu if known")


class BatchImageSearchResponse(BaseModel):
    """Batch search response mapping dish_id to DishImageInfo."""

    results: Dict[str, DishImageInfo] = Field(description="Mapping of dish_id to representative image info")
    total_requested: int
    total_matched: int
    provider_used: str
