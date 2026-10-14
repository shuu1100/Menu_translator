"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List
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
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
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


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
