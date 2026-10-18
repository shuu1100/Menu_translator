"""Automated test suite verifying multilingual accuracy, zero hallucination, and sanitization."""

import pytest
from backend.app.schemas.menu_analysis import SupportedLanguage
from backend.app.services.translation.multilingual_engine import (
    MultilingualCulinaryEngine,
    romanize_hangul,
    romanize_japanese,
)
from backend.app.services.translation.translator import (
    DeterministicCulinaryTranslator,
    DishTranslationResult,
)
from backend.app.services.vision.json_parser import (
    ModelJsonParser,
    is_section_header,
    sanitize_dish_item,
)
from backend.app.services.pipeline_orchestrator import is_valid_rag_match


def test_section_headers_classification():
    """Verify promotional and category headers are identified and never treated as dishes."""
    headers = [
        "NEW (SALTY& SWEET)",
        "SEASON MENU",
        "BEST SELLER",
        "SIGNATURE",
        "MILK TEA",
        "ORIGINAL TEA",
        "ANTIPASTI",
        "PRIMI",
        "SECONDI",
        "ENTRÉES",
        "BOISSONS",
        "VORSPEISEN",
        "신메뉴",
        "음료",
    ]
    for h in headers:
        assert is_section_header(h), f"Expected '{h}' to be identified as section header"

    valid_dishes = [
        "블랙 밀크티",
        "Pizza Margherita",
        "Carpaccio di Manzo",
        "Coq au Vin",
    ]
    for d in valid_dishes:
        assert not is_section_header(d), f"Expected '{d}' NOT to be identified as section header"


def test_dish_sanitizer_removes_model_monologue_and_prefixes():
    """Verify reasoning sentences, schema labels, and fused fields are sanitized."""
    # Case 1: Monologue leaking in name
    raw = "Tea 스 브라운 - description: 시그니처 Milk Tea + 케러멜 (but wait the image might have different descriptions). Wait looking at the menu image"
    name, desc, price, is_header = sanitize_dish_item(raw)
    assert name == "Tea 스 브라운"
    assert "시그니처 Milk Tea + 케러멜" in desc
    assert not is_header
    assert "wait" not in name.lower()
    assert "looking at the menu" not in name.lower()

    # Case 2: Schema prefixes
    raw_prefix = "Name: 블랙 밀크티"
    name, desc, price, is_header = sanitize_dish_item(raw_prefix)
    assert name == "블랙 밀크티"
    assert not is_header

    # Case 3: Category header becomes header
    raw_header = "NEW (SALTY& SWEET)"
    name, desc, price, is_header = sanitize_dish_item(raw_header)
    assert is_header is True


def test_multilingual_script_detection():
    """Verify script detection works across diverse languages."""
    assert MultilingualCulinaryEngine.detect_script("블랙 밀크티") == "ko"
    assert MultilingualCulinaryEngine.detect_script("抹茶ラテ") == "ja"
    assert MultilingualCulinaryEngine.detect_script("香芋奶茶") == "zh"
    assert MultilingualCulinaryEngine.detect_script("شاي بالحليب") == "ar"
    assert MultilingualCulinaryEngine.detect_script("Борщ") == "ru"
    assert MultilingualCulinaryEngine.detect_script("Pizza Margherita") == "latin"


def test_zero_hallucination_when_no_printed_description():
    """Verify that when no printed description exists, no fake description or flavor note is invented."""
    engine = MultilingualCulinaryEngine()
    title, phonetic, desc, flavor = engine.translate_dish(
        original_name="블랙 밀크티",
        printed_desc=None,
        target_lang=SupportedLanguage.EN,
    )
    assert title == "Black Milk Tea"
    assert desc is None, "Expected desc to be None when no printed desc was on menu"
    assert flavor is None, "Expected flavor to be None when no printed flavor was on menu"


@pytest.mark.asyncio
async def test_deterministic_translator_all_supported_languages():
    """Verify translation of menu items across all 10 supported target languages."""
    translator = DeterministicCulinaryTranslator()
    supported = [
        SupportedLanguage.EN,
        SupportedLanguage.ES,
        SupportedLanguage.FR,
        SupportedLanguage.DE,
        SupportedLanguage.JA,
        SupportedLanguage.ZH,
        SupportedLanguage.AR,
        SupportedLanguage.IT,
        SupportedLanguage.PT,
        SupportedLanguage.KO,
    ]

    for lang in supported:
        res = await translator.translate_dish(
            original_name="블랙 밀크티",
            printed_desc="달콤하고 진한 홍차 밀크티",
            target_language=lang,
        )
        assert res.translated_title, f"Translation failed for language {lang.value}"
        assert res.translated_title != ""


def test_rag_isolation_prevents_cross_cuisine_hijack():
    """Verify that a Gong Cha tea cannot match a Pizza Margherita RAG record."""
    class FakeDishRecord:
        native_name = "Pizza Margherita"
        aliases = ["Margherita Pizza", "Pizza"]

    fake_rag = FakeDishRecord()
    # Query is Gong Cha tea
    assert not is_valid_rag_match("Tea 스 브라운", fake_rag)
    assert not is_valid_rag_match("블랙 밀크티", fake_rag)
    # Query is pizza
    assert is_valid_rag_match("Pizza Margherita", fake_rag)
    assert is_valid_rag_match("Margherita Pizza", fake_rag)
