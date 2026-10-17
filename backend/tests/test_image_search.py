"""Unit and integration tests for automatic food image discovery and matching."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.image_search import BatchImageSearchRequest, DishImageQuery
from backend.app.services.images.providers.curated import CuratedImageProvider, create_neutral_placeholder_svg
from backend.app.services.images.providers.pexels import PexelsImageProvider
from backend.app.services.images.providers.unsplash import UnsplashImageProvider
from backend.app.services.images.query_builder import (
    build_image_search_query,
    calculate_match_relevance,
    clean_dish_name,
    infer_cuisine,
    infer_dish_category,
)
from backend.app.services.images.service import ImageSearchService


client = TestClient(app)


def test_clean_dish_name():
    """Verify noisy adjectives, prices, and parentheticals are cleaned."""
    assert clean_dish_name("NEW Chef's Special Tonkotsu Ramen (6 pcs) - $14.50") == "tonkotsu ramen"
    assert clean_dish_name("Signature Mango Smoothie [Large]") == "mango smoothie"
    assert clean_dish_name("Popular Kimchi Fried Rice *Hot*") == "kimchi fried rice"


def test_infer_cuisine_and_category():
    """Verify cuisine and category inference across diverse global dishes."""
    # Japanese
    assert infer_cuisine("Tonkotsu Ramen", native_name="豚骨ラーメン") == "Japanese"
    assert infer_dish_category("Tonkotsu Ramen") == "soup" or infer_dish_category("Tonkotsu Ramen") == "noodles"

    # Korean
    assert infer_cuisine("Kimchi Fried Rice", native_name="김치볶음밥") == "Korean"
    assert infer_dish_category("Kimchi Fried Rice") == "rice"

    # Beverage vs Soup categorization
    assert infer_dish_category("Mango Smoothie") == "beverage"
    assert infer_dish_category("Tom Yum Goong") == "soup"
    assert infer_dish_category("Chocolate Souffle") == "dessert"
    assert infer_dish_category("Spaghetti alla Carbonara") == "noodles"


def test_build_image_search_query():
    """Verify query generator constructs high-precision search strings."""
    pri, fb, cat = build_image_search_query(
        dish_name="Tonkotsu Ramen",
        native_name="特製豚骨ラーメン",
        cuisine="Japanese",
    )
    assert "tonkotsu ramen" in pri.lower()
    assert cat in ("noodles", "soup")

    pri_drink, _, cat_drink = build_image_search_query(
        dish_name="Mango Yogurt Smoothie",
        section="Beverages",
    )
    assert "mango yogurt smoothie" in pri_drink.lower()
    assert cat_drink == "beverage"


def test_calculate_match_relevance_penalty():
    """Verify category mismatch penalty prevents matching soup to drinks."""
    good_score = calculate_match_relevance(
        query_dish_name="Tonkotsu Ramen",
        query_category="noodles",
        candidate_title="Delicious bowl of Japanese tonkotsu ramen noodles",
        candidate_tags=["ramen", "soup", "noodles"],
    )
    assert good_score >= 0.70

    bad_score = calculate_match_relevance(
        query_dish_name="Mango Smoothie",
        query_category="beverage",
        candidate_title="Hot bowl of beef noodle soup with meat",
        candidate_tags=["soup", "meat", "beef"],
    )
    # Severe penalty for category mismatch
    assert bad_score <= 0.40


@pytest.mark.asyncio
async def test_curated_image_provider_known_dishes():
    """Verify curated provider returns verified high-resolution food photos for known dishes."""
    provider = CuratedImageProvider()
    assert provider.is_configured() is True

    # Japanese Ramen
    query_ramen = DishImageQuery(dish_id="d1", dish_name="Tonkotsu Ramen", cuisine="Japanese")
    ramen_res = await provider.search_image(query_ramen)
    assert ramen_res is not None
    assert ramen_res.status == "available"
    assert not ramen_res.is_fallback
    assert "unsplash.com" in ramen_res.image_url
    assert ramen_res.photographer is not None
    assert ramen_res.relevance_score >= 0.70

    # Korean Bubble Tea
    query_tea = DishImageQuery(dish_id="d2", dish_name="Black Milk Tea with Pearls", native_name="블랙 밀크티")
    tea_res = await provider.search_image(query_tea)
    assert tea_res is not None
    assert tea_res.status == "available"
    assert not tea_res.is_fallback

    # Italian Carbonara
    query_pasta = DishImageQuery(dish_id="d3", dish_name="Spaghetti alla Carbonara", cuisine="Italian")
    pasta_res = await provider.search_image(query_pasta)
    assert pasta_res is not None
    assert pasta_res.status == "available"


@pytest.mark.asyncio
async def test_curated_image_provider_unknown_dish_fallback():
    """Verify an unknown or obscure dish returns a neutral cuisine placeholder SVG with unavailable status."""
    provider = CuratedImageProvider()
    query_unknown = DishImageQuery(dish_id="d99", dish_name="Obscure Rare Specialty Xylophone Delicacy")
    res = await provider.search_image(query_unknown)

    assert res is not None
    assert res.is_fallback is True
    assert res.status == "unavailable"
    assert res.image_url.startswith("data:image/svg+xml")
    assert "Representative image unavailable" in res.alt_text


def test_neutral_placeholder_svg_generation():
    """Verify neutral placeholder SVG generates valid URI."""
    uri = create_neutral_placeholder_svg("Grandma's Secret Broth", "Italian")
    assert uri.startswith("data:image/svg+xml;utf8,")
    assert "Grandma" in uri or "Grandma%27s" in uri


def test_unconfigured_external_providers():
    """Verify external providers without API keys report unconfigured and return None."""
    unsplash = UnsplashImageProvider(access_key=None)
    assert unsplash.is_configured() is False

    pexels = PexelsImageProvider(api_key="")
    assert pexels.is_configured() is False


@pytest.mark.asyncio
async def test_image_search_service_caching():
    """Verify identical dish queries hit memory cache without redundant processing."""
    service = ImageSearchService()
    query = DishImageQuery(dish_id="dish_cache_1", dish_name="Tonkotsu Ramen", cuisine="Japanese")

    res1 = await service.search_single_dish(query)
    assert res1 is not None

    cache_key = service._make_cache_key(query)
    assert service.get_cached(cache_key) is not None

    # Second fetch returns exact same cached instance
    res2 = await service.search_single_dish(query)
    assert res2.image_url == res1.image_url


def test_api_get_single_dish_image():
    """Integration test: GET /api/v1/images/search returns valid DishImageInfo."""
    resp = client.get("/api/v1/images/search", params={"dish_name": "Kimchi Fried Rice", "cuisine": "Korean"})
    assert resp.status_code == 200
    data = resp.json()

    assert "image_url" in data
    assert "source" in data
    assert "alt_text" in data
    assert "relevance_score" in data
    assert data["status"] in ("available", "unavailable")


def test_api_post_batch_search():
    """Integration test: POST /api/v1/images/batch-search returns batch results for multiple dishes."""
    payload = {
        "dishes": [
            {"dish_id": "item_1", "dish_name": "Tonkotsu Ramen", "cuisine": "Japanese"},
            {"dish_id": "item_2", "dish_name": "Mango Yogurt Smoothie", "section": "Beverages"},
            {"dish_id": "item_3", "dish_name": "Margherita Pizza", "cuisine": "Italian"},
            {"dish_id": "item_4", "dish_name": "Completely Fictional Dish 12345"},
        ],
        "cuisine": "Global",
    }
    resp = client.post("/api/v1/images/batch-search", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_requested"] == 4
    assert len(data["results"]) == 4

    # Known items should have available images
    assert data["results"]["item_1"]["status"] == "available"
    assert data["results"]["item_2"]["status"] == "available"
    assert data["results"]["item_3"]["status"] == "available"

    # Unknown item should gracefully fall back
    assert data["results"]["item_4"]["is_fallback"] is True
    assert data["results"]["item_4"]["status"] == "unavailable"


def test_unsplash_candidate_scoring_prefers_food_over_unrelated_objects():
    """Verify Unsplash candidate evaluation rejects laptops/people and picks actual food."""
    provider = UnsplashImageProvider(access_key="mock_key_123456789")

    laptop_photo = {
        "id": "p1",
        "description": "Student working on laptop in modern coffee shop",
        "alt_description": "person typing on computer keyboard at desk",
        "tags": [{"title": "laptop"}, {"title": "computer"}, {"title": "person"}],
    }
    food_photo = {
        "id": "p2",
        "description": "Traditional steaming bowl of Tonkotsu Ramen noodles with egg",
        "alt_description": "delicious Japanese ramen noodles in rich pork broth",
        "tags": [{"title": "ramen"}, {"title": "noodles"}, {"title": "food"}, {"title": "soup"}],
    }

    score_laptop = provider._score_candidate(
        photo=laptop_photo,
        dish_name="Tonkotsu Ramen",
        native_name="豚骨ラーメン",
        category="soup",
    )
    score_food = provider._score_candidate(
        photo=food_photo,
        dish_name="Tonkotsu Ramen",
        native_name="豚骨ラーメン",
        category="soup",
    )

    assert score_food >= 0.70
    assert score_laptop < 0.40
    assert score_food > score_laptop


@pytest.mark.asyncio
async def test_unsplash_live_search_if_key_configured():
    """Live integration test: query Unsplash API when access key is configured."""
    from backend.app.core.config import get_settings
    settings = get_settings()

    if not settings.unsplash_access_key:
        pytest.skip("UNSPLASH_ACCESS_KEY not configured in environment")

    provider = UnsplashImageProvider(access_key=settings.unsplash_access_key)
    assert provider.is_configured() is True

    # Test Korean dish: Kimchi Fried Rice
    query = DishImageQuery(
        dish_id="k_dish_1",
        dish_name="Kimchi Fried Rice",
        native_name="김치볶음밥",
        cuisine="Korean",
        section="Rice",
    )
    result = await provider.search_image(query, timeout_seconds=6.0)

    assert result is not None
    assert result.source == "unsplash"
    assert result.status == "available"
    assert result.image_url.startswith("https://images.unsplash.com/")
    assert result.photographer is not None
    assert "utm_source=universal_menu_translator" in (result.photographer_url or "")
    assert "utm_source=universal_menu_translator" in (result.source_url or "")
    assert result.relevance_score >= 0.45

