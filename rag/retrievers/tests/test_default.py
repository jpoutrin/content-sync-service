"""Tests for DefaultRetriever."""

from unittest.mock import Mock

import pytest

from rag.core.acl import QueryACLContext, Visibility
from rag.core.schemas import Chunk, SearchQuery, SearchResult
from rag.retrievers.default import DefaultRetriever


class TestDefaultRetriever:
    """Test suite for DefaultRetriever."""

    @pytest.fixture
    def mock_embedder(self):
        """Create a mock embedder."""
        embedder = Mock()
        embedder.embed.return_value = [0.1] * 384  # Mock 384-dim vector
        return embedder

    @pytest.fixture
    def mock_store(self):
        """Create a mock vector store."""
        store = Mock()
        return store

    @pytest.fixture
    def retriever(self, mock_embedder, mock_store):
        """Create a DefaultRetriever instance with mocked dependencies."""
        return DefaultRetriever(embedder=mock_embedder, store=mock_store)

    @pytest.fixture
    def sample_chunk(self):
        """Create a sample chunk with YouTube metadata."""
        return Chunk(
            id="video:42:chunk:5",
            document_id="video:42",
            content="To configure Django settings, edit settings.py",
            index=5,
            metadata={
                "start_time": 125.5,
                "end_time": 185.2,
                "video_title": "Django Tutorial",
                "video_url": "https://youtube.com/watch?v=abc123",
                "youtube_video_id": "abc123",
                "segment_count": 3
            },
            owner_id="user-123",
            visibility=Visibility.PUBLIC
        )

    @pytest.fixture
    def sample_query(self):
        """Create a sample search query."""
        return SearchQuery(
            text="How to configure Django?",
            top_k=5,
            acl_context=QueryACLContext(principal_id="user-456")
        )

    def test_retrieve_basic(self, retriever, mock_embedder, mock_store, sample_chunk, sample_query):
        """Test basic retrieve operation."""
        # Setup mock responses
        mock_store.search.return_value = [(sample_chunk, 0.89)]

        # Execute
        results = retriever.retrieve(sample_query)

        # Verify embedder was called
        mock_embedder.embed.assert_called_once_with(sample_query.text)

        # Verify store search was called with correct parameters
        mock_store.search.assert_called_once()
        call_args = mock_store.search.call_args
        assert call_args.kwargs["top_k"] == 5
        assert call_args.kwargs["acl_context"] == sample_query.acl_context

        # Verify results
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].chunk == sample_chunk
        assert results[0].score == 0.89

    def test_retrieve_enriches_timestamp_url(self, retriever, mock_embedder, mock_store, sample_chunk, sample_query):
        """Test that retrieve enriches results with timestamp URL."""
        mock_store.search.return_value = [(sample_chunk, 0.89)]

        results = retriever.retrieve(sample_query)

        # Verify timestamp_url was added to metadata
        assert len(results) == 1
        metadata = results[0].document_metadata
        assert "timestamp_url" in metadata
        assert metadata["timestamp_url"] == "https://youtube.com/watch?v=abc123&t=125"

    def test_retrieve_timestamp_url_rounds_to_seconds(self, retriever, mock_embedder, mock_store, sample_chunk, sample_query):
        """Test that timestamp URL uses integer seconds."""
        # Chunk with fractional start time
        chunk = Chunk(
            id="video:42:chunk:5",
            document_id="video:42",
            content="Test content",
            index=5,
            metadata={
                "start_time": 125.789,  # Should round to 125
                "youtube_video_id": "abc123"
            },
            owner_id="user-123",
            visibility=Visibility.PUBLIC
        )
        mock_store.search.return_value = [(chunk, 0.89)]

        results = retriever.retrieve(sample_query)

        metadata = results[0].document_metadata
        assert metadata["timestamp_url"] == "https://youtube.com/watch?v=abc123&t=125"

    def test_retrieve_without_youtube_metadata(self, retriever, mock_embedder, mock_store, sample_query):
        """Test retrieve with chunk that has no YouTube metadata."""
        chunk = Chunk(
            id="doc:1:chunk:0",
            document_id="doc:1",
            content="Some other content",
            index=0,
            metadata={},  # No YouTube metadata
            owner_id="user-123",
            visibility=Visibility.PUBLIC
        )
        mock_store.search.return_value = [(chunk, 0.75)]

        results = retriever.retrieve(sample_query)

        # Should not have timestamp_url
        assert len(results) == 1
        assert "timestamp_url" not in results[0].document_metadata

    def test_retrieve_with_min_score_filter(self, retriever, mock_embedder, mock_store, sample_chunk, sample_query):
        """Test that min_score filtering works correctly."""
        # Create chunks with different scores
        chunk1 = sample_chunk
        chunk2 = Chunk(
            id="video:42:chunk:6",
            document_id="video:42",
            content="Another chunk",
            index=6,
            metadata={"youtube_video_id": "abc123", "start_time": 200.0},
            owner_id="user-123",
            visibility=Visibility.PUBLIC
        )

        mock_store.search.return_value = [
            (chunk1, 0.89),
            (chunk2, 0.65)
        ]

        # Query with min_score threshold
        query_with_min_score = SearchQuery(
            text="Django configuration",
            top_k=5,
            min_score=0.7,
            acl_context=QueryACLContext(principal_id="user-456")
        )

        results = retriever.retrieve(query_with_min_score)

        # Only chunk1 should pass the threshold
        assert len(results) == 1
        assert results[0].chunk.id == "video:42:chunk:5"
        assert results[0].score == 0.89

    def test_retrieve_multiple_results_sorted(self, retriever, mock_embedder, mock_store, sample_query):
        """Test that multiple results are returned in order."""
        chunks = [
            Chunk(
                id=f"video:42:chunk:{i}",
                document_id="video:42",
                content=f"Content {i}",
                index=i,
                metadata={"youtube_video_id": "abc123", "start_time": float(i * 100)},
                owner_id="user-123",
                visibility=Visibility.PUBLIC
            )
            for i in range(3)
        ]

        # Store returns in descending score order
        mock_store.search.return_value = [
            (chunks[2], 0.95),
            (chunks[0], 0.88),
            (chunks[1], 0.75)
        ]

        results = retriever.retrieve(sample_query)

        # Verify order is preserved
        assert len(results) == 3
        assert results[0].score == 0.95
        assert results[1].score == 0.88
        assert results[2].score == 0.75

    def test_retrieve_empty_query_raises_error(self, retriever, sample_query):
        """Test that empty query text raises ValueError."""
        sample_query.text = ""
        with pytest.raises(ValueError, match="Query text cannot be empty"):
            retriever.retrieve(sample_query)

        sample_query.text = "   "
        with pytest.raises(ValueError, match="Query text cannot be empty"):
            retriever.retrieve(sample_query)

    def test_retrieve_invalid_top_k_raises_error(self, retriever, sample_query):
        """Test that invalid top_k raises ValueError."""
        sample_query.top_k = 0
        with pytest.raises(ValueError, match="top_k must be at least 1"):
            retriever.retrieve(sample_query)

        sample_query.top_k = -5
        with pytest.raises(ValueError, match="top_k must be at least 1"):
            retriever.retrieve(sample_query)

    def test_retrieve_invalid_min_score_raises_error(self, retriever, sample_query):
        """Test that invalid min_score raises ValueError."""
        sample_query.min_score = 1.5
        with pytest.raises(ValueError, match="min_score must be between 0.0 and 1.0"):
            retriever.retrieve(sample_query)

        sample_query.min_score = -0.1
        with pytest.raises(ValueError, match="min_score must be between 0.0 and 1.0"):
            retriever.retrieve(sample_query)

    def test_retrieve_embedding_failure_raises_runtime_error(self, retriever, mock_embedder, sample_query):
        """Test that embedding failure raises RuntimeError."""
        mock_embedder.embed.side_effect = Exception("Embedding API failed")

        with pytest.raises(RuntimeError, match="Failed to embed query"):
            retriever.retrieve(sample_query)

    def test_retrieve_search_failure_raises_runtime_error(self, retriever, mock_embedder, mock_store, sample_query):
        """Test that search failure raises RuntimeError."""
        mock_store.search.side_effect = Exception("Database connection failed")

        with pytest.raises(RuntimeError, match="Vector store search failed"):
            retriever.retrieve(sample_query)

    def test_retrieve_passes_acl_context_to_store(self, retriever, mock_embedder, mock_store, sample_chunk, sample_query):
        """Test that ACL context is passed to store.search."""
        mock_store.search.return_value = [(sample_chunk, 0.89)]

        retriever.retrieve(sample_query)

        # Verify ACL context was passed
        call_args = mock_store.search.call_args
        assert call_args.kwargs["acl_context"] == sample_query.acl_context

    def test_retrieve_passes_filters_to_store(self, retriever, mock_embedder, mock_store, sample_chunk):
        """Test that metadata filters are passed to store.search."""
        query = SearchQuery(
            text="test query",
            top_k=5,
            filters={"video_id": "42"},
            acl_context=QueryACLContext(principal_id="user-456")
        )
        mock_store.search.return_value = [(sample_chunk, 0.89)]

        retriever.retrieve(query)

        # Verify filters were passed
        call_args = mock_store.search.call_args
        assert call_args.kwargs["filters"] == {"video_id": "42"}

    def test_index_document_not_implemented(self, retriever):
        """Test that index_document raises NotImplementedError."""
        from rag.core.schemas import Document, DocumentType

        doc = Document(
            id="doc:1",
            content="Test content",
            type=DocumentType.TRANSCRIPT,
            owner_id="user-123"
        )

        with pytest.raises(NotImplementedError, match="Use rag.services.ingestion.IngestionService"):
            retriever.index_document(doc)

    def test_remove_document(self, retriever, mock_store):
        """Test remove_document delegates to store."""
        retriever.remove_document("video:42")

        mock_store.delete_by_document.assert_called_once_with("video:42")

    def test_remove_document_empty_id_raises_error(self, retriever):
        """Test that empty document_id raises ValueError."""
        with pytest.raises(ValueError, match="document_id cannot be empty"):
            retriever.remove_document("")

        with pytest.raises(ValueError, match="document_id cannot be empty"):
            retriever.remove_document("   ")

    def test_enrich_metadata_preserves_existing_fields(self, retriever, sample_chunk):
        """Test that _enrich_chunk_metadata preserves existing metadata."""
        enriched = retriever._enrich_chunk_metadata(sample_chunk)

        # All original fields should be present
        assert enriched["start_time"] == 125.5
        assert enriched["end_time"] == 185.2
        assert enriched["video_title"] == "Django Tutorial"
        assert enriched["video_url"] == "https://youtube.com/watch?v=abc123"
        assert enriched["youtube_video_id"] == "abc123"
        assert enriched["segment_count"] == 3

        # Plus the new timestamp_url
        assert "timestamp_url" in enriched

    def test_enrich_metadata_missing_video_id(self, retriever):
        """Test enrichment when youtube_video_id is missing."""
        chunk = Chunk(
            id="video:42:chunk:5",
            document_id="video:42",
            content="Test",
            index=5,
            metadata={"start_time": 125.5},  # No youtube_video_id
            owner_id="user-123",
            visibility=Visibility.PUBLIC
        )

        enriched = retriever._enrich_chunk_metadata(chunk)

        # Should not add timestamp_url
        assert "timestamp_url" not in enriched
        assert enriched["start_time"] == 125.5

    def test_enrich_metadata_missing_start_time(self, retriever):
        """Test enrichment when start_time is missing."""
        chunk = Chunk(
            id="video:42:chunk:5",
            document_id="video:42",
            content="Test",
            index=5,
            metadata={"youtube_video_id": "abc123"},  # No start_time
            owner_id="user-123",
            visibility=Visibility.PUBLIC
        )

        enriched = retriever._enrich_chunk_metadata(chunk)

        # Should not add timestamp_url
        assert "timestamp_url" not in enriched
        assert enriched["youtube_video_id"] == "abc123"

    def test_retrieve_with_acl_filtering(self, retriever, mock_embedder, mock_store, sample_query):
        """Test that ACL context is properly used in search."""
        # Create chunks with different ACL settings
        public_chunk = Chunk(
            id="video:1:chunk:0",
            document_id="video:1",
            content="Public content",
            index=0,
            metadata={"youtube_video_id": "vid1", "start_time": 0.0},
            owner_id="user-123",
            visibility=Visibility.PUBLIC
        )

        # Store should only return chunks that pass ACL
        mock_store.search.return_value = [(public_chunk, 0.85)]

        retriever.retrieve(sample_query)

        # Verify store.search was called with ACL context
        call_args = mock_store.search.call_args
        assert call_args.kwargs["acl_context"] is not None
        assert call_args.kwargs["acl_context"].principal_id == "user-456"
