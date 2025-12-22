"""Tests for rag_ingest management command."""

from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError

import pytest

from yt_sync.models import Source, Video


@pytest.mark.django_db
class TestRagIngestCommand:
    """Test suite for rag_ingest management command."""

    @pytest.fixture
    def user(self):
        """Create a test user."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
        )

    @pytest.fixture
    def source(self, user):
        """Create a test source."""
        return Source.objects.create(
            user=user,
            type=Source.SourceType.CHANNEL,
            youtube_id="UC123456",
            title="Test Channel",
            url="https://youtube.com/channel/UC123456",
        )

    @pytest.fixture
    def video_with_transcript(self, source):
        """Create a video with completed transcript."""
        return Video.objects.create(
            source=source,
            youtube_video_id="test-video-123",
            title="Test Video with Transcript",
            url="https://youtube.com/watch?v=test-video-123",
            published_at="2024-01-01T00:00:00Z",
            transcript_status=Video.ProcessingStatus.COMPLETED,
            transcript_data=[
                {"text": "Hello world", "start": 0.0, "duration": 2.0},
                {"text": "This is a test", "start": 2.5, "duration": 1.5},
            ],
        )

    @pytest.fixture
    def video_without_transcript(self, source):
        """Create a video without transcript."""
        return Video.objects.create(
            source=source,
            youtube_video_id="test-video-456",
            title="Test Video without Transcript",
            url="https://youtube.com/watch?v=test-video-456",
            published_at="2024-01-02T00:00:00Z",
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=None,
        )

    def test_requires_filter_argument(self):
        """Test that command requires at least one filter argument."""
        with pytest.raises(CommandError) as exc_info:
            call_command("rag_ingest")

        assert "You must specify one of" in str(exc_info.value)

    def test_rejects_multiple_filters(self):
        """Test that command rejects multiple filter arguments."""
        with pytest.raises(CommandError) as exc_info:
            call_command("rag_ingest", "--all", "--video-id", "123")

        assert "You can only specify one of" in str(exc_info.value)

    @patch("rag.management.commands.rag_ingest.IngestionService")
    def test_ingest_specific_video_by_uuid(
        self, mock_service_class, video_with_transcript
    ):
        """Test ingesting a specific video by UUID."""
        # Setup mock
        mock_service = Mock()
        mock_service.ingest_video.return_value = 5
        mock_service_class.return_value = mock_service

        # Run command
        out = StringIO()
        call_command(
            "rag_ingest",
            "--video-id",
            str(video_with_transcript.id),
            stdout=out,
        )

        # Verify
        output = out.getvalue()
        assert "Found 1 videos to process" in output
        assert "Successfully ingested: 1" in output
        assert "5 chunks" in output
        mock_service.ingest_video.assert_called_once()

    @patch("rag.management.commands.rag_ingest.IngestionService")
    def test_ingest_specific_video_by_youtube_id(
        self, mock_service_class, video_with_transcript
    ):
        """Test ingesting a specific video by YouTube ID."""
        # Setup mock
        mock_service = Mock()
        mock_service.ingest_video.return_value = 3
        mock_service_class.return_value = mock_service

        # Run command
        out = StringIO()
        call_command(
            "rag_ingest",
            "--video-id",
            video_with_transcript.youtube_video_id,
            stdout=out,
        )

        # Verify
        output = out.getvalue()
        assert "Found 1 videos to process" in output
        assert "Successfully ingested: 1" in output
        mock_service.ingest_video.assert_called_once()

    def test_video_id_not_found(self):
        """Test error when video ID doesn't exist."""
        with pytest.raises(CommandError) as exc_info:
            call_command("rag_ingest", "--video-id", "nonexistent-id")

        assert "not found" in str(exc_info.value)

    @patch("rag.management.commands.rag_ingest.IngestionService")
    def test_ingest_by_source(self, mock_service_class, source, video_with_transcript):
        """Test ingesting all videos from a source."""
        # Setup mock
        mock_service = Mock()
        mock_service.ingest_video.return_value = 4
        mock_service_class.return_value = mock_service

        # Run command
        out = StringIO()
        call_command(
            "rag_ingest",
            "--source",
            source.youtube_id,
            stdout=out,
        )

        # Verify
        output = out.getvalue()
        assert "Found 1 videos to process" in output
        assert "Successfully ingested: 1" in output
        mock_service.ingest_video.assert_called_once()

    def test_source_not_found(self):
        """Test error when source doesn't exist."""
        with pytest.raises(CommandError) as exc_info:
            call_command("rag_ingest", "--source", "nonexistent-source")

        assert "not found" in str(exc_info.value)

    @patch("rag.management.commands.rag_ingest.IngestionService")
    def test_ingest_all_videos(
        self,
        mock_service_class,
        video_with_transcript,
        video_without_transcript,
    ):
        """Test ingesting all videos with transcripts."""
        # Setup mock
        mock_service = Mock()
        mock_service.ingest_video.return_value = 6
        mock_service_class.return_value = mock_service

        # Run command
        out = StringIO()
        call_command("rag_ingest", "--all", stdout=out)

        # Verify - should only process video with transcript
        output = out.getvalue()
        assert "Found 1 videos to process" in output
        assert "Successfully ingested: 1" in output
        mock_service.ingest_video.assert_called_once()

    @patch("rag.management.commands.rag_ingest.IngestionService")
    def test_dry_run_mode(self, mock_service_class, video_with_transcript):
        """Test dry run mode doesn't actually ingest."""
        # Setup mock
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Run command
        out = StringIO()
        call_command(
            "rag_ingest",
            "--video-id",
            str(video_with_transcript.id),
            "--dry-run",
            stdout=out,
        )

        # Verify
        output = out.getvalue()
        assert "DRY RUN" in output
        assert "Would ingest" in output
        # Should not call ingest_video in dry run mode
        mock_service.ingest_video.assert_not_called()

    @patch("rag.management.commands.rag_ingest.IngestionService")
    @patch("rag.management.commands.rag_ingest.PgVectorStore")
    def test_reingest_flag_deletes_existing(
        self, mock_store_class, mock_service_class, video_with_transcript
    ):
        """Test that reingest flag deletes existing chunks."""
        # Setup mocks
        mock_service = Mock()
        mock_service.ingest_video.return_value = 5
        mock_service_class.return_value = mock_service

        mock_store = Mock()
        mock_store_class.return_value = mock_store

        # Run command
        out = StringIO()
        call_command(
            "rag_ingest",
            "--video-id",
            str(video_with_transcript.id),
            "--reingest",
            stdout=out,
        )

        # Verify
        output = out.getvalue()
        assert "Re-ingesting" in output
        # Should call delete_by_document for reingest
        mock_store.delete_by_document.assert_called_once_with(
            f"video:{video_with_transcript.pk}"
        )
        mock_service.ingest_video.assert_called_once()

    @patch("rag.management.commands.rag_ingest.IngestionService")
    def test_handles_ingestion_errors_gracefully(
        self, mock_service_class, video_with_transcript
    ):
        """Test that ingestion errors are caught and reported."""
        # Setup mock to raise error
        mock_service = Mock()
        mock_service.ingest_video.side_effect = ValueError("Test error")
        mock_service_class.return_value = mock_service

        # Run command - should not raise
        out = StringIO()
        err = StringIO()
        call_command(
            "rag_ingest",
            "--video-id",
            str(video_with_transcript.id),
            stdout=out,
            stderr=err,
        )

        # Verify error handling
        output = out.getvalue()
        error_output = err.getvalue()
        assert "Errors: 1" in output
        assert "Error:" in error_output

    def test_no_videos_to_process(self, source):
        """Test handling when no videos match filters."""
        out = StringIO()
        call_command("rag_ingest", "--all", stdout=out)

        output = out.getvalue()
        assert "Found 0 videos to process" in output
        assert "No videos to process" in output

    @patch("rag.management.commands.rag_ingest.IngestionService")
    @patch("rag.management.commands.rag_ingest.PgVectorStore")
    def test_skips_already_ingested_videos(
        self, mock_store_class, mock_service_class, video_with_transcript
    ):
        """Test that already-ingested videos are skipped unless reingest is set."""
        # Setup mocks
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock vector store to return existing chunks
        mock_store = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [5]  # 5 existing chunks

        # Setup context manager properly
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=mock_cursor)
        cursor_context.__exit__ = Mock(return_value=False)
        mock_conn.cursor = Mock(return_value=cursor_context)

        conn_context = Mock()
        conn_context.__enter__ = Mock(return_value=mock_conn)
        conn_context.__exit__ = Mock(return_value=False)
        mock_store._get_connection = Mock(return_value=conn_context)
        mock_store.table_name = "rag_embeddings"
        mock_store_class.return_value = mock_store

        # Run command without reingest
        out = StringIO()
        call_command(
            "rag_ingest",
            "--video-id",
            str(video_with_transcript.id),
            stdout=out,
        )

        # Verify
        output = out.getvalue()
        assert "Skipped" in output
        assert "already ingested" in output
        # Should not call ingest_video for already-ingested videos
        mock_service.ingest_video.assert_not_called()

    @patch("rag.management.commands.rag_ingest.IngestionService")
    def test_displays_progress_information(
        self, mock_service_class, video_with_transcript
    ):
        """Test that command displays progress and summary information."""
        # Setup mock
        mock_service = Mock()
        mock_service.ingest_video.return_value = 10
        mock_service_class.return_value = mock_service

        # Run command
        out = StringIO()
        call_command(
            "rag_ingest",
            "--video-id",
            str(video_with_transcript.id),
            stdout=out,
        )

        # Verify output contains expected information
        output = out.getvalue()
        assert "Processing:" in output
        assert video_with_transcript.title in output
        assert str(video_with_transcript.id) in output
        assert video_with_transcript.youtube_video_id in output
        assert "Successfully ingested: 1" in output
        assert "Total chunks indexed: 10" in output
