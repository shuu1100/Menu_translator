"""Contract tests for Phase 3 API endpoints and pipeline orchestration."""

import io
import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from backend.app.core.config import Settings, get_settings
from backend.app.main import create_app
from backend.app.services.pipeline_orchestrator import MenuPipelineOrchestrator
from backend.tests.fixtures.menu_generator import create_synthetic_menu


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def sample_image_bytes():
    img_bytes, _ = create_synthetic_menu(width=800, height=1000, condition="clear")
    return img_bytes


# -------------------------------------------------------------
# Configuration Endpoint Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_supported_languages(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/config/languages")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert any(l["code"] == "en" for l in data)
        assert any(l["code"] == "es" for l in data)
        assert any(l["code"] == "ja" for l in data)


# -------------------------------------------------------------
# POST /api/v1/menus/analyze Pipeline Contract Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_menu_success(app, sample_image_bytes, monkeypatch) -> None:
    """Successful end-to-end contract validation with mocked VLM."""
    mock_vlm_content = """
    {
      "source_language": "it",
      "items": [
        {
          "reading_order": 1,
          "section": "Antipasti",
          "original_name": "Bruschetta al Pomodoro",
          "subtitle_or_description": "Toasted sourdough bread, heirloom tomatoes, olive oil",
          "price_display": "€8.50",
          "currency": "€",
          "box_2d": [100, 50, 250, 400]
        }
      ]
    }
    """

    class MockResponse:
        status_code = 200
        def json(self):
            return {"message": {"content": mock_vlm_content}}

    orig_post = httpx.AsyncClient.post
    async def mock_post(self, url, *args, **kwargs):
        if "/api/chat" in str(url):
            return MockResponse()
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("menu.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "target_language": "en",
            "user_dietary_restrictions": "gluten-free, vegan",
            "restaurant_id": "rest_12345",
            "apply_clahe": "false",
        }
        res = await client.post("/api/v1/menus/analyze", files=files, data=data)

        assert res.status_code == 200
        payload = res.json()

        # Verify envelope structure
        assert "menu_metadata" in payload
        assert "dishes" in payload
        assert "processing_metadata" in payload
        assert "safety_disclaimer" in payload

        # Verify metadata
        meta = payload["menu_metadata"]
        assert meta["target_language"] == "en"
        assert meta["restaurant_id"] == "rest_12345"
        assert meta["dish_count"] == 1
        assert meta["image_width"] == 800
        assert meta["image_height"] == 1000

        # Verify dishes & bounding box mapping
        dish = payload["dishes"][0]
        assert dish["original_text"] == "Bruschetta al Pomodoro"
        assert dish["price"] == "€8.50"
        assert dish["currency"] == "€"
        assert dish["evidence_status"] == "unverified"
        assert dish["bounding_box"]["pixel_width"] > 0
        assert 0.0 <= dish["bounding_box"]["xmin"] <= 1.0

        # Verify dietary cross-check caught gluten conflict from bread
        assert any("Gluten" in c for c in dish["dietary_compatibility"]["user_conflicts"])

        # Verify processing metadata stages
        proc = payload["processing_metadata"]
        assert proc["retrieval_status"] in [
            "rag_no_matches_fallback_unverified",
            "rag_hybrid_complete",
            "rag_hybrid_partial",
            "rag_lexical_only",
            "stubbed_not_run_in_phase_3",
        ]
        assert len(proc["stages"]) >= 3


@pytest.mark.asyncio
async def test_analyze_menu_unsupported_language(app, sample_image_bytes) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("menu.jpg", sample_image_bytes, "image/jpeg")}
        data = {"target_language": "unsupported_klingon"}
        res = await client.post("/api/v1/menus/analyze", files=files, data=data)
        assert res.status_code == 422
        assert "UNSUPPORTED_LANGUAGE" in res.text


