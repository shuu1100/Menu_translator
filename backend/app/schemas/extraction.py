"""Pydantic schemas for visual menu extraction."""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class BoundingBox(BaseModel):
    """
    Normalized bounding box coordinates in [0.0, 1.0] relative to original image dimensions.
    xmin: left edge (0.0 - 1.0)
    ymin: top edge (0.0 - 1.0)
    xmax: right edge (0.0 - 1.0)
    ymax: bottom edge (0.0 - 1.0)
    """

    xmin: float = Field(ge=0.0, le=1.0, description="Normalized left coordinate")
    ymin: float = Field(ge=0.0, le=1.0, description="Normalized top coordinate")
    xmax: float = Field(ge=0.0, le=1.0, description="Normalized right coordinate")
    ymax: float = Field(ge=0.0, le=1.0, description="Normalized bottom coordinate")

    # Optional pixel-absolute coordinates computed against original image
    pixel_x: Optional[int] = Field(default=None, description="Absolute pixel left")
    pixel_y: Optional[int] = Field(default=None, description="Absolute pixel top")
    pixel_width: Optional[int] = Field(default=None, description="Absolute pixel width")
    pixel_height: Optional[int] = Field(default=None, description="Absolute pixel height")

    @model_validator(mode="after")
    def validate_box_order(self) -> "BoundingBox":
        # Ensure min < max with a minimal epsilon tolerance
        if self.xmax < self.xmin:
            self.xmin, self.xmax = self.xmax, self.xmin
        if self.ymax < self.ymin:
            self.ymin, self.ymax = self.ymax, self.ymin
        if self.xmax == self.xmin:
            self.xmax = min(1.0, self.xmin + 0.01)
        if self.ymax == self.ymin:
            self.ymax = min(1.0, self.ymin + 0.01)
        return self

    def to_pixel_box(self, orig_width: int, orig_height: int) -> "BoundingBox":
        """Compute and populate pixel coordinates relative to original image size."""
        px = int(round(self.xmin * orig_width))
        py = int(round(self.ymin * orig_height))
        pw = max(1, int(round((self.xmax - self.xmin) * orig_width)))
        ph = max(1, int(round((self.ymax - self.ymin) * orig_height)))
        return BoundingBox(
            xmin=self.xmin,
            ymin=self.ymin,
            xmax=self.xmax,
            ymax=self.ymax,
            pixel_x=px,
            pixel_y=py,
            pixel_width=pw,
            pixel_height=ph,
        )


class MenuTextBlock(BaseModel):
    """Structured text block extracted from a menu section."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Stable block identifier")
    reading_order: int = Field(ge=0, description="Natural reading order sequence index")
    section: Optional[str] = Field(default=None, description="Menu section / category (e.g. Appetizers, Primi, Desserts)")
    original_name: str = Field(description="Dish name as printed in native script")
    phonetic_transcription: Optional[str] = Field(
        default=None, description="Optional phonetic transcription (pinyin, furigana, romaji)"
    )
    subtitle_or_description: Optional[str] = Field(
        default=None, description="Verbatim printed description or listed ingredients from the menu"
    )
    price_display: Optional[str] = Field(
        default=None, description="Verbatim price display string (e.g. '€14.50', '¥800', '$12', '18.-')"
    )
    currency: Optional[str] = Field(
        default=None, description="Currency symbol or ISO code when visible (e.g. '€', '$', '¥', 'EUR')"
    )
    text_region_type: str = Field(
        default="dish_item", description="Type of text region: dish_item, heading, description, price, or other"
    )
    bounding_box: BoundingBox = Field(description="Bounding box for this dish entry")
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Model extraction confidence score"
    )
    uncertainty_notes: Optional[str] = Field(
        default=None, description="Notes on ambiguous or partially legible characters"
    )


class ExtractionWarning(BaseModel):
    """Warning emitted during extraction without aborting the pipeline."""

    code: str = Field(description="Warning code identifier (e.g. LOW_CONTRAST, SKEWED_LAYOUT, MALFORMED_BLOCK)")
    message: str = Field(description="Human-readable warning explanation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic details")


class MenuExtractionResult(BaseModel):
    """Complete result of visual menu extraction."""

    menu_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique extraction session ID")
    source_language: Optional[str] = Field(
        default=None, description="Estimated primary language of the menu text (e.g. 'it', 'fr', 'ja', 'es')"
    )
    original_width: int = Field(gt=0, description="Original image width in pixels")
    original_height: int = Field(gt=0, description="Original image height in pixels")
    items: List[MenuTextBlock] = Field(default_factory=list, description="Extracted dish entries in reading order")
    warnings: List[ExtractionWarning] = Field(default_factory=list, description="Extraction warnings")
    processing_time_ms: float = Field(ge=0.0, description="Total pipeline latency in milliseconds")
    model_name: str = Field(description="Vision model used for extraction")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Fine-grained stage timings and hardware telemetry")

    # Safety Notice: extraction NEVER outputs allergen or health claims
    safety_notice: str = Field(
        default="Extraction stage preserves verbatim printed text only. Inferred allergen or safety claims are strictly prohibited at this stage.",
        description="Explicit safety guarantee banner",
    )
