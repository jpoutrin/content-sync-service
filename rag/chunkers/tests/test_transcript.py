"""Tests for TranscriptChunker implementation."""

import pytest

from rag.chunkers.transcript import TranscriptChunker
from rag.core.acl import Visibility
from rag.core.schemas import Document


class TestTranscriptChunkerInit:
    """Tests for TranscriptChunker initialization."""

    def test_default_initialization(self):
        """Test chunker with default parameters."""
        chunker = TranscriptChunker()
        assert chunker.gap_threshold == 2.0
        assert chunker.max_chars == 1000
        assert chunker.min_chars == 100

    def test_custom_initialization(self):
        """Test chunker with custom parameters."""
        chunker = TranscriptChunker(gap_threshold=3.0, max_chars=500, min_chars=50)
        assert chunker.gap_threshold == 3.0
        assert chunker.max_chars == 500
        assert chunker.min_chars == 50

    def test_invalid_max_chars_less_than_min_chars(self):
        """Test that max_chars < min_chars raises ValueError."""
        with pytest.raises(ValueError, match="max_chars.*must be >= min_chars"):
            TranscriptChunker(max_chars=50, min_chars=100)

    def test_negative_gap_threshold(self):
        """Test that negative gap_threshold raises ValueError."""
        with pytest.raises(ValueError, match="gap_threshold.*must be >= 0"):
            TranscriptChunker(gap_threshold=-1.0)

    def test_negative_min_chars(self):
        """Test that negative min_chars raises ValueError."""
        with pytest.raises(ValueError, match="min_chars.*must be >= 0"):
            TranscriptChunker(min_chars=-10)


