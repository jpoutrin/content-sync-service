"""
Tests for yt_sync models.

These tests verify the basic functionality and constraints
of the User, Source, Video, and ProcessedContent models.
"""
import pytest
from django.db import IntegrityError

from yt_sync.models import ProcessedContent, Source, User, Video

from .factories import (
    ProcessedContentFactory,
    SourceFactory,
    UserFactory,
    VideoFactory,
)


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self):
        """Test that a user can be created with valid data."""
        user = UserFactory()
        assert user.pk is not None
        assert user.email is not None
        assert user.is_active is True

    def test_user_str(self):
        """Test the string representation of a user."""
        user = UserFactory(username="testuser")
        assert str(user) == "testuser"


class TestSourceModel:
    """Tests for the Source model."""

    def test_create_source(self):
        """Test that a source can be created with valid data."""
        source = SourceFactory()
        assert source.pk is not None
        assert source.user is not None
        assert source.youtube_id is not None

    def test_source_str(self):
        """Test the string representation of a source."""
        source = SourceFactory(title="My Channel", type=Source.SourceType.CHANNEL)
        assert "My Channel" in str(source)
        assert "CHANNEL" in str(source)

    def test_source_types(self):
        """Test that source types are valid."""
        channel = SourceFactory(type=Source.SourceType.CHANNEL)
        playlist = SourceFactory(type=Source.SourceType.PLAYLIST)
        assert channel.type == "CHANNEL"
        assert playlist.type == "PLAYLIST"

    def test_source_status(self):
        """Test that source status can be changed."""
        source = SourceFactory(status=Source.Status.ACTIVE)
        assert source.status == "ACTIVE"

        source.status = Source.Status.ERROR
        source.save()
        source.refresh_from_db()
        assert source.status == "ERROR"

    def test_unique_together_constraint(self):
        """Test that a user cannot have duplicate youtube_ids."""
        user = UserFactory()
        SourceFactory(user=user, youtube_id="UC123")

        with pytest.raises(IntegrityError):
            SourceFactory(user=user, youtube_id="UC123")


class TestVideoModel:
    """Tests for the Video model."""

    def test_create_video(self):
        """Test that a video can be created with valid data."""
        video = VideoFactory()
        assert video.pk is not None
        assert video.source is not None
        assert video.youtube_video_id is not None

    def test_video_str(self):
        """Test the string representation of a video."""
        video = VideoFactory(title="Test Video Title")
        assert str(video) == "Test Video Title"

    def test_video_processing_status(self):
        """Test video processing status transitions."""
        video = VideoFactory(transcript_status=Video.ProcessingStatus.PENDING)
        assert video.transcript_status == "PENDING"

        video.transcript_status = Video.ProcessingStatus.PROCESSING
        video.save()
        video.refresh_from_db()
        assert video.transcript_status == "PROCESSING"

        video.transcript_status = Video.ProcessingStatus.COMPLETED
        video.save()
        video.refresh_from_db()
        assert video.transcript_status == "COMPLETED"

    def test_unique_youtube_video_id(self):
        """Test that youtube_video_id must be unique."""
        VideoFactory(youtube_video_id="vid_unique123")

        with pytest.raises(IntegrityError):
            VideoFactory(youtube_video_id="vid_unique123")


class TestProcessedContentModel:
    """Tests for the ProcessedContent model."""

    def test_create_processed_content(self):
        """Test that processed content can be created."""
        content = ProcessedContentFactory()
        assert content.pk is not None
        assert content.video is not None
        assert content.summary is not None

    def test_processed_content_str(self):
        """Test the string representation of processed content."""
        video = VideoFactory(title="Video Title")
        content = ProcessedContentFactory(video=video)
        assert "Video Title" in str(content)

    def test_json_fields(self):
        """Test that JSON fields store data correctly."""
        content = ProcessedContentFactory(
            tags=["python", "django"],
            categories=["Programming"],
            main_ideas=["Idea 1", "Idea 2"],
        )

        content.refresh_from_db()
        assert content.tags == ["python", "django"]
        assert content.categories == ["Programming"]
        assert content.main_ideas == ["Idea 1", "Idea 2"]

    def test_one_to_one_relationship(self):
        """Test that video can only have one processed content."""
        video = VideoFactory()
        ProcessedContentFactory(video=video)

        with pytest.raises(IntegrityError):
            ProcessedContentFactory(video=video)
