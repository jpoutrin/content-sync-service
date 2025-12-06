"""
Tests for yt_sync serializers.

These tests verify that serializers correctly serialize
and deserialize model data.
"""
import pytest

from yt_sync.serializers import (
    ProcessedContentSerializer,
    SourceSerializer,
    VideoSerializer,
)

from .factories import (
    ProcessedContentFactory,
    SourceFactory,
    UserFactory,
    VideoFactory,
)


class TestSourceSerializer:
    """Tests for the SourceSerializer."""

    def test_serialize_source(self):
        """Test that a source is correctly serialized."""
        source = SourceFactory()
        serializer = SourceSerializer(source)
        data = serializer.data

        assert data["id"] == str(source.id)
        assert data["youtube_id"] == source.youtube_id
        assert data["title"] == source.title
        assert data["type"] == source.type
        assert data["status"] == source.status

    def test_read_only_fields(self):
        """Test that read-only fields cannot be set on create."""
        user = UserFactory()
        data = {
            "user": user.id,
            "youtube_id": "UC123456",
            "title": "Test Channel",
            "url": "https://youtube.com/channel/UC123456",
            "type": "CHANNEL",
        }
        serializer = SourceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors


class TestVideoSerializer:
    """Tests for the VideoSerializer."""

    def test_serialize_video(self):
        """Test that a video is correctly serialized."""
        video = VideoFactory()
        serializer = VideoSerializer(video)
        data = serializer.data

        assert data["id"] == str(video.id)
        assert data["youtube_video_id"] == video.youtube_video_id
        assert data["title"] == video.title
        assert data["transcript_status"] == video.transcript_status
        assert data["ai_analysis_status"] == video.ai_analysis_status

    def test_serialize_video_with_processed_content(self):
        """Test serialization includes nested processed content."""
        content = ProcessedContentFactory()
        video = content.video
        serializer = VideoSerializer(video)
        data = serializer.data

        assert "processed_content" in data
        assert data["processed_content"]["summary"] == content.summary

    def test_serialize_video_without_processed_content(self):
        """Test serialization when no processed content exists."""
        video = VideoFactory()
        serializer = VideoSerializer(video)
        data = serializer.data

        assert data["processed_content"] is None


class TestProcessedContentSerializer:
    """Tests for the ProcessedContentSerializer."""

    def test_serialize_processed_content(self):
        """Test that processed content is correctly serialized."""
        content = ProcessedContentFactory()
        serializer = ProcessedContentSerializer(content)
        data = serializer.data

        assert data["summary"] == content.summary
        assert data["tags"] == content.tags
        assert data["categories"] == content.categories
        assert data["main_ideas"] == content.main_ideas
        assert data["key_moments"] == content.key_moments
