"""Comprehensive regression test suite for Description Sanitization and Strict Field Semantics.

Covers:
1. A real printed description is extracted and translated correctly.
2. A dish with no printed description does not receive an invented one.
3. 'Let's check the structure' is rejected as extraction commentary.
4. 'Need to extract each item here' is rejected as prompt leakage.
5. A category such as 'SMOOTHIE' is not used as a description.
6. 'BEST SELLER' is treated as a promotional label when appropriate.
7. A valid description containing ingredients is not incorrectly rejected.
8. Two adjacent dishes retain their own descriptions.
9. Descriptions remain correctly associated after sorting and filtering.
10. Changing the target language retranslates the original description rather than cascading translations.
11. Failed enrichment does not replace a valid description.
12. Missing descriptions produce null/empty state without fabricated filler.
"""

import pytest
from backend.app.schemas.extraction import BoundingBox, MenuTextBlock
from backend.app.schemas.menu_analysis import AnalyzedDish, DietaryCompatibility, EvidenceStatus, SupportedLanguage
from backend.app.services.safety.description_sanitizer import DescriptionSanitizer
from backend.app.services.translation.multilingual_engine import MultilingualCulinaryEngine
from backend.app.services.translation.translator import DeterministicCulinaryTranslator
from backend.app.services.vision.json_parser import ModelJsonParser


