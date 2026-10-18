"""Service for assessing system health and component connectivity."""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import httpx

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.schemas.health import (
    ComponentHealth,
    HealthResponse,
    OverallHealthStatus,
    ServiceStatus,
)

logger = get_logger(__name__)


class HealthService:
    """Evaluates health of backend services without falsely claiming model inference works."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    async def check_api(self) -> ComponentHealth:
        """API service is healthy if we are executing this code."""
        return ComponentHealth(
            status=ServiceStatus.OK,
            message="FastAPI service is running",
            details={
                "environment": self.settings.environment,
                "version": self.settings.app_version,
            },
        )

    async def check_database(self) -> ComponentHealth:
        """Check database file, FTS5 support, sqlite-vec extension, and dishes count."""
        try:
            from backend.app.db.connection import get_db_manager

            mgr = get_db_manager()
            db_status = mgr.get_status()
            dishes_count = 0

            if db_status.get("connected", False):
                try:
                    with mgr.connection() as con:
                        row = con.execute("SELECT COUNT(*) FROM dishes").fetchone()
                        dishes_count = row[0] if row else 0
                except Exception as exc:
                    logger.debug("Could not query dishes count: %s", exc)

                vector_status = db_status.get("vector_status", "unknown")
                msg = f"Database connected ({dishes_count} dishes, vector: {vector_status})"
                return ComponentHealth(
                    status=ServiceStatus.OK,
                    message=msg,
                    details={
                        "path": str(mgr.db_path),
                        "connected": True,
                        "fts5": db_status.get("fts5", False),
                        "vector_search": db_status.get("vector_search", False),
                        "vector_version": db_status.get("vector_version"),
                        "vector_status": vector_status,
                        "dishes_count": dishes_count,
                    },
                )
            else:
                return ComponentHealth(
                    status=ServiceStatus.UNAVAILABLE,
                    message=f"Database connection failed: {db_status.get('error', 'unknown error')}",
                    details=db_status,
                )
        except Exception as e:
            return ComponentHealth(
                status=ServiceStatus.DEGRADED,
                message=f"Database health inspection error: {str(e)}",
                details={"error": str(e)},
            )

    async def check_model_service(self, check_active_inference: bool = False) -> ComponentHealth:
        """
        Check local Ollama VLM connectivity and verify if the configured vision model exists.
        Distinguishes between:
        1. Backend available: True (we are running)
        2. Ollama server reachable: True/False
        3. Configured model installed: True/False
        4. Active inference available: checked only when check_active_inference=True
        """
        base_url = self.settings.ollama_base_url.rstrip("/")
        model_name = self.settings.vision_model
        tags_url = f"{base_url}/api/tags"

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(tags_url)
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

                if response.status_code != 200:
                    return ComponentHealth(
                        status=ServiceStatus.UNAVAILABLE,
                        message=f"Ollama server responded with HTTP {response.status_code}",
                        details={
                            "provider": "ollama",
                            "base_url": base_url,
                            "configured_model": model_name,
                            "backend_available": True,
                            "ollama_server_available": False,
                            "model_installed": False,
                            "active_inference_checked": check_active_inference,
                            "active_inference_available": False,
                            "latency_ms": latency_ms,
                            "inference_ready": False,
                        },
                    )

                data = response.json()
                raw_models: List[Dict[str, Any]] = data.get("models", [])
                available_model_names = [m.get("name", "") for m in raw_models]

                # Check if configured model or model:latest matches
                model_found = any(
                    m == model_name or m.startswith(f"{model_name}:") or model_name.startswith(f"{m}:")
                    for m in available_model_names
                )

                if not model_found:
                    return ComponentHealth(
                        status=ServiceStatus.DEGRADED,
                        message=f"Ollama server is reachable, but configured model '{model_name}' is not installed.",
                        details={
                            "provider": "ollama",
                            "base_url": base_url,
                            "configured_model": model_name,
                            "available_models": available_model_names,
                            "backend_available": True,
                            "ollama_server_available": True,
                            "model_installed": False,
                            "active_inference_checked": check_active_inference,
                            "active_inference_available": False,
                            "latency_ms": latency_ms,
                            "inference_ready": False,
                            "resolution": f"Run: ollama pull {model_name}",
                        },
                    )

                # Model is installed. Now check if active inference probe was explicitly requested.
                active_inference_ok = None
                if check_active_inference:
                    # Lightweight text probe to confirm inference engine is loaded and responsive
                    probe_url = f"{base_url}/api/chat"
                    probe_payload = {
                        "model": model_name,
                        "messages": [{"role": "user", "content": "ping"}],
                        "stream": False,
                        "options": {
                            "num_predict": 5,
                        },
                    }
                    try:
                        probe_res = await client.post(probe_url, json=probe_payload, timeout=45.0)
                        active_inference_ok = (probe_res.status_code == 200)
                    except Exception as probe_err:
                        logger.warning(f"Active inference probe failed: {probe_err}")
                        active_inference_ok = False

                    if not active_inference_ok:
                        return ComponentHealth(
                            status=ServiceStatus.DEGRADED,
                            message=f"Model '{model_name}' is installed, but active inference probe failed or timed out.",
                            details={
                                "provider": "ollama",
                                "base_url": base_url,
                                "configured_model": model_name,
                                "available_models": available_model_names,
                                "backend_available": True,
                                "ollama_server_available": True,
                                "model_installed": True,
                                "active_inference_checked": True,
                                "active_inference_available": False,
                                "latency_ms": latency_ms,
                                "inference_ready": False,
                            },
                        )

                return ComponentHealth(
                    status=ServiceStatus.OK,
                    message=f"Model '{model_name}' is installed and available in Ollama.",
                    details={
                        "provider": "ollama",
                        "base_url": base_url,
                        "configured_model": model_name,
                        "available_models": available_model_names,
                        "backend_available": True,
                        "ollama_server_available": True,
                        "model_installed": True,
                        "active_inference_checked": check_active_inference,
                        "active_inference_available": active_inference_ok,
                        "latency_ms": latency_ms,
                        "inference_ready": True,
                    },
                )

        except httpx.ConnectError:
            return ComponentHealth(
                status=ServiceStatus.UNAVAILABLE,
                message=f"Cannot connect to Ollama at {base_url}. Ensure Ollama is running.",
                details={
                    "provider": "ollama",
                    "base_url": base_url,
                    "configured_model": model_name,
                    "backend_available": True,
                    "ollama_server_available": False,
                    "model_installed": False,
                    "active_inference_checked": check_active_inference,
                    "active_inference_available": False,
                    "inference_ready": False,
                    "resolution": "Start the Ollama daemon via 'ollama serve'",
                },
            )
        except httpx.TimeoutException:
            return ComponentHealth(
                status=ServiceStatus.UNAVAILABLE,
                message=f"Timed out connecting to Ollama at {base_url}",
                details={
                    "provider": "ollama",
                    "base_url": base_url,
                    "configured_model": model_name,
                    "backend_available": True,
                    "ollama_server_available": False,
                    "model_installed": False,
                    "active_inference_checked": check_active_inference,
                    "active_inference_available": False,
                    "inference_ready": False,
                },
            )
        except Exception as e:
            return ComponentHealth(
                status=ServiceStatus.UNAVAILABLE,
                message=f"Error inspecting model service: {str(e)}",
                details={
                    "provider": "ollama",
                    "base_url": base_url,
                    "configured_model": model_name,
                    "backend_available": True,
                    "ollama_server_available": False,
                    "model_installed": False,
                    "active_inference_checked": check_active_inference,
                    "active_inference_available": False,
                    "inference_ready": False,
                },
            )

    async def get_overall_health(self, check_active_inference: bool = False) -> HealthResponse:
        """Aggregate health check results."""
        api_health = await self.check_api()
        db_health = await self.check_database()
        model_health = await self.check_model_service(check_active_inference=check_active_inference)

        services = {
            "api": api_health,
            "database": db_health,
            "model_service": model_health,
        }

        # Determine overall status
        if any(s.status == ServiceStatus.UNAVAILABLE for s in services.values()):
            overall = OverallHealthStatus.DEGRADED
        elif any(s.status == ServiceStatus.DEGRADED for s in services.values()):
            overall = OverallHealthStatus.DEGRADED
        else:
            overall = OverallHealthStatus.HEALTHY

        return HealthResponse(
            status=overall,
            version=self.settings.app_version,
            environment=self.settings.environment,
            timestamp=datetime.now(timezone.utc),
            services=services,
        )
