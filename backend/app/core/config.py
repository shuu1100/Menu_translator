"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    app_name: str = "Menu Translator API"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", description="Environment mode")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")

    # Server & Networking
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        description="Allowed CORS origins",
    )

    # Local VLM Inference (Ollama)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama local API base URL",
    )
    vision_model: str = Field(
        default="qwen3-vl:8b",
        description="Vision Language Model identifier to use in Ollama",
    )
    inference_timeout_seconds: int = Field(
        default=300,
        description="Timeout for model inference requests in seconds",
    )
    translation_model: Optional[str] = Field(
        default=None,
        description="Model to use for translation/enrichment (defaults to vision_model if None)",
    )
    translation_temperature: float = Field(
        default=0.1,
        description="Sampling temperature for contextual translation (0.0 to 0.2)",
    )
    translation_timeout_seconds: int = Field(
        default=30,
        description="Timeout for translation generation in seconds",
    )

    # Database & Storage
    database_path: str = Field(
        default="data/culinary_knowledge.db",
        description="Path to SQLite culinary knowledge database",
    )
    sqlite_vec_enabled: bool = Field(
        default=True,
        description="Enable sqlite-vec dense vector search if available",
    )
    embedding_dimension: int = Field(
        default=384,
        description="Vector embedding dimension (384 for standard multilingual MiniLM)",
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Multilingual embedding model identifier",
    )
    rrf_k: int = Field(
        default=60,
        description="Reciprocal Rank Fusion smoothing parameter k",
    )
    retrieval_confidence_threshold: float = Field(
        default=0.012,
        description="Minimum RRF score required to consider a match authoritative",
    )

    # File uploads
    max_upload_size_mb: int = Field(
        default=15,
        description="Maximum allowed image upload size in megabytes",
    )
    allowed_extensions: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        description="Allowed MIME types for uploaded menu photos",
    )
    image_max_dimension: int = Field(
        default=1024,
        description="Max width/height dimension to resize images before processing",
    )
    max_concurrent_requests: int = Field(
        default=4,
        description="Maximum concurrent pipeline inference requests",
    )
    pipeline_timeout_seconds: int = Field(
        default=120,
        description="Maximum overall timeout for end-to-end menu analysis pipeline in seconds",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
