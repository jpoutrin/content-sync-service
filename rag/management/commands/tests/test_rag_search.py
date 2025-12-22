"""Tests for rag_search management command."""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError

import pytest

from rag.core.acl import QueryACLContext, Visibility
from rag.core.schemas import Chunk, SearchResult
from yt_sync.models import User


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create(
        email="test@example.com",
        username="testuser",
    )


@pytest.fixture
def mock_retriever():
    """Create a mock retriever with sample results."""
    # Create sample chunks and results
    chunk1 = Chunk(
        id="video:1:chunk:0",
        document_id="video:1",
        content="Django settings configuration best practices",
        index=0,
        metadata={
            "start_time": 125.5,
            "end_time": 185.2,
            "video_title": "Django Tutorial",
            "video_url": "https://youtube.com/watch?v=abc123",
            "youtube_video_id": "abc123",
        },
        owner_id="user-123",
        visibility=Visibility.PRIVATE,
    )

    chunk2 = Chunk(
        id="video:1:chunk:5",
        document_id="video:1",
        content="Environment variables for Django configuration",
        index=5,
        metadata={
            "start_time": 420.0,
            "end_time": 465.8,
            "video_title": "Django Tutorial",
            "video_url": "https://youtube.com/watch?v=abc123",
            "youtube_video_id": "abc123",
        },
        owner_id="user-123",
        visibility=Visibility.PRIVATE,
    )

    result1 = SearchResult(
        chunk=chunk1,
        score=0.89,
        document_metadata={"timestamp_url": "https://youtube.com/watch?v=abc123&t=125"},
    )

    result2 = SearchResult(
        chunk=chunk2,
        score=0.82,
        document_metadata={"timestamp_url": "https://youtube.com/watch?v=abc123&t=420"},
    )

    mock = MagicMock()
    mock.retrieve.return_value = [result1, result2]
    return mock


