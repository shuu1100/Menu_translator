"""Health check schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Component status values."""

    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class OverallHealthStatus(str, Enum):
    """Overall system health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health details for an individual component."""

    status: ServiceStatus
    message: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Unified response payload for /health and /api/v1/health."""

    status: OverallHealthStatus
    version: str
    environment: str
    timestamp: datetime
    services: Dict[str, ComponentHealth]
