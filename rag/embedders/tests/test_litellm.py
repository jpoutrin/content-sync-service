"""Tests for LiteLLMEmbedder."""

from unittest.mock import MagicMock, patch

import pytest

from rag.embedders.litellm import LiteLLMEmbedder


class TestLiteLLMEmbedderInit:
    """Test LiteLLMEmbedder initialization."""

    def test_init_default_local(self):
        """Test default initialization with local provider."""
        embedder = LiteLLMEmbedder()
        assert embedder.provider == 'local'
        assert embedder.model_name == 'sentence-transformers/all-MiniLM-L6-v2'
        assert embedder._batch_size == 32
        assert embedder._local_model is not None

    def test_init_explicit_openai(self):
        """Test initialization with OpenAI provider."""
        embedder = LiteLLMEmbedder(provider='openai')
        assert embedder.provider == 'openai'
        assert embedder.model_name == 'text-embedding-3-small'
        assert embedder._local_model is None

    @patch('rag.embedders.litellm.SentenceTransformer')
    def test_init_custom_model(self, mock_st):
        """Test initialization with custom model."""
        embedder = LiteLLMEmbedder(provider='local', model='custom-model')
        assert embedder.model_name == 'custom-model'
        mock_st.assert_called_once_with('custom-model')

    def test_init_custom_batch_size(self):
        """Test initialization with custom batch size."""
        embedder = LiteLLMEmbedder(batch_size=64)
        assert embedder._batch_size == 64

    def test_init_invalid_provider(self):
        """Test initialization with invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LiteLLMEmbedder(provider='invalid')  # type: ignore[arg-type]


class TestLiteLLMEmbedderProperties:
    """Test LiteLLMEmbedder properties."""

    def test_dimensions_local(self):
        """Test dimensions property for local provider."""
        embedder = LiteLLMEmbedder(provider='local')
        assert embedder.dimensions == 384

    def test_dimensions_openai(self):
        """Test dimensions property for OpenAI provider."""
        embedder = LiteLLMEmbedder(provider='openai')
        assert embedder.dimensions == 1536

    @patch('rag.embedders.litellm.SentenceTransformer')
    def test_dimensions_unknown_model(self, mock_st):
        """Test dimensions property defaults to 384 for unknown models."""
        embedder = LiteLLMEmbedder(provider='local', model='unknown-model')
        assert embedder.dimensions == 384

    def test_model_name(self):
        """Test model_name property."""
        embedder = LiteLLMEmbedder(provider='local')
        assert embedder.model_name == 'sentence-transformers/all-MiniLM-L6-v2'


class TestLiteLLMEmbedderLocal:
    """Test LiteLLMEmbedder with local provider."""

    def test_embed_local(self):
        """Test embedding single text with local provider."""
        embedder = LiteLLMEmbedder(provider='local')
        vector = embedder.embed("Hello world")

        assert isinstance(vector, list)
        assert len(vector) == 384
        assert all(isinstance(x, float) for x in vector)

    def test_embed_local_empty_text(self):
        """Test embedding empty text raises ValueError."""
        embedder = LiteLLMEmbedder(provider='local')

        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedder.embed("")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedder.embed("   ")

    def test_embed_batch_local(self):
        """Test embedding batch of texts with local provider."""
        embedder = LiteLLMEmbedder(provider='local')
        texts = ["Hello world", "How are you?", "Goodbye"]
        vectors = embedder.embed_batch(texts)

        assert isinstance(vectors, list)
        assert len(vectors) == 3
        assert all(len(v) == 384 for v in vectors)
        assert all(isinstance(x, float) for v in vectors for x in v)

    def test_embed_batch_local_empty_list(self):
        """Test embedding empty list raises ValueError."""
        embedder = LiteLLMEmbedder(provider='local')

        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            embedder.embed_batch([])

    def test_embed_batch_local_contains_empty(self):
        """Test embedding batch with empty string raises ValueError."""
        embedder = LiteLLMEmbedder(provider='local')

        with pytest.raises(ValueError, match="cannot contain empty strings"):
            embedder.embed_batch(["Hello", "", "World"])

        with pytest.raises(ValueError, match="cannot contain empty strings"):
            embedder.embed_batch(["Hello", "   ", "World"])

    def test_embed_batch_local_respects_batch_size(self):
        """Test that batch processing respects batch_size parameter."""
        embedder = LiteLLMEmbedder(provider='local', batch_size=2)
        texts = ["text1", "text2", "text3", "text4", "text5"]
        vectors = embedder.embed_batch(texts)

        assert len(vectors) == 5
        assert all(len(v) == 384 for v in vectors)


class TestLiteLLMEmbedderOpenAI:
    """Test LiteLLMEmbedder with OpenAI provider."""

    @patch('rag.embedders.litellm.litellm.embedding')
    def test_embed_openai(self, mock_embedding):
        """Test embedding single text with OpenAI provider."""
        # Mock LiteLLM response
        mock_response = MagicMock()
        mock_response.data = [{'embedding': [0.1] * 1536}]
        mock_embedding.return_value = mock_response

        embedder = LiteLLMEmbedder(provider='openai')
        vector = embedder.embed("Hello world")

        assert isinstance(vector, list)
        assert len(vector) == 1536
        mock_embedding.assert_called_once_with(
            model='text-embedding-3-small',
            input=["Hello world"]
        )

    @patch('rag.embedders.litellm.litellm.embedding')
    def test_embed_openai_api_error(self, mock_embedding):
        """Test that API errors are caught and raised as RuntimeError."""
        mock_embedding.side_effect = Exception("API error")

        embedder = LiteLLMEmbedder(provider='openai')

        with pytest.raises(RuntimeError, match="LiteLLM embedding failed"):
            embedder.embed("Hello world")

    @patch('rag.embedders.litellm.litellm.embedding')
    def test_embed_batch_openai(self, mock_embedding):
        """Test embedding batch of texts with OpenAI provider."""
        # Mock LiteLLM response
        mock_response = MagicMock()
        mock_response.data = [
            {'embedding': [0.1] * 1536},
            {'embedding': [0.2] * 1536},
            {'embedding': [0.3] * 1536}
        ]
        mock_embedding.return_value = mock_response

        embedder = LiteLLMEmbedder(provider='openai')
        texts = ["Hello", "world", "test"]
        vectors = embedder.embed_batch(texts)

        assert len(vectors) == 3
        assert all(len(v) == 1536 for v in vectors)
        mock_embedding.assert_called_once_with(
            model='text-embedding-3-small',
            input=texts
        )

    @patch('rag.embedders.litellm.litellm.embedding')
    def test_embed_batch_openai_respects_batch_size(self, mock_embedding):
        """Test that batch processing respects batch_size parameter."""
        # Mock LiteLLM response for each batch
        mock_response_1 = MagicMock()
        mock_response_1.data = [
            {'embedding': [0.1] * 1536},
            {'embedding': [0.2] * 1536}
        ]
        mock_response_2 = MagicMock()
        mock_response_2.data = [
            {'embedding': [0.3] * 1536},
            {'embedding': [0.4] * 1536}
        ]
        mock_response_3 = MagicMock()
        mock_response_3.data = [
            {'embedding': [0.5] * 1536}
        ]

        mock_embedding.side_effect = [mock_response_1, mock_response_2, mock_response_3]

        embedder = LiteLLMEmbedder(provider='openai', batch_size=2)
        texts = ["text1", "text2", "text3", "text4", "text5"]
        vectors = embedder.embed_batch(texts)

        assert len(vectors) == 5
        assert all(len(v) == 1536 for v in vectors)
        assert mock_embedding.call_count == 3

        # Verify batching
        calls = mock_embedding.call_args_list
        assert calls[0][1]['input'] == ["text1", "text2"]
        assert calls[1][1]['input'] == ["text3", "text4"]
        assert calls[2][1]['input'] == ["text5"]

    @patch('rag.embedders.litellm.litellm.embedding')
    def test_embed_batch_openai_api_error(self, mock_embedding):
        """Test that batch API errors are caught and raised as RuntimeError."""
        mock_embedding.side_effect = Exception("API error")

        embedder = LiteLLMEmbedder(provider='openai')

        with pytest.raises(RuntimeError, match="LiteLLM batch embedding failed"):
            embedder.embed_batch(["Hello", "world"])


class TestLiteLLMEmbedderInterface:
    """Test that LiteLLMEmbedder implements EmbedderInterface."""

    def test_implements_interface(self):
        """Test that LiteLLMEmbedder implements all required methods."""
        from rag.core.interfaces import EmbedderInterface

        embedder = LiteLLMEmbedder(provider='local')

        # Check instance
        assert isinstance(embedder, EmbedderInterface)

        # Check required methods
        assert hasattr(embedder, 'embed')
        assert hasattr(embedder, 'embed_batch')
        assert hasattr(embedder, 'model_name')
        assert hasattr(embedder, 'dimensions')

        # Check methods are callable
        assert callable(embedder.embed)
        assert callable(embedder.embed_batch)
