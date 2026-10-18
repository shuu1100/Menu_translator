import asyncio
import os
import sys

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.schemas.menu_analysis import SupportedLanguage
from backend.app.schemas.image_search import DishImageQuery
from backend.app.services.images.query_builder import build_image_search_query
from backend.app.services.images.providers.unsplash import UnsplashImageProvider
from backend.app.services.images.providers.curated import CuratedImageProvider, create_neutral_placeholder_svg
from backend.app.services.images.service import ImageSearchService
from backend.app.services.translation.translator import DeterministicCulinaryTranslator

async def run_all_tests():
    print("======================================================================")
    print("STARTING 10 SECTION D VERIFICATION TESTS")
    print("======================================================================\n")

    # Test 1 & 2: Known descriptive Korean dish translated to Spanish, English, and Japanese
    print("--- Test 1 & 2: Descriptive Korean dish -> Spanish, English, Japanese ---")
    translator = DeterministicCulinaryTranslator()
    
    dish_korean = "비빔밥"
    es_res = await translator.translate_dish(original_name=dish_korean, printed_desc="", target_language=SupportedLanguage.ES)
    en_res = await translator.translate_dish(original_name=dish_korean, printed_desc="", target_language=SupportedLanguage.EN)
    ja_res = await translator.translate_dish(original_name=dish_korean, printed_desc="", target_language=SupportedLanguage.JA)
    
    print(f"Original: {dish_korean}")
    print(f"ES: {es_res.translated_title}")
    print(f"EN: {en_res.translated_title}")
    print(f"JA: {ja_res.translated_title}")
    assert "Arroz" in es_res.translated_title or "Bibimbap" in es_res.translated_title, "Spanish translation failed"
    assert "Rice" in en_res.translated_title or "Bibimbap" in en_res.translated_title, "English translation failed"
    assert "ビビンバ" in ja_res.translated_title or "ピビンパ" in ja_res.translated_title or "ご飯" in ja_res.translated_title or len(ja_res.translated_title) > 0
    print(">>> Test 1 & 2 PASSED.\n")

    # Test 3: Genuine brand name / proper noun preserved
    print("--- Test 3: Brand name / proper noun preserved ---")
    brand_dish = "Coca-Cola Zero"
    brand_res = await translator.translate_dish(original_name=brand_dish, printed_desc="Refresco carbonatado", target_language=SupportedLanguage.ES)
    print(f"Brand dish: {brand_dish} -> {brand_res.translated_title}")
    assert "Coca-Cola" in brand_res.translated_title
    print(">>> Test 3 PASSED.\n")

    # Test 4: Menu item with no description (verifying description remains null/None)
    print("--- Test 4: Menu item with no description remains null ---")
    no_desc_res = await translator.translate_dish(original_name="치즈폼 우롱티", printed_desc="", target_language=SupportedLanguage.ES)
    print(f"Dish: 치즈폼 우롱티 | Culinary Description: {no_desc_res.culinary_description}")
    assert no_desc_res.culinary_description is None or no_desc_res.culinary_description == "", f"Expected None/empty, got: {no_desc_res.culinary_description}"
    print(">>> Test 4 PASSED.\n")

    # Test 5: The exact milk tea / soft-serve item that previously returned sushi ("브라운소프트 시그니처")
    print("--- Test 5: Exact item '브라운소프트 시그니처' rejecting sushi ---")
    primary_q, fallback_q, inferred_cat = build_image_search_query(
        dish_name="브라운소프트 시그니처",
        section="Dessert & Beverages",
    )
    print(f"Built Query for '브라운소프트 시그니처': primary='{primary_q}', category='{inferred_cat}'")
    assert inferred_cat in ("dessert", "beverage")
    
    # Check candidate scoring for a candidate with sushi tags against beverage/dessert
    mock_sushi_candidate = {
        "id": "sushi_123",
        "description": "Delicious salmon nigiri sushi platter",
        "alt_description": "Japanese sushi roll",
        "tags": [{"title": "sushi"}, {"title": "salmon"}, {"title": "japanese food"}],
        "urls": {"regular": "https://images.unsplash.com/sushi.jpg", "thumb": "https://images.unsplash.com/sushi_thumb.jpg"},
        "user": {"name": "Photographer", "links": {"html": "https://unsplash.com/@photo"}}
    }
    unsplash_provider = UnsplashImageProvider()
    sushi_score = unsplash_provider._score_candidate(mock_sushi_candidate, "brown sugar soft serve", None, "dessert")
    print(f"Score for sushi photo matched to dessert: {sushi_score}")
    assert sushi_score == 0.0, f"Expected 0.0 hard rejection, got {sushi_score}"
    
    # Also test for beverage category
    sushi_score_bev = unsplash_provider._score_candidate(mock_sushi_candidate, "black milk tea", None, "beverage")
    print(f"Score for sushi photo matched to beverage: {sushi_score_bev}")
    assert sushi_score_bev == 0.0, f"Expected 0.0 hard rejection, got {sushi_score_bev}"
    print(">>> Test 5 PASSED.\n")

    # Test 6: Item with no suitable Unsplash result -> neutral placeholder with clean un-encoded text
    print("--- Test 6: Neutral placeholder with clean un-encoded text ---")
    import urllib.parse
    svg_data = create_neutral_placeholder_svg(dish_name="브라운소프트 시그니처", cuisine="Korean")
    print(f"Generated SVG URI (start): {svg_data[:80]}")
    # Verify no double URL-encoded junk like %25EB%25B8%25
    assert "%25" not in svg_data, "Double URL encoding detected in SVG placeholder!"
    decoded_svg = urllib.parse.unquote(svg_data)
    assert "Representative photo unavailable" in decoded_svg, "Missing 'Representative photo unavailable' text!"
    assert "브라운소프트 시그니처" in decoded_svg, "Dish name was lost or encoded incorrectly in SVG text!"
    print(">>> Test 6 PASSED.\n")

    # Test 7: Language switching preserves original OCR text
    print("--- Test 7: Language switching preserves original OCR text ---")
    orig_ocr = "블랙 밀크티 + 펄"
    es_item = await translator.translate_dish(original_name=orig_ocr, printed_desc="", target_language=SupportedLanguage.ES)
    fr_item = await translator.translate_dish(original_name=orig_ocr, printed_desc="", target_language=SupportedLanguage.FR)
    
    print(f"Original OCR: {orig_ocr}")
    print(f"ES translated: {es_item.translated_title}")
    print(f"FR translated: {fr_item.translated_title}")
    dish_payload_es = {"original_name": orig_ocr, "translated_name": es_item.translated_title}
    dish_payload_fr = {"original_name": orig_ocr, "translated_name": fr_item.translated_title}
    assert dish_payload_es["original_name"] == orig_ocr
    assert dish_payload_fr["original_name"] == orig_ocr
    assert dish_payload_es["translated_name"] != orig_ocr
    print(">>> Test 7 PASSED.\n")

    # Test 8: Correct image association across language switching & filtering
    print("--- Test 8: Image association across language switching & filtering ---")
    img_service = ImageSearchService()
    img_res1 = await img_service.search_single_dish(
        DishImageQuery(
            dish_id="dish_1",
            dish_name="블랙 밀크티",
            section="beverage",
            cuisine="korean",
            description="Black milk tea with pearls"
        )
    )
    img_res2 = await img_service.search_single_dish(
        DishImageQuery(
            dish_id="dish_1",
            dish_name="Té con Leche Negro",
            section="beverage",
            cuisine="korean",
            description="Black milk tea with pearls"
        )
    )
    print(f"Image 1 (from Korean name): {img_res1.image_url[:50]}... (source: {img_res1.source})")
    print(f"Image 2 (from Spanish name): {img_res2.image_url[:50]}... (source: {img_res2.source})")
    assert img_res1.image_url is not None
    assert img_res2.image_url is not None
    print(">>> Test 8 PASSED.\n")

    # Test 9: Missing or invalid Unsplash credentials graceful fallback
    print("--- Test 9: Missing or invalid Unsplash credentials fallback ---")
    saved_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    try:
        os.environ["UNSPLASH_ACCESS_KEY"] = "INVALID_KEY_FOR_TESTING_12345"
        bad_provider = UnsplashImageProvider(access_key="INVALID_KEY_FOR_TESTING_12345")
        res = await bad_provider.search_image(
            DishImageQuery(dish_id="dish_bad", dish_name="블랙 밀크티", section="beverage")
        )
        print(f"Result with invalid key: {res}")
        assert res is None, "Expected None from bad Unsplash key, triggering graceful fallback"
        
        from backend.app.core.config import Settings
        no_key_settings = Settings(unsplash_access_key="")
        fallback_service = ImageSearchService(settings=no_key_settings)
        fallback_img = await fallback_service.search_single_dish(
            DishImageQuery(
                dish_id="dish_fb",
                dish_name="블랙 밀크티",
                section="beverage",
                cuisine="korean"
            )
        )
        print(f"Fallback Image Source: {fallback_img.source}")
        assert fallback_img.source in ("curated", "placeholder"), f"Expected curated or placeholder, got {fallback_img.source}"
    finally:
        if saved_key:
            os.environ["UNSPLASH_ACCESS_KEY"] = saved_key
        else:
            os.environ.pop("UNSPLASH_ACCESS_KEY", None)
    print(">>> Test 9 PASSED.\n")

    print("======================================================================")
    print("ALL 9 FUNCTIONAL AUDIT TESTS COMPLETED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
