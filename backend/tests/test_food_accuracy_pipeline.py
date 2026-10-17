"""Comprehensive regression suite for Food Data Accuracy, Ingredient Grounding, and Schema Contracts."""

import pytest
from backend.app.schemas.menu_analysis import (
    AnalyzedDish,
    EvidenceStatus,
    DietaryFlagStatus,
    DietaryCompatibility,
    BoundingBox,
)
from backend.app.services.safety.description_sanitizer import DescriptionSanitizer
from backend.app.services.safety.safety_engine import CulinarySafetyEngine
from backend.app.services.vision.json_parser import ModelJsonParser, sanitize_dish_item


class TestFoodDataAccuracyAndIngredients:
    """Verify end-to-end food data accuracy and strict field separation."""

    def test_watermarks_and_blog_stamps_rejected(self):
        """Watermark strings like '티스토리' or 'tistory.com' must never be extracted as dishes."""
        assert DescriptionSanitizer.is_watermark_or_artifact("티스토리") is True
        assert DescriptionSanitizer.is_watermark_or_artifact("tistory.com") is True
        assert DescriptionSanitizer.is_watermark_or_artifact("blog.naver.com") is True
        assert DescriptionSanitizer.is_watermark_or_artifact("블로그") is True
        assert DescriptionSanitizer.is_prompt_commentary_dish_name("티스토리") is True

        # Valid food names must NOT be rejected
        assert DescriptionSanitizer.is_watermark_or_artifact("블랙 밀크티") is False
        assert DescriptionSanitizer.is_watermark_or_artifact("Shoyu Ramen") is False

    def test_section_heading_cleaning_and_prompt_leakage_removal(self):
        """Section titles like 'BEST SELLER section (not to be included as an item)' must be cleaned."""
        raw_sec = "BEST SELLER section (not to be included as an item)"
        cleaned = DescriptionSanitizer.clean_section_title(raw_sec)
        assert cleaned == "BEST SELLER"

        raw_sec_2 = "NEW (SALTY & SWEET) section"
        cleaned_2 = DescriptionSanitizer.clean_section_title(raw_sec_2)
        assert cleaned_2 == "NEW (SALTY & SWEET)"

        raw_sec_3 = "MILK TEA (not an item)"
        cleaned_3 = DescriptionSanitizer.clean_section_title(raw_sec_3)
        assert cleaned_3 == "MILK TEA"

    def test_price_never_treated_as_culinary_description(self):
        """Strings like 'price L6.1 J', 'L 6.1 / J', or '4.5 / 5.6' must be rejected as descriptions."""
        # Check direct price rejection
        is_valid, desc, reason = DescriptionSanitizer.validate_and_clean_description("price L6.1 J")
        assert is_valid is False
        assert desc is None
        assert reason == "PRICE_DATA_IN_DESCRIPTION"

        is_valid_2, desc_2, reason_2 = DescriptionSanitizer.validate_and_clean_description("L6.1 / J")
        assert is_valid_2 is False
        assert desc_2 is None
        assert reason_2 == "PRICE_DATA_IN_DESCRIPTION"

        is_valid_3, desc_3, reason_3 = DescriptionSanitizer.validate_and_clean_description("L 5.8")
        assert is_valid_3 is False
        assert desc_3 is None

    def test_sanitize_dish_item_moves_price_from_desc_to_price(self):
        """If model returns price in subtitle_or_description, it must be moved to price and cleared from desc."""
        name, desc, price, is_header = sanitize_dish_item(
            raw_name="블랙 밀크티",
            raw_desc="price L6.1 J",
            raw_price=None,
        )
        assert name == "블랙 밀크티"
        assert desc is None  # Description cleared!
        assert "L6.1" in price  # Moved to price!
        assert not is_header

    def test_zero_description_as_ingredients_hallucination(self):
        """A dish description or absence of ingredients must NOT create fabricated ingredients."""
        # Case A: Dish with no printed ingredients
        dish = AnalyzedDish(
            dish_id="dish_tea_01",
            reading_order=1,
            section="MILK TEA",
            bounding_box=BoundingBox(xmin=0.0, ymin=0.0, xmax=0.5, ymax=0.5),
            original_text="흑당 밀크티",
            translated_title="Brown Sugar Milk Tea",
            culinary_description=None,
            price="L 5.5",
            currency="₩",
            key_ingredients=[],
            ingredients_original=[],
            ingredients_translated=[],
            ingredient_evidence_status=EvidenceStatus.NOT_LISTED,
        )

        assert dish.key_ingredients == []
        assert dish.ingredients_original == []
        assert dish.ingredients_translated == []
        assert dish.ingredient_evidence_status == EvidenceStatus.NOT_LISTED
        # Verify schema aliases
        assert dish.id == "dish_tea_01"
        assert dish.original_name == "흑당 밀크티"
        assert dish.translated_name == "Brown Sugar Milk Tea"
        assert dish.price_text_original == "L 5.5"

    def test_unverified_dietary_status_does_not_generate_false_user_conflicts(self):
        """When user selects dietary restrictions, UNKNOWN status must NOT raise an active conflict badge."""
        dietary = DietaryCompatibility(
            vegan=DietaryFlagStatus.UNKNOWN,
            vegetarian=DietaryFlagStatus.UNKNOWN,
            gluten_free=DietaryFlagStatus.UNKNOWN,
            halal=DietaryFlagStatus.UNKNOWN,
        )

        # User enables gluten, dairy, and vegan filters
        user_restrictions = ["gluten", "dairy", "vegan"]
        conflicts = CulinarySafetyEngine.calculate_user_conflicts(
            dietary=dietary,
            allergens=[],
            user_restrictions=user_restrictions,
            extracted_ingredients=[],
        )

        # Must NOT generate conflict badges when evidence is merely unknown
        assert conflicts == []

    def test_confirmed_violation_generates_active_conflict(self):
        """When an ingredient explicitly violates a restriction, conflict must be raised."""
        dietary = DietaryCompatibility(
            vegan=DietaryFlagStatus.NO,
            vegetarian=DietaryFlagStatus.YES,
            gluten_free=DietaryFlagStatus.NO,
            halal=DietaryFlagStatus.YES,
        )

        user_restrictions = ["vegan", "gluten"]
        conflicts = CulinarySafetyEngine.calculate_user_conflicts(
            dietary=dietary,
            allergens=[],
            user_restrictions=user_restrictions,
            extracted_ingredients=["fresh cow milk", "wheat flour"],
        )

        assert any("vegan" in c.lower() for c in conflicts)
        assert any("gluten" in c.lower() for c in conflicts)

    def test_transliteration_never_concatenated_into_translated_title(self):
        """Phonetic transcription must remain in its own separate field, not concatenated to translated title."""
        dish = AnalyzedDish(
            dish_id="dish_02",
            reading_order=2,
            bounding_box=BoundingBox(xmin=0.0, ymin=0.0, xmax=0.5, ymax=0.5),
            original_text="블랙 밀크티",
            translated_title="Black Milk Tea",
            phonetic_transcription="Beullaek Milkeuti",
        )

        assert dish.translated_title == "Black Milk Tea"
        assert dish.phonetic_transcription == "Beullaek Milkeuti"
        assert "Beullaek" not in dish.translated_title
        assert dish.transliteration == "Beullaek Milkeuti"
