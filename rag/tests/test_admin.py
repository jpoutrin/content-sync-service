"""Tests for RAG admin integration."""

from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.http import HttpRequest

import pytest

from yt_sync.admin import VideoAdmin
from yt_sync.models import Source, Video

User = get_user_model()


@pytest.mark.django_db
class TestVideoAdmin:
    """Test suite for VideoAdmin."""

    @pytest.fixture
    def admin_user(self):
        """Create a staff user for admin tests."""
        return User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass",
            is_staff=True,
            is_superuser=True,
        )

    @pytest.fixture
    def regular_user(self):
        """Create a regular user for testing ACL."""
        return User.objects.create_user(
            username="user123",
            email="user@example.com",
            password="testpass",
        )

    @pytest.fixture
    def source(self, regular_user):
        """Create a video source."""
        return Source.objects.create(
            user=regular_user,
            type=Source.SourceType.CHANNEL,
            youtube_id="UC_test_channel",
            title="Test Channel",
            url="https://youtube.com/channel/UC_test_channel",
        )

    @pytest.fixture
    def video_with_transcript(self, source):
        """Create a video with transcript data."""
        return Video.objects.create(
            source=source,
            youtube_video_id="abc123",
            title="Test Video",
            url="https://youtube.com/watch?v=abc123",
            published_at="2024-01-01T00:00:00Z",
            transcript_data=[
                {"text": "Hello world", "start": 0.0, "duration": 2.0},
                {"text": "This is a test", "start": 2.0, "duration": 3.0},
            ],
            transcript_status=Video.ProcessingStatus.COMPLETED,
        )

    @pytest.fixture
    def video_without_transcript(self, source):
        """Create a video without transcript data."""
        return Video.objects.create(
            source=source,
            youtube_video_id="xyz789",
            title="No Transcript Video",
            url="https://youtube.com/watch?v=xyz789",
            published_at="2024-01-01T00:00:00Z",
            transcript_data=[],
            transcript_status=Video.ProcessingStatus.PENDING,
        )

    @pytest.fixture
    def video_admin(self):
        """Create a VideoAdmin instance."""
        site = AdminSite()
        return VideoAdmin(Video, site)

    @pytest.fixture
    def mock_request(self, admin_user):
        """Create a mock HTTP request with admin user."""
        request = HttpRequest()
        request.user = admin_user
        request.META = {}
        request._messages = Mock()
        return request

    def test_admin_registration(self):
        """Test that VideoAdmin is properly registered."""
        site = AdminSite()
        admin_instance = VideoAdmin(Video, site)
        assert admin_instance.model == Video

    def test_list_display_fields(self, video_admin):
        """Test that list_display contains expected fields."""
        expected_fields = (
            "title",
            "youtube_video_id",
            "source",
            "transcript_status",
            "ai_analysis_status",
            "published_at",
        )
        assert video_admin.list_display == expected_fields

    def test_list_filter_fields(self, video_admin):
        """Test that list_filter contains expected fields."""
        expected_filters = (
            "transcript_status",
            "ai_analysis_status",
            "published_at",
        )
        assert video_admin.list_filter == expected_filters

    def test_search_fields(self, video_admin):
        """Test that search_fields contains expected fields."""
        expected_fields = ("title", "youtube_video_id")
        assert video_admin.search_fields == expected_fields

    def test_actions_registered(self, video_admin):
        """Test that custom actions are registered."""
        assert "ingest_selected_videos" in video_admin.actions

    @patch("yt_sync.admin.IngestionService")
    def test_ingest_action_success(
        self,
        mock_ingestion_service,
        video_admin,
        mock_request,
        video_with_transcript,
    ):
        """Test successful ingestion of videos."""
        # Setup mock
        mock_service_instance = Mock()
        mock_service_instance.ingest_video.return_value = 5
        mock_ingestion_service.return_value = mock_service_instance

        # Create queryset
        queryset = Video.objects.filter(pk=video_with_transcript.pk)

        # Execute action
        with patch("yt_sync.admin.messages") as mock_messages:
            video_admin.ingest_selected_videos(mock_request, queryset)

            # Verify success message
            mock_messages.SUCCESS = 25  # Django messages.SUCCESS constant
            success_calls = [
                call
                for call in mock_messages.method_calls
                if "Successfully ingested" in str(call)
            ]
            assert len(success_calls) > 0

        # Verify service was called
        mock_service_instance.ingest_video.assert_called_once_with(
            video_with_transcript
        )

    def test_ingest_action_no_transcripts(
        self, video_admin, mock_request, video_without_transcript
    ):
        """Test ingestion action with no transcripts."""
        queryset = Video.objects.filter(pk=video_without_transcript.pk)

        with patch("yt_sync.admin.messages") as mock_messages:
            video_admin.ingest_selected_videos(mock_request, queryset)

            # Verify warning message was shown
            mock_messages.WARNING = 30  # Django messages.WARNING constant
            warning_calls = [
                call
                for call in mock_messages.method_calls
                if "No videos with transcript data" in str(call)
            ]
            assert len(warning_calls) > 0

    @patch("yt_sync.admin.IngestionService")
    def test_ingest_action_partial_failure(
        self,
        mock_ingestion_service,
        video_admin,
        mock_request,
        video_with_transcript,
        source,
    ):
        """Test ingestion action with partial failures."""
        # Create second video
        video2 = Video.objects.create(
            source=source,
            youtube_video_id="def456",
            title="Second Video",
            url="https://youtube.com/watch?v=def456",
            published_at="2024-01-01T00:00:00Z",
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
            transcript_status=Video.ProcessingStatus.COMPLETED,
        )

        # Setup mock to succeed for first, fail for second
        mock_service_instance = Mock()
        mock_service_instance.ingest_video.side_effect = [
            5,  # Success for first video
            RuntimeError("Embedding failed"),  # Failure for second
        ]
        mock_ingestion_service.return_value = mock_service_instance

        queryset = Video.objects.filter(pk__in=[video_with_transcript.pk, video2.pk])

        with patch("yt_sync.admin.messages") as mock_messages:
            video_admin.ingest_selected_videos(mock_request, queryset)

            # Should have both success and error messages
            mock_messages.SUCCESS = 25
            mock_messages.ERROR = 40
            mock_messages.WARNING = 30

            # Check for success message
            success_calls = [
                call
                for call in mock_messages.method_calls
                if "Successfully ingested 1 video" in str(call)
            ]
            assert len(success_calls) > 0

            # Check for failure message
            error_calls = [
                call
                for call in mock_messages.method_calls
                if "Failed to ingest" in str(call)
            ]
            assert len(error_calls) > 0

    @patch("yt_sync.admin.DefaultRetriever")
    @patch("yt_sync.admin.PgVectorStore")
    @patch("yt_sync.admin.LiteLLMEmbedder")
    def test_perform_rag_search(
        self,
        mock_embedder_class,
        mock_store_class,
        mock_retriever_class,
        video_admin,
    ):
        """Test RAG search functionality."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder_class.return_value = mock_embedder

        mock_store = Mock()
        mock_store_class.return_value = mock_store

        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever

        # Create mock search result
        mock_chunk = Mock()
        mock_chunk.id = "video:42:chunk:5"
        mock_chunk.content = "Test content"

        mock_result = Mock()
        mock_result.chunk = mock_chunk
        mock_result.score = 0.89
        mock_result.document_metadata = {
            "video_title": "Test Video",
            "video_url": "https://youtube.com/watch?v=abc123",
            "start_time": 125.5,
            "end_time": 185.2,
            "youtube_video_id": "abc123",
        }

        mock_retriever.retrieve.return_value = [mock_result]

        # Execute search
        results = video_admin._perform_rag_search("test query")

        # Verify retriever was initialized and called
        mock_retriever.retrieve.assert_called_once()

        # Verify results format
        assert len(results) == 1
        result = results[0]
        assert result["chunk_id"] == "video:42:chunk:5"
        assert result["content"] == "Test content"
        assert result["score"] == 0.89
        assert result["video_id"] == "42"
        assert result["video_title"] == "Test Video"
        assert "timestamp_url" in result
        assert result["formatted_timestamp"] == "02:05"

    def test_format_timestamp_minutes_seconds(self, video_admin):
        """Test timestamp formatting for MM:SS format."""
        assert video_admin._format_timestamp(125.5) == "02:05"
        assert video_admin._format_timestamp(0.0) == "00:00"
        assert video_admin._format_timestamp(59.9) == "00:59"

    def test_format_timestamp_hours(self, video_admin):
        """Test timestamp formatting for HH:MM:SS format."""
        assert video_admin._format_timestamp(3661.0) == "01:01:01"
        assert video_admin._format_timestamp(7200.0) == "02:00:00"

    @patch("yt_sync.admin.DefaultRetriever")
    @patch("yt_sync.admin.PgVectorStore")
    @patch("yt_sync.admin.LiteLLMEmbedder")
    def test_changelist_view_with_rag_search(
        self,
        mock_embedder_class,
        mock_store_class,
        mock_retriever_class,
        video_admin,
        mock_request,
    ):
        """Test changelist view with RAG search query."""
        # Setup mocks for search
        mock_embedder = Mock()
        mock_embedder_class.return_value = mock_embedder

        mock_store = Mock()
        mock_store_class.return_value = mock_store

        mock_retriever = Mock()
        mock_retriever_class.return_value = mock_retriever

        mock_chunk = Mock()
        mock_chunk.id = "video:1:chunk:0"
        mock_chunk.content = "Search result"

        mock_result = Mock()
        mock_result.chunk = mock_chunk
        mock_result.score = 0.95
        mock_result.document_metadata = {
            "video_title": "Result Video",
            "video_url": "https://youtube.com/watch?v=test",
            "start_time": 10.0,
            "end_time": 20.0,
            "youtube_video_id": "test",
        }

        mock_retriever.retrieve.return_value = [mock_result]

        # Add RAG search to request
        mock_request.GET = {"rag_search": "test query"}

        # Mock the parent changelist_view
        with patch.object(VideoAdmin.__bases__[0], "changelist_view") as mock_super:
            mock_super.return_value = Mock()

            # Call changelist_view
            video_admin.changelist_view(mock_request)

            # Verify super was called with search results in context
            call_args = mock_super.call_args
            extra_context = call_args[1].get("extra_context", {})

            assert "rag_search_query" in extra_context
            assert extra_context["rag_search_query"] == "test query"
            assert "rag_search_results" in extra_context
            assert len(extra_context["rag_search_results"]) == 1