class TestTranscriptChunkerChunk:
    """Tests for TranscriptChunker.chunk() method."""

    @pytest.fixture
    def base_document(self):
        """Create a base document with minimal required fields."""
        return Document(
            id="video:42",
            content="",  # Not used for transcript chunking
            owner_id="user:123",
            visibility=Visibility.PRIVATE,
            metadata={
                "transcript_segments": [],
                "video_title": "Test Video",
                "video_url": "https://example.com/video/42",
                "youtube_video_id": "abc123xyz",
            }
        )

    def test_chunk_simple_transcript(self, base_document):
        """Test chunking a simple transcript with no gaps."""
        base_document.metadata["transcript_segments"] = [
            {"text": "Hello world", "start": 0.0, "duration": 2.0},
            {"text": "This is a test", "start": 2.0, "duration": 2.0},
            {"text": "of transcript chunking", "start": 4.0, "duration": 2.0},
        ]

        chunker = TranscriptChunker(gap_threshold=2.0, max_chars=1000, min_chars=10)
        chunks = chunker.chunk(base_document)

        # Should create one chunk since no gaps exceed threshold
        assert len(chunks) == 1
        assert chunks[0].content == "Hello world This is a test of transcript chunking"
        assert chunks[0].id == "video:42:chunk:0"
        assert chunks[0].document_id == "video:42"
        assert chunks[0].index == 0

        # Check metadata
        metadata = chunks[0].metadata
        assert metadata["start_time"] == 0.0
        assert metadata["end_time"] == 6.0
        assert metadata["segment_count"] == 3
        assert metadata["video_title"] == "Test Video"
        assert metadata["video_url"] == "https://example.com/video/42"
        assert metadata["youtube_video_id"] == "abc123xyz"

    def test_chunk_with_time_gap(self, base_document):
        """Test chunking transcript with time gap exceeding threshold."""
        base_document.metadata["transcript_segments"] = [
            {"text": "First segment", "start": 0.0, "duration": 2.0},
            {"text": "Second segment", "start": 2.0, "duration": 2.0},
            # Large gap here (3 seconds)
            {"text": "Third segment", "start": 7.0, "duration": 2.0},
        ]

        chunker = TranscriptChunker(gap_threshold=2.5, max_chars=1000, min_chars=10)
        chunks = chunker.chunk(base_document)

        # Should create two chunks due to gap
        assert len(chunks) == 2

        # First chunk
        assert chunks[0].content == "First segment Second segment"
        assert chunks[0].id == "video:42:chunk:0"
        assert chunks[0].metadata["start_time"] == 0.0
        assert chunks[0].metadata["end_time"] == 4.0
        assert chunks[0].metadata["segment_count"] == 2

        # Second chunk
        assert chunks[1].content == "Third segment"
        assert chunks[1].id == "video:42:chunk:1"
        assert chunks[1].metadata["start_time"] == 7.0
        assert chunks[1].metadata["end_time"] == 9.0
        assert chunks[1].metadata["segment_count"] == 1

    def test_chunk_respects_max_chars(self, base_document):
        """Test that chunks are split when max_chars is exceeded."""
        base_document.metadata["transcript_segments"] = [
            {"text": "A" * 50, "start": 0.0, "duration": 1.0},
            {"text": "B" * 50, "start": 1.0, "duration": 1.0},
            {"text": "C" * 50, "start": 2.0, "duration": 1.0},
        ]

        chunker = TranscriptChunker(gap_threshold=5.0, max_chars=80, min_chars=10)
        chunks = chunker.chunk(base_document)

        # Should split due to max_chars
        assert len(chunks) >= 2

        # Each chunk should be under max_chars
        for chunk in chunks:
            assert len(chunk.content) <= 80

    def test_chunk_respects_min_chars(self, base_document):
        """Test that small chunks below min_chars are avoided when possible."""
        base_document.metadata["transcript_segments"] = [
            {"text": "Small", "start": 0.0, "duration": 1.0},
            # Large gap
            {"text": "Another small chunk", "start": 10.0, "duration": 1.0},
        ]

        chunker = TranscriptChunker(gap_threshold=2.0, max_chars=1000, min_chars=100)
        chunks = chunker.chunk(base_document)

        # Both segments are too small individually, but still created
        # because they're the only option
        assert len(chunks) == 2

    def test_chunk_acl_fields_preserved(self, base_document):
        """Test that ACL fields are copied from document to chunks."""
        base_document.owner_id = "user:999"
        base_document.visibility = Visibility.SHARED
        base_document.shared_with_users = ["user:111", "user:222"]
        base_document.shared_with_groups = ["group:aaa"]
        base_document.tenant_id = "tenant:xyz"
        base_document.metadata["transcript_segments"] = [
            {"text": "Test content", "start": 0.0, "duration": 2.0},
        ]

        chunker = TranscriptChunker()
        chunks = chunker.chunk(base_document)

        assert len(chunks) == 1
        chunk = chunks[0]

        # ACL fields should be copied
        assert chunk.owner_id == "user:999"
        assert chunk.visibility == Visibility.SHARED
        assert chunk.shared_with_users == ["user:111", "user:222"]
        assert chunk.shared_with_groups == ["group:aaa"]
        assert chunk.tenant_id == "tenant:xyz"

    def test_chunk_empty_segments_raises_error(self, base_document):
        """Test that empty transcript_segments raises ValueError."""
        base_document.metadata["transcript_segments"] = []

        chunker = TranscriptChunker()
        with pytest.raises(ValueError, match="must contain 'transcript_segments' list"):
            chunker.chunk(base_document)

    def test_chunk_missing_transcript_segments_raises_error(self):
        """Test that missing transcript_segments raises ValueError."""
        document = Document(
            id="video:42",
            content="",
            owner_id="user:123",
            metadata={
                "video_title": "Test",
                "video_url": "https://example.com/42",
                "youtube_video_id": "abc",
            }
        )

        chunker = TranscriptChunker()
        with pytest.raises(ValueError, match="must contain 'transcript_segments' list"):
            chunker.chunk(document)

    def test_chunk_missing_video_metadata_raises_error(self, base_document):
        """Test that missing video metadata raises ValueError."""
        base_document.metadata = {
            "transcript_segments": [
                {"text": "Test", "start": 0.0, "duration": 1.0}
            ],
            # Missing video_title, video_url, youtube_video_id
        }

        chunker = TranscriptChunker()
        with pytest.raises(ValueError, match="must contain 'video_title'"):
            chunker.chunk(base_document)

    def test_chunk_invalid_document_id_format(self, base_document):
        """Test that invalid document ID format raises ValueError."""
        base_document.id = "invalid:format:123"
        base_document.metadata["transcript_segments"] = [
            {"text": "Test", "start": 0.0, "duration": 1.0}
        ]

        chunker = TranscriptChunker()
        with pytest.raises(ValueError, match="Document ID must start with 'video:'"):
            chunker.chunk(base_document)

    def test_chunk_invalid_segment_format(self, base_document):
        """Test that invalid segment format raises ValueError."""
        base_document.metadata["transcript_segments"] = [
            {"text": "Valid segment", "start": 0.0, "duration": 1.0},
            {"text": "Missing start field", "duration": 1.0},  # Invalid
        ]

        chunker = TranscriptChunker()
        with pytest.raises(ValueError, match="must have 'text', 'start', and 'duration' fields"):
            chunker.chunk(base_document)

    def test_chunk_non_dict_segment(self, base_document):
        """Test that non-dict segments raise ValueError."""
        base_document.metadata["transcript_segments"] = [
            "not a dict",  # Invalid
        ]

        chunker = TranscriptChunker()
        with pytest.raises(ValueError, match="must be a dictionary"):
            chunker.chunk(base_document)

    def test_chunk_skips_empty_text_segments(self, base_document):
        """Test that segments with empty text are skipped."""
        base_document.metadata["transcript_segments"] = [
            {"text": "First", "start": 0.0, "duration": 1.0},
            {"text": "   ", "start": 1.0, "duration": 1.0},  # Empty after strip
            {"text": "", "start": 2.0, "duration": 1.0},  # Empty
            {"text": "Second", "start": 3.0, "duration": 1.0},
        ]

        chunker = TranscriptChunker(gap_threshold=5.0)
        chunks = chunker.chunk(base_document)

        assert len(chunks) == 1
        assert chunks[0].content == "First Second"
        assert chunks[0].metadata["segment_count"] == 2

    def test_chunk_id_format(self, base_document):
        """Test that chunk IDs follow the correct format."""
        base_document.metadata["transcript_segments"] = [
            {"text": "First chunk", "start": 0.0, "duration": 2.0},
            {"text": "Second chunk after gap", "start": 10.0, "duration": 2.0},
            {"text": "Third chunk after gap", "start": 20.0, "duration": 2.0},
        ]

        chunker = TranscriptChunker(gap_threshold=2.0)
        chunks = chunker.chunk(base_document)

        # Check chunk ID format: video:{video_pk}:chunk:{index}
        assert chunks[0].id == "video:42:chunk:0"
        assert chunks[1].id == "video:42:chunk:1"
        assert chunks[2].id == "video:42:chunk:2"

    def test_chunk_complex_video_pk(self):
        """Test chunking with complex video primary key."""
        document = Document(
            id="video:abc-123-xyz",
            content="",
            owner_id="user:123",
            metadata={
                "transcript_segments": [
                    {"text": "Test content", "start": 0.0, "duration": 1.0}
                ],
                "video_title": "Test",
                "video_url": "https://example.com/video/abc-123-xyz",
                "youtube_video_id": "xyz",
            }
        )

        chunker = TranscriptChunker()
        chunks = chunker.chunk(document)

        assert len(chunks) == 1
        assert chunks[0].id == "video:abc-123-xyz:chunk:0"

    def test_chunk_multiple_chunks_with_mixed_conditions(self, base_document):
        """Test chunking with both time gaps and size limits."""
        base_document.metadata["transcript_segments"] = [
            {"text": "A" * 30, "start": 0.0, "duration": 1.0},
            {"text": "B" * 30, "start": 1.0, "duration": 1.0},
            # Time gap triggers split
            {"text": "C" * 30, "start": 10.0, "duration": 1.0},
            {"text": "D" * 30, "start": 11.0, "duration": 1.0},
            {"text": "E" * 30, "start": 12.0, "duration": 1.0},
            # This should trigger size-based split
            {"text": "F" * 30, "start": 13.0, "duration": 1.0},
        ]

        chunker = TranscriptChunker(gap_threshold=2.0, max_chars=100, min_chars=20)
        chunks = chunker.chunk(base_document)

        # Should have multiple chunks due to both gap and size constraints
        assert len(chunks) >= 2

        # Each chunk should respect max_chars
        for chunk in chunks:
            assert len(chunk.content) <= 100

    def test_chunk_single_large_segment(self, base_document):
        """Test that a single segment exceeding max_chars is still created."""
        base_document.metadata["transcript_segments"] = [
            {"text": "A" * 200, "start": 0.0, "duration": 1.0},
        ]

        chunker = TranscriptChunker(max_chars=100, min_chars=50)
        chunks = chunker.chunk(base_document)

        # Single segment should create one chunk even if it exceeds max_chars
        assert len(chunks) == 1
        assert len(chunks[0].content) == 200
