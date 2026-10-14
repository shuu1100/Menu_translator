"""Comprehensive test suite for visual menu extraction, image preprocessing, and parsing."""

import io
import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from backend.app.core.exceptions import InvalidImageError, ModelInferenceError
from backend.app.main import create_app
from backend.app.schemas.extraction import BoundingBox, MenuExtractionResult, MenuTextBlock
from backend.app.services.image_processor import ImageProcessor
from backend.app.services.vision.json_parser import ModelJsonParser
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.tests.fixtures.menu_generator import create_synthetic_menu
from backend.tests.fixtures.metrics import calculate_iou, character_error_rate, word_error_rate


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# -------------------------------------------------------------
# Image Processing Tests
# -------------------------------------------------------------

def test_image_processor_valid_decode(sample_jpeg_bytes: bytes) -> None:
    img = ImageProcessor.validate_and_decode(sample_jpeg_bytes)
    assert img.mode == "RGB"
    assert img.size == (800, 1000)


def test_image_processor_rejects_empty_payload() -> None:
    with pytest.raises(InvalidImageError, match="empty"):
        ImageProcessor.validate_and_decode(b"")


def test_image_processor_rejects_corrupted_payload() -> None:
    with pytest.raises(InvalidImageError, match="Malformed"):
        ImageProcessor.validate_and_decode(b"NOT_AN_IMAGE_PAYLOAD_CORRUPT")


def test_image_processor_aspect_ratio_preservation() -> None:
    # 3000 x 1000 image (3:1 aspect ratio)
    img = Image.new("RGB", (3000, 1000), color=(200, 200, 200))
    preprocessed = ImageProcessor.preprocess_for_vlm(img, max_dimension=1500)

    assert preprocessed.original_width == 3000
    assert preprocessed.original_height == 1000
    assert preprocessed.processed_width == 1500
    assert preprocessed.processed_height == 500  # Exact 3:1 aspect ratio preserved!
    assert preprocessed.scale_factor == 0.5


def test_image_processor_clahe_enhancement(sample_jpeg_bytes: bytes) -> None:
    img = ImageProcessor.validate_and_decode(sample_jpeg_bytes)
    preprocessed = ImageProcessor.preprocess_for_vlm(img, apply_clahe=True)
    assert preprocessed.applied_clahe is True
    assert len(preprocessed.image_bytes) > 0


def test_bounding_box_mapping() -> None:
    # 0-1000 scale to normalized 0-1 and pixels
    box = ImageProcessor.map_normalized_box(
        xmin=100, ymin=200, xmax=500, ymax=600, orig_width=1000, orig_height=2000
    )
    assert box.xmin == 0.1
    assert box.ymin == 0.2
    assert box.xmax == 0.5
    assert box.ymax == 0.6
    assert box.pixel_x == 100
    assert box.pixel_y == 400
    assert box.pixel_width == 400
    assert box.pixel_height == 800


# -------------------------------------------------------------
# Defensive JSON Parsing Tests
# -------------------------------------------------------------

def test_json_parser_fenced_markdown() -> None:
    raw_response = """
Here is the extracted menu content:
```json
{
  "source_language": "it",
  "items": [
    {
      "reading_order": 1,
      "section": "Antipasti",
      "original_name": "Bruschetta al Pomodoro",
      "price_display": "€8.50",
      "box_2d": [100, 50, 250, 400]
    }
  ]
}
```
Hope this is helpful!
"""
    lang, items, warnings = ModelJsonParser.parse_and_validate(raw_response, 1000, 1000)
    assert lang == "it"
    assert len(items) == 1
    assert items[0].original_name == "Bruschetta al Pomodoro"
    assert items[0].price_display == "€8.50"
    assert items[0].section == "Antipasti"
    assert items[0].bounding_box.xmin == 0.05
    assert items[0].bounding_box.ymin == 0.10


