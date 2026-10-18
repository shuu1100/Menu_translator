"""Tests for health check endpoints and error handling."""

import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.health_service import HealthService


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_root_endpoint(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["health"] == "/health"
        assert data["api_v1_health"] == "/api/v1/health"


@pytest.mark.asyncio
async def test_health_endpoint_schema(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "services" in data
        assert "api" in data["services"]
        assert "database" in data["services"]
        assert "model_service" in data["services"]
        assert data["services"]["api"]["status"] == "ok"


@pytest.mark.asyncio
async def test_api_v1_health_matches_root_health(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp1 = await client.get("/health")
        resp2 = await client.get("/api/v1/health")
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["version"] == resp2.json()["version"]


@pytest.mark.asyncio
async def test_health_reports_degraded_when_ollama_unreachable(monkeypatch) -> None:
    """Explicitly verify health does not falsely claim inference works when model service is offline."""
    settings = Settings(ollama_base_url="http://127.0.0.1:9999")  # Unused port
    service = HealthService(settings=settings)

    model_health = await service.check_model_service()
    assert model_health.status == "unavailable"
    assert model_health.details["inference_ready"] is False
    assert "Cannot connect" in model_health.message or "error" in model_health.message.lower()

    overall = await service.get_overall_health()
    assert overall.status == "degraded"
    assert overall.services["model_service"].details["inference_ready"] is False


@pytest.mark.asyncio
async def test_health_reports_degraded_when_model_missing_in_ollama(monkeypatch) -> None:
    """Verify health flags missing model when Ollama is running but target model is not pulled."""
    class MockResponse:
        status_code = 200
        def json(self):
            return {"models": [{"name": "llama3:latest"}]}

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    settings = Settings(vision_model="qwen3-vl:8b")
    service = HealthService(settings=settings)

    model_health = await service.check_model_service()
    assert model_health.status == "degraded"
    assert model_health.details["inference_ready"] is False
    assert "not installed" in model_health.message or "not pulled" in model_health.message

    overall = await service.get_overall_health()
    assert overall.status == "degraded"


@pytest.mark.asyncio
async def test_health_reports_healthy_when_model_present(monkeypatch) -> None:
    """Verify health succeeds when Ollama returns the target model."""
    class MockResponse:
        status_code = 200
        def json(self):
            return {"models": [{"name": "qwen3-vl:8b"}]}

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    settings = Settings(vision_model="qwen3-vl:8b")
    service = HealthService(settings=settings)

    model_health = await service.check_model_service()
    assert model_health.status == "ok"
    assert model_health.details["inference_ready"] is True
    assert model_health.details["ollama_server_available"] is True
    assert model_health.details["model_installed"] is True

    overall = await service.get_overall_health()
    assert overall.status == "healthy"


@pytest.mark.asyncio
async def test_health_active_inference_probe_success(monkeypatch) -> None:
    """Verify active inference probe when explicitly requested."""
    class MockTagsResponse:
        status_code = 200
        def json(self):
            return {"models": [{"name": "qwen3-vl:8b"}]}

    class MockChatResponse:
        status_code = 200
        def json(self):
            return {"message": {"content": "pong"}}

    async def mock_get(*args, **kwargs):
        return MockTagsResponse()

    async def mock_post(*args, **kwargs):
        return MockChatResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    service = HealthService(settings=Settings(vision_model="qwen3-vl:8b"))
    model_health = await service.check_model_service(check_active_inference=True)

    assert model_health.status == "ok"
    assert model_health.details["active_inference_checked"] is True
    assert model_health.details["active_inference_available"] is True


@pytest.mark.asyncio
async def test_health_active_inference_probe_failure(monkeypatch) -> None:
    """Verify health degrades if active inference probe fails despite model being listed."""
    class MockTagsResponse:
        status_code = 200
        def json(self):
            return {"models": [{"name": "qwen3-vl:8b"}]}

    class MockChatResponse:
        status_code = 500
        def json(self):
            return {"error": "crashed"}

    async def mock_get(*args, **kwargs):
        return MockTagsResponse()

    async def mock_post(*args, **kwargs):
        return MockChatResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    service = HealthService(settings=Settings(vision_model="qwen3-vl:8b"))
    model_health = await service.check_model_service(check_active_inference=True)

    assert model_health.status == "degraded"
    assert model_health.details["active_inference_checked"] is True
    assert model_health.details["active_inference_available"] is False
    assert model_health.details["inference_ready"] is False

