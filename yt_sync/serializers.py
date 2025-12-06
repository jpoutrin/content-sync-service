from rest_framework import serializers
from .models import Source, Video, ProcessedContent


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for YouTube Source (channel or playlist)."""

    class Meta:
        model = Source
        fields = [
            "id",
            "user",
            "type",
            "youtube_id",
            "title",
            "url",
            "sync_frequency",
            "last_sync_at",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "last_sync_at")


class ProcessedContentSerializer(serializers.ModelSerializer):
    """Serializer for AI-processed video content."""

    class Meta:
        model = ProcessedContent
        fields = [
            "summary",
            "tags",
            "categories",
            "main_ideas",
            "key_moments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")


class VideoSerializer(serializers.ModelSerializer):
    """Serializer for YouTube Video with optional processed content."""

    processed_content = ProcessedContentSerializer(read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "source",
            "youtube_video_id",
            "title",
            "url",
            "duration",
            "published_at",
            "transcript_text",
            "transcript_data",
            "transcript_status",
            "ai_analysis_status",
            "processing_error",
            "created_at",
            "processed_content",
        ]
        read_only_fields = ("id", "created_at", "published_at", "duration")
