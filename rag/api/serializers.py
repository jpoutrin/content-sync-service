"""DRF serializers for RAG search API."""

from rest_framework import serializers


class SearchQuerySerializer(serializers.Serializer):
    """
    Serializer for search query parameters.

    Validates and normalizes query parameters from the API request.

    Query Parameters:
        q: Search query text (required, 1-500 chars)
        top_k: Maximum number of results (1-100, default 5)
        min_score: Minimum similarity score threshold (0.0-1.0, default 0.0)
    """

    q = serializers.CharField(
        required=True,
        min_length=1,
        max_length=500,
        help_text="Search query text (natural language)"
    )
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=100,
        help_text="Maximum number of results to return"
    )
    min_score = serializers.FloatField(
        required=False,
        default=0.0,
        min_value=0.0,
        max_value=1.0,
        help_text="Minimum similarity score threshold (0.0-1.0)"
    )


class SearchResultItemSerializer(serializers.Serializer):
    """
    Serializer for a single search result item.

    Represents a matched transcript chunk with video metadata
    and timestamp information for direct navigation.
    """

    chunk_id = serializers.CharField(
        help_text="Unique chunk identifier (format: video:{pk}:chunk:{index})"
    )
    content = serializers.CharField(
        help_text="The text content of the transcript chunk"
    )
    score = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        help_text="Similarity score (0.0-1.0, higher is better)"
    )
    video_id = serializers.CharField(
        help_text="Video primary key as string"
    )
    video_title = serializers.CharField(
        help_text="Title of the source video"
    )
    video_url = serializers.URLField(
        help_text="URL to the video page"
    )
    start_time = serializers.FloatField(
        min_value=0.0,
        help_text="Chunk start timestamp in seconds"
    )
    end_time = serializers.FloatField(
        min_value=0.0,
        help_text="Chunk end timestamp in seconds"
    )
    timestamp_url = serializers.URLField(
        help_text="Direct URL to video at start timestamp"
    )


class SearchResponseSerializer(serializers.Serializer):
    """
    Serializer for complete search response.

    Contains the original query and list of matching results.
    """

    query = serializers.CharField(
        help_text="The original search query"
    )
    results = SearchResultItemSerializer(
        many=True,
        help_text="List of matching transcript chunks, sorted by score descending"
    )
    total = serializers.IntegerField(
        min_value=0,
        help_text="Total number of results returned"
    )
