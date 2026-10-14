"""
Live integration test for Ollama with Qwen3-VL 8B.
Runs ONLY when Ollama is locally reachable and qwen3-vl:8b is installed;
otherwise skips gracefully with an informative message.
"""

import os
import httpx
import pytest
from backend.app.core.config import Settings
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.tests.fixtures.menu_generator import create_synthetic_menu


def is_ollama_qwen_available() -> bool:
    """Synchronous probe to check if Ollama daemon is reachable and model is installed."""
    settings = Settings()
    base_url = settings.ollama_base_url.rstrip("/")
    try:
        with httpx.Client(timeout=2.0) as client:
            res = client.get(f"{base_url}/api/tags")
            if res.status_code == 200:
                models = [m.get("name", "") for m in res.json().get("models", [])]
                return any(
                    m == settings.vision_model or m.startswith(f"{settings.vision_model}:")
                    for m in models
                )
    except Exception:
        return False
    return False


@pytest.mark.asyncio
async def test_live_ollama_menu_extraction():
    """Manual integration test verifying live inference with local Qwen3-VL 8B."""
    if not os.getenv("RUN_LIVE_OLLAMA_TEST"):
        pytest.skip(
            "SKIPPED: Manual live integration test disabled by default to keep CI/pytest fast. "
            "To execute live inference, set RUN_LIVE_OLLAMA_TEST=1."
        )

    if not is_ollama_qwen_available():
        pytest.skip(
            "SKIPPED: Local Ollama is unreachable or configured 'qwen3-vl:8b' model is not installed. "
            "To enable live integration testing, run 'ollama serve' and 'ollama pull qwen3-vl:8b'."
        )

    settings = Settings()
    provider = OllamaVisionProvider(settings=settings)

    # Use a compact synthetic menu for faster integration validation
    img_bytes, gt_meta = create_synthetic_menu(width=600, height=800, condition="clear")

    result = await provider.extract_menu(
        image_bytes=img_bytes,
        mime_type="image/jpeg",
        apply_clahe=False,
    )

    assert result.original_width == 600
    assert result.original_height == 800
    assert result.model_name == settings.vision_model
    assert result.processing_time_ms > 0
    assert "Inferred allergen or safety claims are strictly prohibited" in result.safety_notice

    # Verify structured items returned have valid normalized coordinates
    for item in result.items:
        assert 0.0 <= item.bounding_box.xmin <= 1.0
        assert 0.0 <= item.bounding_box.ymin <= 1.0
        assert 0.0 <= item.bounding_box.xmax <= 1.0
        assert 0.0 <= item.bounding_box.ymax <= 1.0
        assert item.reading_order >= 1
