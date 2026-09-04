"""Embedding service - OpenAI API-based implementation."""

import logging

from src.config import get_settings
from src.services.interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIEmbeddingService(EmbeddingProvider):
    """Generates embeddings via OpenAI's text-embedding API."""

    def __init__(self) -> None:
        self._api_key = settings.openai_api_key
        self._model = settings.embedding_model
        self._dimensions = settings.embedding_dimensions
        self._client = None

    def _get_client(self):
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            if not self._api_key:
                raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file.")
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Handles batching internally - OpenAI accepts up to 2048 texts per call,
        but we batch at 100 to stay safe on token limits.
        """
        client = self._get_client()
        all_embeddings: list[list[float]] = []

        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Clean empty strings (OpenAI rejects them)
            cleaned = [t if t.strip() else "empty" for t in batch]

            response = client.embeddings.create(
                model=self._model,
                input=cleaned,
                dimensions=self._dimensions,
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def dimensions(self) -> int:
        """Return the configured embedding dimensionality."""
        return self._dimensions
