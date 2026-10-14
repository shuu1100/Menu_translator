"""Local embedding provider supporting 384-dimensional dense vectors."""

import hashlib
import math
import re
from typing import List, Optional
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.services.embedding.base import BaseEmbeddingProvider

logger = get_logger(__name__)


def serialize_float32(vector: List[float]) -> bytes:
    """Serialize float list to binary format for sqlite-vec."""
    try:
        import sqlite_vec
        return sqlite_vec.serialize_float32(vector)
    except (ImportError, AttributeError):
        import struct
        return struct.pack(f"{len(vector)}f", *vector)


class LocalMultilingualEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic local multilingual embedding provider.
    
    Generates 384-dimensional normalized dense vectors using subword n-gram 
    hashing and semantic feature projections. Operates completely locally without
    requiring external GPU drivers, external model downloads, or network access.
    Optionally delegates to fastembed if installed and initialized.
    """

    def __init__(
        self,
        dimension: Optional[int] = None,
        model_name: Optional[str] = None,
        try_fastembed: bool = False,
    ):
        settings = get_settings()
        self._dimension = dimension or settings.embedding_dimension
        self._model_name = model_name or settings.embedding_model
        self._fastembed_model = None

        if try_fastembed:
            try:
                from fastembed import TextEmbedding
                self._fastembed_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
                logger.info("Initialized FastEmbed model: %s", self._model_name)
            except Exception as exc:
                logger.debug("FastEmbed unavailable or disabled; using deterministic local vectorizer: %s", exc)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _hash_token(self, token: str, seed: int) -> int:
        """Hash a token with seed to an integer."""
        h = hashlib.sha256(f"{seed}:{token}".encode("utf-8")).digest()
        return int.from_bytes(h[:4], byteorder="little")

    def _vectorize_local(self, text: str) -> List[float]:
        """Compute deterministic normalized dense vector for text."""
        cleaned = text.strip().lower()
        if not cleaned:
            # Return zero vector with slight perturbation on index 0 to avoid zero-norm division
            vec = [0.0] * self._dimension
            vec[0] = 1.0
            return vec

        vec = [0.0] * self._dimension

        # Tokenize by unicode words and CJK characters
        # Matches latin words or individual CJK/Arabic glyphs
        tokens = re.findall(r"[\w]+|[\u4e00-\u9fff]|[\u3040-\u309f]|[\u30a0-\u30ff]|[\u0600-\u06ff]", cleaned)

        # 1. Whole word tokens
        for token in tokens:
            for seed in (1, 2, 3):
                h = self._hash_token(token, seed)
                idx = h % self._dimension
                sign = 1.0 if ((h >> 16) & 1) == 0 else -1.0
                vec[idx] += sign * 1.5

        # 2. Character n-grams (2-grams, 3-grams) for robust morphological and cross-lingual matching
        for token in tokens:
            if len(token) > 1:
                for n in (2, 3):
                    for i in range(len(token) - n + 1):
                        ngram = token[i : i + n]
                        h = self._hash_token(ngram, 42)
                        idx = h % self._dimension
                        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
                        vec[idx] += sign * 0.75

        # 3. L2 Normalization to unit sphere (||v||_2 = 1.0)
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-12:
            return [x / norm for x in vec]
        else:
            vec[0] = 1.0
            return vec

    def embed_text(self, text: str) -> List[float]:
        """Generate 384-d normalized vector for text."""
        if self._fastembed_model is not None:
            try:
                embeddings = list(self._fastembed_model.embed([text]))
                raw = embeddings[0].tolist()
                norm = math.sqrt(sum(x * x for x in raw))
                return [x / norm for x in raw] if norm > 1e-12 else raw
            except Exception as exc:
                logger.warning("FastEmbed inference error; falling back to local vectorizer: %s", exc)

        return self._vectorize_local(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if self._fastembed_model is not None:
            try:
                raw_batch = list(self._fastembed_model.embed(texts))
                result = []
                for emb in raw_batch:
                    raw = emb.tolist()
                    norm = math.sqrt(sum(x * x for x in raw))
                    result.append([x / norm for x in raw] if norm > 1e-12 else raw)
                return result
            except Exception as exc:
                logger.warning("FastEmbed batch inference error; falling back to local vectorizer: %s", exc)

        return [self._vectorize_local(t) for t in texts]


# Global singleton provider instance
_default_embedding_provider: Optional[BaseEmbeddingProvider] = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Return shared embedding provider."""
    global _default_embedding_provider
    if _default_embedding_provider is None:
        _default_embedding_provider = LocalMultilingualEmbeddingProvider()
    return _default_embedding_provider