def test_json_parser_cleans_trailing_commas() -> None:
    raw_with_trailing = """
{
  "source_language": "fr",
  "items": [
    {
      "reading_order": 1,
      "original_name": "Soupe à l'oignon",
      "price_display": "12€",
      "box_2d": [100, 100, 200, 300],
    },
  ],
}
"""
    lang, items, warnings = ModelJsonParser.parse_and_validate(raw_with_trailing, 1000, 1000)
    assert lang == "fr"
    assert len(items) == 1
    assert items[0].original_name == "Soupe à l'oignon"


def test_json_parser_raises_on_unparseable_junk() -> None:
    with pytest.raises(ModelInferenceError):
        ModelJsonParser.parse_and_validate("TOTAL UNSTRUCTURED GARBAGE TEXT WITHOUT JSON", 1000, 1000)


# -------------------------------------------------------------
# Strict Safety Policy Tests
# -------------------------------------------------------------

def test_extraction_stage_prohibits_allergen_claims() -> None:
    result = MenuExtractionResult(
        menu_id="test_menu",
        original_width=1000,
        original_height=1000,
        processing_time_ms=120.0,
        model_name="qwen3-vl:8b",
        items=[],
    )
    # Verify strict safety notice presence
    assert "Inferred allergen or safety claims are strictly prohibited at this stage" in result.safety_notice


# -------------------------------------------------------------
# API Endpoint Integration Tests (Mocked VLM)
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_extract_endpoint_success(monkeypatch) -> None:
    app = create_app()

    # Mock Ollama chat response
    mock_content = """
    {
      "source_language": "it",
      "items": [
        {
          "reading_order": 1,
          "section": "Primi",
          "original_name": "Tagliatelle al Ragù",
          "subtitle_or_description": "Egg pasta with bolognese sauce",
          "price_display": "€16.50",
          "box_2d": [150, 100, 300, 500]
        }
      ]
    }
    """

    class MockResponse:
        status_code = 200
        def json(self):
            return {"message": {"content": mock_content}}

    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, *args, **kwargs):
        if "/api/chat" in str(url):
            return MockResponse()
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    img_bytes, _ = create_synthetic_menu(condition="clear")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("menu.jpg", img_bytes, "image/jpeg")}
        data = {"apply_clahe": "true"}
        response = await client.post("/api/v1/extract", files=files, data=data)

        assert response.status_code == 200, f"Failed with: {response.text}"
        result = response.json()
        assert "source_language" in result, f"Keys in result: {list(result.keys())}, body: {result}"
        assert result["source_language"] == "it"
        assert len(result["items"]) == 1
        assert result["items"][0]["original_name"] == "Tagliatelle al Ragù"
        assert result["items"][0]["price_display"] == "€16.50"
        assert result["items"][0]["bounding_box"]["pixel_width"] > 0
        assert any(w["code"] == "CLAHE_ENHANCEMENT_APPLIED" for w in result["warnings"])


@pytest.mark.asyncio
async def test_extract_endpoint_rejects_non_image() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")}
        response = await client.post("/api/v1/extract", files=files)
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["error"]["message"]


# -------------------------------------------------------------
# Metric Calculation Tests
# -------------------------------------------------------------

def test_iou_and_error_rate_metrics() -> None:
    box1 = {"xmin": 0.1, "ymin": 0.1, "xmax": 0.5, "ymax": 0.5}
    box2 = {"xmin": 0.1, "ymin": 0.1, "xmax": 0.5, "ymax": 0.5}
    assert calculate_iou(box1, box2) == 1.0

    box3 = {"xmin": 0.6, "ymin": 0.6, "xmax": 0.9, "ymax": 0.9}
    assert calculate_iou(box1, box3) == 0.0

    assert character_error_rate("Pizza Margherita", "Pizza Margherita") == 0.0
    assert word_error_rate("Pasta Carbonara", "Pasta Carbonara") == 0.0
    assert character_error_rate("Pizza", "Pizzas") == 0.2


# -------------------------------------------------------------
# Additional Phase 7 Tests
# -------------------------------------------------------------