@pytest.mark.asyncio
async def test_analyze_menu_empty_file(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        res = await client.post("/api/v1/menus/analyze", files=files)
        assert res.status_code == 400
        assert "empty" in res.text.lower()


@pytest.mark.asyncio
async def test_analyze_menu_invalid_image_bytes(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("corrupt.jpg", b"RANDOM_NOT_AN_IMAGE_DATA", "image/jpeg")}
        res = await client.post("/api/v1/menus/analyze", files=files)
        assert res.status_code == 400
        assert "Malformed" in res.text or "invalid" in res.text.lower()


@pytest.mark.asyncio
async def test_analyze_menu_oversized_upload(app, monkeypatch) -> None:
    """Uploads exceeding max_upload_size_mb return 413 Payload Too Large."""
    # Temporarily set max upload to 0.001 MB (1 KB) for fast test execution
    app.dependency_overrides[get_settings] = lambda: Settings(max_upload_size_mb=0)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("big.jpg", b"A" * 5000, "image/jpeg")}
            res = await client.post("/api/v1/menus/analyze", files=files)
            assert res.status_code == 413
            assert "PAYLOAD_TOO_LARGE" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analyze_menu_model_timeout_mapped_to_504(app, sample_image_bytes, monkeypatch) -> None:
    """Inference timeout is mapped to HTTP 504 Gateway Timeout."""
    orig_post = httpx.AsyncClient.post
    async def mock_post(self, url, *args, **kwargs):
        if "/api/chat" in str(url):
            raise httpx.TimeoutException("Model inference timed out after 300s")
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("menu.jpg", sample_image_bytes, "image/jpeg")}
        res = await client.post("/api/v1/menus/analyze", files=files)
        assert res.status_code == 504
        assert "INFERENCE_TIMEOUT" in res.text


@pytest.mark.asyncio
async def test_analyze_menu_model_offline_mapped_to_503(app, sample_image_bytes, monkeypatch) -> None:
    """Connection failure to Ollama is mapped to HTTP 503 Service Unavailable."""
    orig_post = httpx.AsyncClient.post
    async def mock_post(self, url, *args, **kwargs):
        if "/api/chat" in str(url):
            raise httpx.ConnectError("Could not connect to Ollama")
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("menu.jpg", sample_image_bytes, "image/jpeg")}
        res = await client.post("/api/v1/menus/analyze", files=files)
        assert res.status_code == 503
        assert "MODEL_SERVICE_UNAVAILABLE" in res.text


@pytest.mark.asyncio
async def test_analyze_menu_without_optional_restaurant_id(app, sample_image_bytes, monkeypatch) -> None:
    """Missing restaurant_id is supported and defaults cleanly."""
    mock_vlm_content = '{"items": [{"reading_order": 1, "original_name": "Tiramisu", "price_display": "€6"}]}'
    class MockResponse:
        status_code = 200
        def json(self): return {"message": {"content": mock_vlm_content}}

    orig_post = httpx.AsyncClient.post
    async def mock_post(self, url, *args, **kwargs):
        if "/api/chat" in str(url):
            return MockResponse()
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("menu.jpg", sample_image_bytes, "image/jpeg")}
        res = await client.post("/api/v1/menus/analyze", files=files)
        assert res.status_code == 200
        payload = res.json()
        assert payload["menu_metadata"]["restaurant_id"] is None
        assert len(payload["dishes"]) == 1


@pytest.mark.asyncio
async def test_analyze_menu_malformed_vlm_output_handling(app, sample_image_bytes, monkeypatch) -> None:
    """Unrecoverable malformed VLM output raises 502 with error envelope."""
    class MockResponse:
        status_code = 200
        def json(self): return {"message": {"content": "TOTALLY UNPARSEABLE JUNK WITHOUT ANY JSON"}}

    orig_post = httpx.AsyncClient.post
    async def mock_post(self, url, *args, **kwargs):
        if "/api/chat" in str(url):
            return MockResponse()
        return await orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("menu.jpg", sample_image_bytes, "image/jpeg")}
        res = await client.post("/api/v1/menus/analyze", files=files)
        assert res.status_code == 502
        assert "MODEL_INFERENCE_ERROR" in res.text


@pytest.mark.asyncio
async def test_analyze_menu_unexpected_pipeline_exception_mapped_to_500(app, sample_image_bytes, monkeypatch) -> None:
    """Unexpected system crash in pipeline maps to HTTP 500 error envelope."""
    async def crash_pipeline(*args, **kwargs):
        raise RuntimeError("Unexpected pipeline hardware fault")

    monkeypatch.setattr("backend.app.services.pipeline_orchestrator.MenuPipelineOrchestrator.run_pipeline", crash_pipeline)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("menu.jpg", sample_image_bytes, "image/jpeg")}
        res = await client.post("/api/v1/menus/analyze", files=files)
        assert res.status_code == 500
        assert "PIPELINE_ERROR" in res.text

