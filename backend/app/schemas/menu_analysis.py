"""Pydantic schemas for the complete Menu Analysis pipeline contracts."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.extraction import BoundingBox, ExtractionWarning
from backend.app.schemas.image_search import DishImageInfo


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
    HI = "hi"
    RU = "ru"

    @classmethod
    def from_code(cls, code: str) -> "SupportedLanguage":
        """Normalize language code (e.g. 'zh-CN' -> 'zh', 'ES' -> 'es')."""
        if not code:
            return cls.EN
        c = code.lower().strip()
        if c in ("zh-cn", "zh_cn", "zh-hans"):
            return cls.ZH
        if c in ("pt-br", "pt_br", "pt-pt"):
            return cls.PT
        for item in cls:
            if item.value == c:
                return item
        # Try 2-letter prefix
        prefix = c.split("-")[0].split("_")[0]
        for item in cls:
            if item.value == prefix:
                return item
        raise ValueError(f"Unsupported language code '{code}'")


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

    # Primary identifiers & reading order
    dish_id: str
    id: Optional[str] = None
    reading_order: int
    section: Optional[str] = None
    category: Optional[str] = None
    section_original: Optional[str] = None
    section_translated: Optional[str] = None
    tags: List[str] = Field(default_factory=list, description="Promotional or category badges (e.g. Best Seller, New, Signature)")
    bounding_box: BoundingBox

    # Names and Pronunciation
    original_text: str = Field(description="Verbatim native dish name as printed")
    original_name: Optional[str] = Field(default=None, description="Exact source-language dish name")
    translated_title: str = Field(description="Contextual translated dish title")
    translated_name: Optional[str] = Field(default=None, description="Translated dish name")
    phonetic_transcription: Optional[str] = None
    transliteration: Optional[str] = None

    # Descriptions
    original_description: Optional[str] = Field(
        default=None, description="Verbatim native description printed on the menu"
    )
    culinary_description: Optional[str] = Field(
        default=None, description="Faithful translation of printed description (or None if none printed)"
    )
    translated_description: Optional[str] = Field(
        default=None, description="Faithful translation of the printed description"
    )
    generated_description: Optional[str] = Field(
        default=None, description="Optional AI-generated culinary narrative, clearly labelled as non-printed"
    )
    flavor_profile: Optional[str] = Field(
        default=None, description="Flavor profile descriptors (e.g. savory, umami, spicy, sweet)"
    )

    # Prices
    price: Optional[str] = None
    currency: Optional[str] = None
    price_value: Optional[float] = None
    price_currency: Optional[str] = None
    price_text_original: Optional[str] = None

    # Ingredients & Grounding
    key_ingredients: List[str] = Field(
        default_factory=list, description="Extracted or matched ingredients"
    )
    ingredients_original: List[str] = Field(
        default_factory=list, description="Ingredients explicitly listed in the source"
    )
    ingredients_translated: List[str] = Field(
        default_factory=list, description="Translations of those ingredients"
    )
    ingredients_verified: List[str] = Field(
        default_factory=list, description="Ingredients confirmed through trusted source"
    )
    ingredient_evidence_status: EvidenceStatus = Field(
        default=EvidenceStatus.NOT_LISTED,
        description="Explicit status describing where the ingredient info came from",
    )

    # Allergens, Nutrition & Dietary Safety
    allergen_warnings: List[AllergenWarning] = Field(default_factory=list)
    allergens: List[AllergenWarning] = Field(default_factory=list)
    nutrition: Optional[Dict[str, Any]] = None
    dietary_compatibility: DietaryCompatibility = Field(default_factory=DietaryCompatibility)
    dietary_evidence: Dict[str, str] = Field(default_factory=dict)
    confidence: Optional[float] = Field(default=0.95, description="Extraction confidence score")
    source_evidence: Optional[str] = None
    evidence_status: EvidenceStatus = Field(
        default=EvidenceStatus.UNVERIFIED,
        description="Authoritative status of culinary data",
    )
    representative_image: Optional[DishImageInfo] = Field(
        default=None,
        description="Matched representative food photograph metadata with licensing & attribution",
    )

    def model_post_init(self, __context: Any) -> None:
        """Synchronize aliases bidirectionally to ensure full contract adherence."""
        if not self.id:
            self.id = self.dish_id
        if not self.original_name:
            self.original_name = self.original_text
        if not self.translated_name:
            self.translated_name = self.translated_title
        if not self.transliteration:
            self.transliteration = self.phonetic_transcription
        if not self.translated_description:
            self.translated_description = self.culinary_description
        if not self.section_original:
            self.section_original = self.section
        if not self.price_text_original and self.price:
            self.price_text_original = self.price
        if not self.price_currency and self.currency:
            self.price_currency = self.currency
        if not self.allergens and self.allergen_warnings:
            self.allergens = self.allergen_warnings
        if not self.key_ingredients and self.ingredients_translated:
            self.key_ingredients = self.ingredients_translated
        elif not self.ingredients_translated and self.key_ingredients:
            self.ingredients_translated = self.key_ingredients


class StageTiming(BaseModel):
    """Timing for an individual pipeline execution stage."""

    stage: str
    duration_ms: float
    request_id: Optional[str] = None


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


class RetranslateRequest(BaseModel):
    """Request payload to retranslate existing dishes to a new target language."""

    dishes: List[AnalyzedDish]
    target_language: str
    user_dietary_restrictions: Optional[List[str]] = None


class RetranslateResponse(BaseModel):
    """Response payload containing retranslated dishes."""

    dishes: List[AnalyzedDish]
    target_language: str

