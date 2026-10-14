"""Data models for culinary knowledge base entities and retrieval results."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RestaurantRecord(BaseModel):
    """Restaurant metadata model."""

    restaurant_id: str
    display_name: str
    locale: str
    location_label: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DishIngredientRecord(BaseModel):
    """Normalized ingredient record associated with a dish."""

    id: Optional[int] = None
    dish_id: str
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    verification_status: str = Field(default="unverified", description="'verified' or 'unverified'")


class AllergenEvidenceRecord(BaseModel):
    """Allergen verification record."""

    id: Optional[int] = None
    dish_id: str
    allergen: str
    status: str = Field(
        default="unknown",
        description="'contains', 'may_contain', 'not_listed', or 'unknown'",
    )
    evidence_source: str
    reviewer_metadata: Optional[str] = None
    updated_at: Optional[str] = None


class DishRecord(BaseModel):
    """Full culinary dish record."""

    dish_id: str
    restaurant_id: Optional[str] = None
    native_name: str
    aliases: List[str] = Field(default_factory=list)
    phonetic_spelling: Optional[str] = None
    canonical_category: Optional[str] = None
    base_ingredients: List[str] = Field(default_factory=list)
    cooking_technique: Optional[str] = None
    cultural_narrative: Optional[str] = None
    flavor_profile: Optional[str] = None
    known_allergens: List[str] = Field(default_factory=list)
    dietary_flags: Dict[str, Any] = Field(default_factory=dict)
    price_metadata: Optional[Dict[str, Any]] = None
    provenance: str
    verification_status: str = Field(default="unverified", description="'verified' or 'unverified'")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    ingredients: List[DishIngredientRecord] = Field(default_factory=list)
    allergen_evidence: List[AllergenEvidenceRecord] = Field(default_factory=list)


class RetrievedDish(BaseModel):
    """Retrieved dish result from hybrid RRF search."""

    dish: DishRecord
    rrf_score: float
    lexical_rank: Optional[int] = None
    vector_rank: Optional[int] = None
    exact_match: bool = False
    match_type: str = Field(
        default="unknown",
        description="'exact', 'fts', 'vector', or 'hybrid'",
    )
    is_authoritative: bool = Field(
        default=False,
        description="Whether score meets authoritative threshold and passes restaurant isolation",
    )
