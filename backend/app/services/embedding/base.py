"""Base interface for embedding providers."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract base class for generating dense vector embeddings."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector embedding dimensionality."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the embedding model."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a normalized dense vector embedding for single text input."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a batch of texts."""
        pass