def test_empty_model_response() -> None:
    """Empty JSON object or empty string produces empty items with an explicit warning."""
    lang, items, warnings = ModelJsonParser.parse_and_validate("{}", 1000, 1000)
    assert len(items) == 0
    assert any(w.code == "EMPTY_EXTRACTION" for w in warnings)


def test_missing_required_fields_safe_handling() -> None:
    """Items missing original_name are skipped with an explicit warning."""
    raw = """
    {
      "items": [
        {"reading_order": 1, "original_name": "", "price_display": "$10"},
        {"reading_order": 2, "original_name": "Gelato al Limone", "price_display": "€4.50"}
      ]
    }
    """
    lang, items, warnings = ModelJsonParser.parse_and_validate(raw, 1000, 1000)
    assert len(items) == 1
    assert items[0].original_name == "Gelato al Limone"
    assert any(w.code == "SKIPPED_EMPTY_NAME" for w in warnings)


def test_out_of_bounds_bounding_box_clamping() -> None:
    """Boxes exceeding 1.0 or with negative bounds are safely clamped to [0.0, 1.0]."""
    raw = """
    {
      "items": [
        {
          "original_name": "Tiramisu",
          "box_2d": [-50, -20, 1200, 1500]
        }
      ]
    }
    """
    lang, items, warnings = ModelJsonParser.parse_and_validate(raw, 1000, 2000)
    assert len(items) == 1
    box = items[0].bounding_box
    assert box.xmin == 0.0
    assert box.ymin == 0.0
    assert box.xmax == 1.0
    assert box.ymax == 1.0
    assert box.pixel_x == 0
    assert box.pixel_y == 0
    assert box.pixel_width == 1000
    assert box.pixel_height == 2000


def test_ambiguous_dish_and_currency_extraction() -> None:
    """Currency is parsed or extracted, and uncertainty notes are preserved without guessing."""
    raw = """
    {
      "source_language": "ja",
      "items": [
        {
          "reading_order": 1,
          "original_name": "ラーメン",
          "price_display": "¥850",
          "currency": "JPY",
          "text_region_type": "dish_item",
          "uncertainty_notes": "First character partially smudged by broth stain"
        }
      ]
    }
    """
    lang, items, warnings = ModelJsonParser.parse_and_validate(raw, 800, 1200)
    assert len(items) == 1
    item = items[0]
    assert item.currency == "JPY"
    assert item.text_region_type == "dish_item"
    assert "smudged" in item.uncertainty_notes


@pytest.mark.asyncio
async def test_ollama_connection_refused_error(monkeypatch) -> None:
    """When Ollama connection fails, raises ModelServiceUnavailableError."""
    async def mock_post(*args, **kwargs):
        raise httpx.ConnectError("Connection refused to 127.0.0.1:11434")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    provider = OllamaVisionProvider()
    img_bytes, _ = create_synthetic_menu()

    with pytest.raises(Exception) as exc_info:
        await provider.extract_menu(img_bytes)

    assert "Could not connect to Ollama" in str(exc_info.value) or "unavailable" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_ollama_timeout_error(monkeypatch) -> None:
    """When Ollama request times out, raises ModelInferenceError with timeout message."""
    async def mock_post(*args, **kwargs):
        raise httpx.TimeoutException("Read timed out")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    provider = OllamaVisionProvider()
    img_bytes, _ = create_synthetic_menu()

    with pytest.raises(Exception) as exc_info:
        await provider.extract_menu(img_bytes)

    assert "timed out" in str(exc_info.value).lower()


def test_backward_compatibility_schema_extension() -> None:
    """Existing MenuTextBlock without new fields currency/text_region_type deserializes with valid defaults."""
    old_data = {
        "id": "item123",
        "reading_order": 1,
        "original_name": "Pasta",
        "bounding_box": {"xmin": 0.1, "ymin": 0.1, "xmax": 0.5, "ymax": 0.5},
    }
    block = MenuTextBlock.model_validate(old_data)
    assert block.original_name == "Pasta"
    assert block.currency is None
    assert block.text_region_type == "dish_item"