@pytest.mark.django_db
class TestRagSearchCommand:
    """Tests for the rag_search management command."""

    def test_command_requires_query_argument(self):
        """Test that command fails without query argument."""
        with pytest.raises(CommandError, match="the following arguments are required"):
            call_command("rag_search")

    def test_command_rejects_empty_query(self, test_user):
        """Test that command rejects empty query text."""
        with pytest.raises(CommandError, match="Query text cannot be empty"):
            call_command("rag_search", "")

    def test_command_validates_top_k_range(self, test_user):
        """Test that command validates top_k parameter range."""
        with pytest.raises(CommandError, match="--top-k must be between 1 and 100"):
            call_command("rag_search", "test query", top_k=0)

        with pytest.raises(CommandError, match="--top-k must be between 1 and 100"):
            call_command("rag_search", "test query", top_k=101)

    def test_command_validates_min_score_range(self, test_user):
        """Test that command validates min_score parameter range."""
        with pytest.raises(
            CommandError, match="--min-score must be between 0.0 and 1.0"
        ):
            call_command("rag_search", "test query", min_score=-0.1)

        with pytest.raises(
            CommandError, match="--min-score must be between 0.0 and 1.0"
        ):
            call_command("rag_search", "test query", min_score=1.1)

    def test_command_fails_without_users_and_no_bypass(self, db):
        """Test that command fails when no users exist and bypass_acl is not set."""
        # Ensure no users exist
        User.objects.all().delete()

        with pytest.raises(
            CommandError,
            match="No users found in database. Create a user first or use --bypass-acl",
        ):
            call_command("rag_search", "test query")

    def test_command_fails_with_invalid_user_id(self, test_user):
        """Test that command fails with invalid user ID."""
        with pytest.raises(CommandError, match="User with ID .* not found"):
            call_command("rag_search", "test query", user="nonexistent-user-id")

    @patch("rag.management.commands.rag_search.DefaultRetriever")
    @patch("rag.management.commands.rag_search.PgVectorStore")
    @patch("rag.management.commands.rag_search.LiteLLMEmbedder")
    def test_command_executes_search_with_default_options(
        self, mock_embedder_class, mock_store_class, mock_retriever_class, test_user
    ):
        """Test that command executes search with default options."""
        # Setup mocks
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_retriever_class.return_value = mock_retriever

        out = StringIO()
        call_command("rag_search", "django settings", stdout=out)

        # Verify retriever.retrieve was called
        assert mock_retriever.retrieve.called
        call_args = mock_retriever.retrieve.call_args[0][0]

        # Verify SearchQuery parameters
        assert call_args.text == "django settings"
        assert call_args.top_k == 5  # default
        assert call_args.min_score is None  # default
        assert isinstance(call_args.acl_context, QueryACLContext)
        assert call_args.acl_context.principal_id == str(test_user.id)
        assert call_args.acl_context.bypass_acl is False

    @patch("rag.management.commands.rag_search.DefaultRetriever")
    @patch("rag.management.commands.rag_search.PgVectorStore")
    @patch("rag.management.commands.rag_search.LiteLLMEmbedder")
    def test_command_executes_search_with_custom_options(
        self, mock_embedder_class, mock_store_class, mock_retriever_class, test_user
    ):
        """Test that command executes search with custom options."""
        # Setup mocks
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_retriever_class.return_value = mock_retriever

        out = StringIO()
        call_command(
            "rag_search",
            "API design patterns",
            top_k=10,
            min_score=0.7,
            user=str(test_user.id),
            stdout=out,
        )

        # Verify retriever.retrieve was called
        assert mock_retriever.retrieve.called
        call_args = mock_retriever.retrieve.call_args[0][0]

        # Verify SearchQuery parameters
        assert call_args.text == "API design patterns"
        assert call_args.top_k == 10
        assert call_args.min_score == 0.7
        assert call_args.acl_context.principal_id == str(test_user.id)

    @patch("rag.management.commands.rag_search.DefaultRetriever")
    @patch("rag.management.commands.rag_search.PgVectorStore")
    @patch("rag.management.commands.rag_search.LiteLLMEmbedder")
    def test_command_with_bypass_acl(
        self, mock_embedder_class, mock_store_class, mock_retriever_class
    ):
        """Test that command bypasses ACL when --bypass-acl is set."""
        # Setup mocks
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_retriever_class.return_value = mock_retriever

        out = StringIO()
        call_command("rag_search", "system query", bypass_acl=True, stdout=out)

        # Verify retriever.retrieve was called
        assert mock_retriever.retrieve.called
        call_args = mock_retriever.retrieve.call_args[0][0]

        # Verify ACL bypass
        assert call_args.acl_context.bypass_acl is True
        assert call_args.acl_context.principal_id == "system"

        # Verify warning in output
        output = out.getvalue()
        assert "Bypassing ACL filtering" in output

    @patch("rag.management.commands.rag_search.DefaultRetriever")
    @patch("rag.management.commands.rag_search.PgVectorStore")
    @patch("rag.management.commands.rag_search.LiteLLMEmbedder")
    def test_command_pretty_output(
        self,
        mock_embedder_class,
        mock_store_class,
        mock_retriever_class,
        test_user,
        mock_retriever,
    ):
        """Test that command outputs pretty-printed results."""
        # Setup mocks
        mock_retriever_class.return_value = mock_retriever

        out = StringIO()
        call_command("rag_search", "django settings", stdout=out)

        output = out.getvalue()

        # Verify output contains key information
        assert "Query: django settings" in output
        assert "Results: 2" in output
        assert "Score: 0.89" in output
        assert "Django settings configuration best practices" in output
        assert "Django Tutorial" in output
        assert "125.5s - 185.2s" in output
        assert "https://youtube.com/watch?v=abc123&t=125" in output

    @patch("rag.management.commands.rag_search.DefaultRetriever")
    @patch("rag.management.commands.rag_search.PgVectorStore")
    @patch("rag.management.commands.rag_search.LiteLLMEmbedder")
    def test_command_json_output(
        self,
        mock_embedder_class,
        mock_store_class,
        mock_retriever_class,
        test_user,
        mock_retriever,
    ):
        """Test that command outputs JSON when --json flag is set."""
        # Setup mocks
        mock_retriever_class.return_value = mock_retriever

        out = StringIO()
        call_command("rag_search", "django settings", json=True, stdout=out)

        output = out.getvalue()

        # Verify output is valid JSON
        data = json.loads(output)

        assert data["query"] == "django settings"
        assert data["total"] == 2
        assert len(data["results"]) == 2

        # Verify first result structure
        result1 = data["results"][0]
        assert result1["chunk_id"] == "video:1:chunk:0"
        assert result1["score"] == 0.89
        assert "Django settings" in result1["content"]
        assert result1["metadata"]["video_title"] == "Django Tutorial"

    @patch("rag.management.commands.rag_search.DefaultRetriever")
    @patch("rag.management.commands.rag_search.PgVectorStore")
    @patch("rag.management.commands.rag_search.LiteLLMEmbedder")
    def test_command_no_results(
        self, mock_embedder_class, mock_store_class, mock_retriever_class, test_user
    ):
        """Test that command handles empty results gracefully."""
        # Setup mocks to return no results
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_retriever_class.return_value = mock_retriever

        out = StringIO()
        call_command("rag_search", "nonexistent query", stdout=out)

        output = out.getvalue()

        # Verify output shows no results
        assert "Results: 0" in output
        assert "No results found" in output

    @patch("rag.management.commands.rag_search.DefaultRetriever")
    @patch("rag.management.commands.rag_search.PgVectorStore")
    @patch("rag.management.commands.rag_search.LiteLLMEmbedder")
    def test_command_handles_search_error(
        self, mock_embedder_class, mock_store_class, mock_retriever_class, test_user
    ):
        """Test that command handles search errors gracefully."""
        # Setup mocks to raise an error
        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = RuntimeError("Vector store error")
        mock_retriever_class.return_value = mock_retriever

        with pytest.raises(CommandError, match="Search failed: Vector store error"):
            call_command("rag_search", "test query")

    @patch("rag.management.commands.rag_search.DefaultRetriever")
    @patch("rag.management.commands.rag_search.PgVectorStore")
    @patch("rag.management.commands.rag_search.LiteLLMEmbedder")
    def test_command_truncates_long_content(
        self,
        mock_embedder_class,
        mock_store_class,
        mock_retriever_class,
        test_user,
    ):
        """Test that command truncates long content in pretty output."""
        # Create a chunk with very long content
        long_content = "A" * 400
        chunk = Chunk(
            id="video:1:chunk:0",
            document_id="video:1",
            content=long_content,
            index=0,
            metadata={},
            owner_id="user-123",
            visibility=Visibility.PRIVATE,
        )

        result = SearchResult(chunk=chunk, score=0.95, document_metadata={})

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [result]
        mock_retriever_class.return_value = mock_retriever

        out = StringIO()
        call_command("rag_search", "test", stdout=out)

        output = out.getvalue()

        # Verify content is truncated with ellipsis
        assert "AAA..." in output
        # Full content should not be in output (would be > 300 chars)
        assert long_content not in output
