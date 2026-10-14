"""Tests for configuration settings."""

from backend.app.core.config import Settings


def test_settings_default_values() -> None:
    settings = Settings()
    assert settings.app_name == "Menu Translator API"
    assert settings.port == 8000
    assert settings.vision_model == "qwen3-vl:8b"
    assert settings.ollama_base_url in ["http://localhost:11434", "http://127.0.0.1:11434"]
    assert settings.max_upload_size_mb == 15
    assert "image/jpeg" in settings.allowed_extensions