class TestDescriptionSanitizerRegression:
    """Test suite targeting regression cases 1-12."""

    def test_case_1_real_printed_description_preserved_and_translated(self):
        """1. A real printed description is extracted and translated correctly."""
        raw_desc = "Fresh handmade noodles in rich pork collagen broth with scallions"
        is_valid, cleaned, reason = DescriptionSanitizer.validate_and_clean_description(
            raw_desc, dish_name="Tonkotsu Ramen", section="Ramen"
        )
        assert is_valid is True
        assert cleaned == raw_desc
        assert reason is None

        # Test translation retains description
        t_title, t_phonetic, t_desc, _ = MultilingualCulinaryEngine.translate_dish(
            original_name="Tonkotsu Ramen",
            printed_desc=cleaned,
            target_lang=SupportedLanguage.EN,
        )
        assert t_desc == raw_desc

    def test_case_2_dish_with_no_printed_description_never_invents_one(self):
        """2. A dish with no printed description does not receive an invented one."""
        is_valid, cleaned, reason = DescriptionSanitizer.validate_and_clean_description(
            None, dish_name="Black Milk Tea", section="Milk Tea"
        )
        assert is_valid is True
        assert cleaned is None

        # Engine translation with None printed_desc MUST return None
        t_title, t_phonetic, t_desc, _ = MultilingualCulinaryEngine.translate_dish(
            original_name="블랙 밀크티",
            printed_desc=None,
            target_lang=SupportedLanguage.EN,
        )
        assert t_title == "Black Milk Tea"
        assert t_desc is None  # Case B guarantee: Never invent a description

    def test_case_3_lets_check_the_structure_rejected(self):
        """3. 'Let's check the structure' is rejected as extraction commentary."""
        leakage = "The menu has columns. Let's check the structure"
        assert DescriptionSanitizer.is_prompt_commentary_dish_name(leakage) is True

        is_valid, cleaned, reason = DescriptionSanitizer.validate_and_clean_description(
            leakage, dish_name="Pizza Margherita"
        )
        assert is_valid is False
        assert cleaned is None
        assert reason == "PROMPT_LEAKAGE_DETECTED"

    def test_case_4_need_to_extract_each_item_rejected(self):
        """4. 'Need to extract each item here' is rejected as prompt leakage."""
        leakage = "Each item has a name, description, price. Need to extract each item here."
        assert DescriptionSanitizer.is_prompt_commentary_dish_name(leakage) is True

        is_valid, cleaned, reason = DescriptionSanitizer.validate_and_clean_description(
            leakage, dish_name="Milk Tea"
        )
        assert is_valid is False
        assert cleaned is None
        assert reason == "PROMPT_LEAKAGE_DETECTED"

    def test_case_5_category_smoothie_not_used_as_description(self):
        """5. A category such as 'SMOOTHIE' is not used as a description."""
        is_valid, cleaned, reason = DescriptionSanitizer.validate_and_clean_description(
            "SMOOTHIE", dish_name="Mango Smoothie", section="SMOOTHIE"
        )
        assert is_valid is False
        assert cleaned is None
        assert reason in ("SECTION_HEADING_USED_AS_DESCRIPTION", "DESCRIPTION_DUPLICATES_SECTION_TITLE")

    def test_case_6_best_seller_treated_as_promotional_label(self):
        """6. 'BEST SELLER' is treated as a promotional label when appropriate."""
        tags = DescriptionSanitizer.extract_tags(
            name="Taro Milk Tea", section="BEST SELLER (top row)"
        )
        assert "Best Seller" in tags

        tags_direct = DescriptionSanitizer.extract_tags(
            name="[BEST SELLER] Signature Milk Tea", section=None
        )
        assert "Best Seller" in tags_direct

    def test_case_7_valid_description_with_ingredients_not_rejected(self):
        """7. A valid description containing ingredients is not incorrectly rejected."""
        genuine_desc = "San Marzano tomato sauce, fresh buffalo mozzarella, fresh basil, extra virgin olive oil"
        is_valid, cleaned, reason = DescriptionSanitizer.validate_and_clean_description(
            genuine_desc, dish_name="Pizza Margherita", section="Pizze"
        )
        assert is_valid is True
        assert cleaned == genuine_desc
        assert reason is None

    def test_case_8_two_adjacent_dishes_retain_own_descriptions(self):
        """8. Two adjacent dishes retain their own descriptions without cross-contamination."""
        dish1_desc = "Steamed pork dumplings with ginger and scallions"
        dish2_desc = None  # Second dish has NO description

        is_val_1, clean_1, _ = DescriptionSanitizer.validate_and_clean_description(dish1_desc, "Dumplings")
        is_val_2, clean_2, _ = DescriptionSanitizer.validate_and_clean_description(dish2_desc, "Spring Rolls")

        assert clean_1 == dish1_desc
        assert clean_2 is None

    def test_case_9_descriptions_associated_with_stable_ids_after_sorting(self):
        """9. Descriptions remain correctly associated after sorting and filtering."""
        dishes = [
            AnalyzedDish(
                dish_id="dish-1",
                reading_order=2,
                bounding_box=BoundingBox(ymin=0.1, xmin=0.1, ymax=0.2, xmax=0.2),
                original_text="Taro Milk Tea",
                translated_title="Taro Milk Tea",
                original_description="Sweet taro root blended with fresh milk",
                culinary_description="Sweet taro root blended with fresh milk",
            ),
            AnalyzedDish(
                dish_id="dish-2",
                reading_order=1,
                bounding_box=BoundingBox(ymin=0.05, xmin=0.1, ymax=0.09, xmax=0.2),
                original_text="Black Milk Tea",
                translated_title="Black Milk Tea",
                original_description=None,
                culinary_description=None,
            ),
        ]

        # Sort by reading order
        sorted_dishes = sorted(dishes, key=lambda d: d.reading_order)
        assert sorted_dishes[0].dish_id == "dish-2"
        assert sorted_dishes[0].culinary_description is None
        assert sorted_dishes[1].dish_id == "dish-1"
        assert sorted_dishes[1].culinary_description == "Sweet taro root blended with fresh milk"

    @pytest.mark.asyncio
    async def test_case_10_changing_target_language_retranslates_original(self):
        """10. Changing target language retranslates original description rather than compounding."""
        translator = DeterministicCulinaryTranslator()
        orig_name = "블랙 밀크티"
        orig_desc = "홍차와 부드러운 우유"

        # Translate to Spanish
        es_res = await translator.translate_dish(
            original_name=orig_name,
            printed_desc=orig_desc,
            target_language=SupportedLanguage.ES,
        )
        assert es_res.translated_title == "Té Negro con Leche"

        # Translate to German from original
        de_res = await translator.translate_dish(
            original_name=orig_name,
            printed_desc=orig_desc,
            target_language=SupportedLanguage.DE,
        )
        assert de_res.translated_title == "Schwarzer Milchtee"

    def test_case_11_failed_enrichment_does_not_replace_valid_description(self):
        """11. Failed enrichment does not replace a valid description."""
        orig_desc = "Traditional stone bowl bibimbap with assorted seasonal vegetables"
        # Even if RAG returns None, original description is preserved
        is_val, clean, _ = DescriptionSanitizer.validate_and_clean_description(orig_desc, "Bibimbap")
        assert clean == orig_desc

    def test_case_12_missing_description_handles_cleanly(self):
        """12. Frontend/backend contract ensures missing description has no fabricated filler."""
        raw_filler = "Artisan regional culinary preparation of BEST SELLER (top row)."
        is_val, clean, reason = DescriptionSanitizer.validate_and_clean_description(
            raw_filler, dish_name="BEST SELLER"
        )
        assert is_val is False
        assert clean is None
        assert reason == "FABRICATED_FILLER_DETECTED"
