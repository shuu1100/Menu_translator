"""Pydantic schemas for the complete Menu Analysis pipeline contracts."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.extraction import BoundingBox, ExtractionWarning


class SupportedLanguage(str, Enum):
    """Supported target languages for menu translation."""

    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    JA = "ja"
    ZH = "zh"
    AR = "ar"
    IT = "it"
    PT = "pt"
    KO = "ko"


class EvidenceStatus(str, Enum):
    """Reliability level of culinary and allergen evidence."""

    CONFIRMED = "confirmed"      # Sourced directly from verified recipe database
    POSSIBLE = "possible"        # Sourced from printed description on physical menu
    UNVERIFIED = "unverified"    # Machine generated; unverified by authoritative culinary records
    NOT_LISTED = "not_listed"    # Available record does not list it; NOT proof of absence
    UNKNOWN = "unknown"          # Inconclusive or absent evidence


class DietaryFlagStatus(str, Enum):
    """Dietary compatibility assessment."""

    YES = "yes"
    NO = "no"
    POSSIBLE = "possible"
    UNKNOWN = "unknown"


class DietaryCompatibility(BaseModel):
    """Dietary lifestyle compatibility breakdown."""

    vegan: DietaryFlagStatus = DietaryFlagStatus.UNKNOWN
    vegetarian: DietaryFlagStatus = DietaryFlagStatus.UNKNOWN
    gluten_free: DietaryFlagStatus = DietaryFlagStatus.UNKNOWN
    halal: DietaryFlagStatus = DietaryFlagStatus.UNKNOWN
    user_conflicts: List[str] = Field(
        default_factory=list,
        description="List of user-specified restrictions that this dish may violate",
    )
    confidence_notes: Optional[str] = None


class AllergenWarning(BaseModel):
    """Specific allergen disclosure and evidence grounding."""

    allergen: str = Field(description="Identified allergen (e.g. gluten, dairy, nuts, shellfish)")
    status: EvidenceStatus = Field(
        default=EvidenceStatus.UNVERIFIED,
        description="Evidence status: confirmed, possible, unverified, not_listed, unknown",
    )
    source: str = Field(
        default="unverified_extraction",
        description="Source of finding: recipe_record, printed_menu, unverified_inference",
    )
    notes: Optional[str] = None
    icon: Optional[str] = Field(
        default=None,
        description="Accessibility icon name (e.g. alert-triangle, shield-alert, info)",
    )
    severity: str = Field(
        default="warning",
        description="Severity: critical (contains), warning (may_contain/unknown), advisory (not_listed)",
    )


class AnalyzedDish(BaseModel):
    """Fully analyzed dish record combining extraction, enrichment, and safety evaluation."""

    dish_id: str
    reading_order: int
    section: Optional[str] = None
    bounding_box: BoundingBox
    original_text: str = Field(description="Verbatim native script as printed")
    phonetic_transcription: Optional[str] = None
    translated_title: str = Field(description="Contextual translated dish title")
    culinary_description: Optional[str] = Field(
        default=None, description="Culinary explanation and cultural context"
    )
    flavor_profile: Optional[str] = Field(
        default=None, description="Flavor profile descriptors (e.g. savory, umami, spicy, sweet)"
    )
    key_ingredients: List[str] = Field(
        default_factory=list, description="Extracted or matched ingredients"
    )
    allergen_warnings: List[AllergenWarning] = Field(default_factory=list)
    dietary_compatibility: DietaryCompatibility = Field(default_factory=DietaryCompatibility)
    price: Optional[str] = None
    currency: Optional[str] = None
    evidence_status: EvidenceStatus = Field(
        default=EvidenceStatus.UNVERIFIED,
        description="Authoritative status of culinary data",
    )


class StageTiming(BaseModel):
    """Timing for an individual pipeline execution stage."""

    stage: str
    duration_ms: float


class ProcessingMetadata(BaseModel):
    """Metadata regarding processing duration, models, and pipeline diagnostics."""

    request_id: str
    total_latency_ms: float
    model_name: str
    retrieval_status: str = Field(
        default="stubbed_not_run",
        description="Status of RAG knowledge base retrieval (stubbed in Phase 3)",
    )
    stages: List[StageTiming] = Field(default_factory=list)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)


class MenuMetadata(BaseModel):
    """Menu document level metadata."""

    source_language: Optional[str] = None
    target_language: SupportedLanguage
    image_width: int
    image_height: int
    dish_count: int
    restaurant_id: Optional[str] = None
    warnings: List[ExtractionWarning] = Field(default_factory=list)


class MenuAnalysisResponse(BaseModel):
    """Unified response payload for POST /api/v1/menus/analyze."""

    menu_metadata: MenuMetadata
    dishes: List[AnalyzedDish] = Field(default_factory=list)
    processing_metadata: ProcessingMetadata
    safety_disclaimer: str = Field(
        default=(
            "CRITICAL SAFETY NOTICE: Allergen and dietary data at this stage are unverified. "
            "Never rely solely on AI for life-threatening allergies. Confirm all ingredients with restaurant staff."
        )
    )
