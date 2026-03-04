"""Tests for IngestionService."""

from unittest.mock import Mock

import pytest

from rag.core.acl import Visibility
from rag.core.schemas import Chunk, Document, DocumentType, Embedding
from rag.services.ingestion import IngestionService


class TestIngestionService:
    """Test suite for IngestionService."""

    @pytest.fixture
    def mock_chunker(self):
        """Create a mock chunker."""
        chunker = Mock()
        # Return sample chunks
        chunker.chunk.return_value = [
            Chunk(
                id="video:123:chunk:0",
                document_id="video:123",
                content="First chunk content",
                index=0,
                metadata={
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "segment_count": 5,
                    "video_title": "Test Video",
                    "video_url": "https://example.com/video/123",
                    "youtube_video_id": "abc123",
                },
                owner_id="user-1",
                visibility=Visibility.PRIVATE,
                shared_with_users=[],
                shared_with_groups=[],
                tenant_id=None,
            ),
            Chunk(
                id="video:123:chunk:1",
                document_id="video:123",
                content="Second chunk content",
                index=1,
                metadata={
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "segment_count": 4,
                    "video_title": "Test Video",
                    "video_url": "https://example.com/video/123",
                    "youtube_video_id": "abc123",
                },
                owner_id="user-1",
                visibility=Visibility.PRIVATE,
                shared_with_users=[],
                shared_with_groups=[],
                tenant_id=None,
            ),
        ]
        return chunker

    @pytest.fixture
    def mock_embedder(self):
        """Create a mock embedder."""
        embedder = Mock()
        embedder.model_name = "test-model"
        embedder.dimensions = 384
        # Return sample embeddings
        embedder.embed_batch.return_value = [
            [0.1] * 384,  # First embedding
            [0.2] * 384,  # Second embedding
        ]
        return embedder

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        store = Mock()
        store.upsert_batch.return_value = None
        return store

    @pytest.fixture
    def ingestion_service(self, mock_chunker, mock_embedder, mock_vector_store):
        """Create an IngestionService with mocked dependencies."""
        return IngestionService(mock_chunker, mock_embedder, mock_vector_store)

    @pytest.fixture
    def sample_video(self):
        """Create a sample video object."""
        # Create mock user
        user = Mock()
        user.id = "user-123"

        # Create mock source
        source = Mock()
        source.user = user

        # Create mock video
        video = Mock()
        video.id = "video-uuid-123"
        video.pk = 123
        video.source = source
        video.youtube_video_id = "abc123xyz"
        video.title = "Test Video Title"
        video.url = "https://youtube.com/watch?v=abc123xyz"
        video.transcript_data = [
            {"text": "Hello world", "start": 0.0, "duration": 2.0},
            {"text": "This is a test", "start": 2.5, "duration": 3.0},
        ]
        return video

    def test_init(self, mock_chunker, mock_embedder, mock_vector_store):
        """Test IngestionService initialization."""
        service = IngestionService(mock_chunker, mock_embedder, mock_vector_store)
        assert service.chunker is mock_chunker
        assert service.embedder is mock_embedder
        assert service.vector_store is mock_vector_store

    def test_ingest_video_success(self, ingestion_service, sample_video):
        """Test successful video ingestion."""
        count = ingestion_service.ingest_video(sample_video)

        # Should return count of chunks
        assert count == 2

        # Verify chunker was called with correct Document
        ingestion_service.chunker.chunk.assert_called_once()
        doc_arg = ingestion_service.chunker.chunk.call_args[0][0]
        assert isinstance(doc_arg, Document)
        assert doc_arg.id == "video:123"
        assert doc_arg.type == DocumentType.TRANSCRIPT
        assert doc_arg.owner_id == "user-123"
        assert doc_arg.visibility == Visibility.PRIVATE
        assert doc_arg.metadata["youtube_video_id"] == "abc123xyz"
        assert doc_arg.metadata["video_title"] == "Test Video Title"
        assert doc_arg.metadata["transcript_segments"] == sample_video.transcript_data

        # Verify embedder was called with chunk contents
        ingestion_service.embedder.embed_batch.assert_called_once_with(
            ["First chunk content", "Second chunk content"]
        )

        # Verify vector store was called with chunks and embeddings
        ingestion_service.vector_store.upsert_batch.assert_called_once()
        chunks_arg, embeddings_arg = (
            ingestion_service.vector_store.upsert_batch.call_args[0]
        )
        assert len(chunks_arg) == 2
        assert len(embeddings_arg) == 2
        assert all(isinstance(c, Chunk) for c in chunks_arg)
        assert all(isinstance(e, Embedding) for e in embeddings_arg)
        assert embeddings_arg[0].chunk_id == "video:123:chunk:0"
        assert embeddings_arg[0].model == "test-model"
        assert embeddings_arg[0].dimensions == 384

    def test_ingest_video_no_transcript(self, ingestion_service, sample_video):
        """Test ingestion fails when video has no transcript."""
        sample_video.transcript_data = None

        with pytest.raises(ValueError, match="has no transcript data"):
            ingestion_service.ingest_video(sample_video)

        # Should not call any downstream services
        ingestion_service.chunker.chunk.assert_not_called()
        ingestion_service.embedder.embed_batch.assert_not_called()
        ingestion_service.vector_store.upsert_batch.assert_not_called()

    def test_ingest_video_empty_transcript(self, ingestion_service, sample_video):
        """Test ingestion fails when video has empty transcript."""
        sample_video.transcript_data = []

        with pytest.raises(ValueError, match="has no transcript data"):
            ingestion_service.ingest_video(sample_video)

    def test_ingest_video_missing_source(self, ingestion_service, sample_video):
        """Test ingestion fails when video has no source."""
        sample_video.source = None

        with pytest.raises(ValueError, match="missing source or user relationship"):
            ingestion_service.ingest_video(sample_video)

    def test_ingest_video_missing_user(self, ingestion_service, sample_video):
        """Test ingestion fails when source has no user."""
        sample_video.source.user = None

        with pytest.raises(ValueError, match="missing source or user relationship"):
            ingestion_service.ingest_video(sample_video)

    def test_ingest_video_missing_youtube_id(self, ingestion_service, sample_video):
        """Test ingestion fails when video has no YouTube ID."""
        sample_video.youtube_video_id = None

        with pytest.raises(ValueError, match="missing youtube_video_id"):
            ingestion_service.ingest_video(sample_video)

    def test_ingest_video_missing_title(self, ingestion_service, sample_video):
        """Test ingestion fails when video has no title."""
        sample_video.title = None

        with pytest.raises(ValueError, match="missing title"):
            ingestion_service.ingest_video(sample_video)

    def test_ingest_video_missing_url(self, ingestion_service, sample_video):
        """Test ingestion fails when video has no URL."""
        sample_video.url = None

        with pytest.raises(ValueError, match="missing url"):
            ingestion_service.ingest_video(sample_video)

    def test_ingest_video_chunking_fails(
        self, ingestion_service, sample_video, mock_chunker
    ):
        """Test ingestion handles chunking failures."""
        mock_chunker.chunk.side_effect = Exception("Chunking error")

        with pytest.raises(RuntimeError, match="Chunking failed"):
            ingestion_service.ingest_video(sample_video)

        # Should not call embedder or storage
        ingestion_service.embedder.embed_batch.assert_not_called()
        ingestion_service.vector_store.upsert_batch.assert_not_called()

    def test_ingest_video_no_chunks_generated(
        self, ingestion_service, sample_video, mock_chunker
    ):
        """Test ingestion fails when no chunks are generated."""
        mock_chunker.chunk.return_value = []

        with pytest.raises(ValueError, match="No chunks generated"):
            ingestion_service.ingest_video(sample_video)

        # Should not call embedder or storage
        ingestion_service.embedder.embed_batch.assert_not_called()
        ingestion_service.vector_store.upsert_batch.assert_not_called()

    def test_ingest_video_embedding_fails(
        self, ingestion_service, sample_video, mock_embedder
    ):
        """Test ingestion handles embedding failures."""
        mock_embedder.embed_batch.side_effect = Exception("Embedding error")

        with pytest.raises(RuntimeError, match="Embedding failed"):
            ingestion_service.ingest_video(sample_video)

        # Should not call storage
        ingestion_service.vector_store.upsert_batch.assert_not_called()

    def test_ingest_video_storage_fails(
        self, ingestion_service, sample_video, mock_vector_store
    ):
        """Test ingestion handles storage failures."""
        mock_vector_store.upsert_batch.side_effect = Exception("Storage error")

        with pytest.raises(RuntimeError, match="Storage failed"):
            ingestion_service.ingest_video(sample_video)

    def test_build_document_from_video(self, ingestion_service, sample_video):
        """Test document building from video."""
        document = ingestion_service._build_document_from_video(sample_video)

        assert document.id == "video:123"
        assert document.type == DocumentType.TRANSCRIPT
        assert document.owner_id == "user-123"
        assert document.visibility == Visibility.PRIVATE
        assert document.shared_with_users == []
        assert document.shared_with_groups == []
        assert document.tenant_id is None
        assert document.source_id == "video-uuid-123"
        assert document.metadata["transcript_segments"] == sample_video.transcript_data
        assert document.metadata["video_title"] == "Test Video Title"
        assert document.metadata["video_url"] == sample_video.url
        assert document.metadata["youtube_video_id"] == "abc123xyz"

    def test_acl_metadata_propagated(self, ingestion_service, sample_video):
        """Test that ACL metadata is properly set in the document."""
        document = ingestion_service._build_document_from_video(sample_video)

        # Verify ACL fields are set correctly
        assert document.owner_id == str(sample_video.source.user.id)
        assert document.visibility == Visibility.PRIVATE
        assert isinstance(document.shared_with_users, list)
        assert isinstance(document.shared_with_groups, list)

    def test_document_id_format(self, ingestion_service, sample_video):
        """Test that document ID follows the correct format."""
        document = ingestion_service._build_document_from_video(sample_video)
        assert document.id == f"video:{sample_video.pk}"
        assert document.id.startswith("video:")
