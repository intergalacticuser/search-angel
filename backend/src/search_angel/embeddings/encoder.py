"""Sentence-transformer embedding encoder."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Lazy import to avoid loading torch at module import time
_model: Any = None


def _get_model(model_name: str) -> Any:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model '%s'...", model_name)
        _model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded")
    return _model


class EmbeddingEncoder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384) -> None:
        self.model_name = model_name
        self.dimension = dimension

    def encode(self, text: str) -> list[float]:
        model = _get_model(self.model_name)
        embedding: np.ndarray = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []
        model = _get_model(self.model_name)
        embeddings: np.ndarray = model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True
        )
        return embeddings.tolist()

    async def async_encode(self, text: str) -> list[float]:
        """Async wrapper - runs encoding in thread pool to avoid blocking."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.encode, text)

    async def async_encode_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]:
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.encode_batch, texts, batch_size)
