"""Embedding service package."""

from backend.app.services.embedding.base import BaseEmbeddingProvider
from backend.app.services.embedding.local_provider import (
    LocalMultilingualEmbeddingProvider,
    get_embedding_provider,
    serialize_float32,
)

__all__ = [
    "BaseEmbeddingProvider",
    "LocalMultilingualEmbeddingProvider",
    "get_embedding_provider",
    "serialize_float32",
]
