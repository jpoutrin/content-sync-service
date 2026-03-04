"""Multi-provider embedder using LiteLLM and sentence-transformers."""

from typing import Literal

import litellm
from sentence_transformers import SentenceTransformer

from rag.core.interfaces import EmbedderInterface


class LiteLLMEmbedder(EmbedderInterface):
    """
    Multi-provider embedding service supporting local and cloud models.

    Supports two providers:
    - 'local': sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
    - 'openai': OpenAI text-embedding-3-small via LiteLLM (1536 dimensions)

    Args:
        provider: Provider name ('local' or 'openai')
        model: Model identifier (optional, uses defaults if not provided)
        batch_size: Number of texts to embed per API call (default: 32)

    Examples:
        >>> embedder = LiteLLMEmbedder(provider='local')
        >>> vector = embedder.embed("Hello world")
        >>> len(vector)
        384

        >>> embedder = LiteLLMEmbedder(provider='openai')
        >>> vectors = embedder.embed_batch(["text1", "text2"])
        >>> len(vectors[0])
        1536
    """

    # Default models for each provider
    DEFAULT_MODELS = {
        'local': 'sentence-transformers/all-MiniLM-L6-v2',
        'openai': 'text-embedding-3-small'
    }

    # Dimensions for each model
    MODEL_DIMENSIONS = {
        'sentence-transformers/all-MiniLM-L6-v2': 384,
        'text-embedding-3-small': 1536
    }

    def __init__(
        self,
        provider: Literal['local', 'openai'] = 'local',
        model: str | None = None,
        batch_size: int = 32
    ):
        """
        Initialize the embedder.

        Args:
            provider: Provider name ('local' or 'openai')
            model: Model identifier (uses default if not provided)
            batch_size: Number of texts to embed per API call

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in self.DEFAULT_MODELS:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Choose from: {list(self.DEFAULT_MODELS.keys())}"
            )

        self.provider = provider
        self._model = model or self.DEFAULT_MODELS[provider]
        self._batch_size = batch_size

        # Initialize local model if using sentence-transformers
        self._local_model: SentenceTransformer | None = None
        if self.provider == 'local':
            self._local_model = SentenceTransformer(self._model)

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return self._model

    @property
    def dimensions(self) -> int:
        """
        Return the embedding dimensions.

        Returns:
            Number of dimensions in the embedding vector
        """
        return self.MODEL_DIMENSIONS.get(self._model, 384)

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            ValueError: If text is empty
            RuntimeError: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if self.provider == 'local':
            return self._embed_local(text)
        else:
            return self._embed_litellm(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors in the same order as input

        Raises:
            ValueError: If texts is empty or contains empty strings
            RuntimeError: If API call fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        if any(not t or not t.strip() for t in texts):
            raise ValueError("Texts list cannot contain empty strings")

        if self.provider == 'local':
            return self._embed_batch_local(texts)
        else:
            return self._embed_batch_litellm(texts)

    def _embed_local(self, text: str) -> list[float]:
        """
        Generate embedding using local sentence-transformers model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self._local_model is None:
            raise RuntimeError("Local model not initialized")

        embedding = self._local_model.encode(text, convert_to_numpy=True)
        result: list[float] = embedding.tolist()
        return result

    def _embed_batch_local(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using local sentence-transformers model.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self._local_model is None:
            raise RuntimeError("Local model not initialized")

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]
            embeddings = self._local_model.encode(batch, convert_to_numpy=True)
            all_embeddings.extend(embeddings.tolist())

        return all_embeddings

    def _embed_litellm(self, text: str) -> list[float]:
        """
        Generate embedding using LiteLLM provider.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            RuntimeError: If API call fails
        """
        try:
            response = litellm.embedding(
                model=self._model,
                input=[text]
            )
            result: list[float] = response.data[0]['embedding']
            return result
        except Exception as e:
            raise RuntimeError(f"LiteLLM embedding failed: {e}") from e

    def _embed_batch_litellm(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using LiteLLM provider with batching.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            RuntimeError: If API call fails
        """
        all_embeddings = []

        try:
            # Process in batches
            for i in range(0, len(texts), self._batch_size):
                batch = texts[i:i + self._batch_size]
                response = litellm.embedding(
                    model=self._model,
                    input=batch
                )
                # Extract embeddings in order
                batch_embeddings = [item['embedding'] for item in response.data]
                all_embeddings.extend(batch_embeddings)

            return all_embeddings
        except Exception as e:
            raise RuntimeError(f"LiteLLM batch embedding failed: {e}") from e
