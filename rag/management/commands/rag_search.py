"""Django management command for semantic search over indexed transcripts."""

import json
from argparse import ArgumentParser

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rag.core.acl import QueryACLContext
from rag.core.schemas import SearchQuery
from rag.embedders.litellm import LiteLLMEmbedder
from rag.retrievers.default import DefaultRetriever
from rag.stores.pgvector import PgVectorStore
from yt_sync.models import User


class Command(BaseCommand):
    """
    Django management command for semantic search over indexed video transcripts.

    This command provides a CLI interface to the RAG semantic search system,
    allowing users to search indexed video transcripts from the command line.

    Usage:
        python manage.py rag_search "your query text"
        python manage.py rag_search "django settings" --top-k 10 --min-score 0.7
        python manage.py rag_search "API design" --user user123
        python manage.py rag_search "testing" --bypass-acl

    The command initializes the embedder, vector store, and retriever using
    the configuration from Django settings, then executes the search and
    displays formatted results.
    """

    help = "Perform semantic search over indexed video transcripts"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command-line arguments.

        Args:
            parser: Django's argument parser
        """
        # Required positional argument
        parser.add_argument(
            "query",
            type=str,
            help="Search query text (natural language)",
        )

        # Optional arguments
        parser.add_argument(
            "--top-k",
            type=int,
            default=5,
            help="Maximum number of results to return (default: 5, max: 100)",
        )

        parser.add_argument(
            "--min-score",
            type=float,
            default=None,
            help="Minimum similarity score threshold (0.0-1.0)",
        )

        parser.add_argument(
            "--user",
            type=str,
            default=None,
            help="User ID to set ACL context (uses first user if not specified)",
        )

        parser.add_argument(
            "--bypass-acl",
            action="store_true",
            help="Bypass ACL filtering (staff/system access only)",
        )

        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results as JSON instead of pretty-printed format",
        )

    def handle(self, *args, **options) -> None:
        """Execute the search command.

        Args:
            *args: Positional arguments (unused)
            **options: Command-line options dict

        Raises:
            CommandError: If validation fails or search encounters an error
        """
        # Extract and validate arguments
        query_text = options["query"]
        top_k = options["top_k"]
        min_score = options["min_score"]
        user_id = options["user"]
        bypass_acl = options["bypass_acl"]
        json_output = options["json"]

        # Validate arguments
        if not query_text.strip():
            raise CommandError("Query text cannot be empty")

        if top_k < 1 or top_k > 100:
            raise CommandError("--top-k must be between 1 and 100")

        if min_score is not None and not (0.0 <= min_score <= 1.0):
            raise CommandError("--min-score must be between 0.0 and 1.0")

        # Build ACL context
        try:
            acl_context = self._build_acl_context(user_id, bypass_acl, json_output)
        except Exception as e:
            raise CommandError(f"Failed to build ACL context: {e}") from e

        # Initialize components
        try:
            embedder = self._get_embedder()
            store = self._get_vector_store()
            retriever = DefaultRetriever(embedder, store)
        except Exception as e:
            raise CommandError(f"Failed to initialize search components: {e}") from e

        # Build search query
        search_query = SearchQuery(
            text=query_text,
            top_k=top_k,
            min_score=min_score,
            acl_context=acl_context,
        )

        # Execute search
        if not json_output:
            self.stdout.write(self.style.MIGRATE_HEADING("Searching..."))

        try:
            results = retriever.retrieve(search_query)
        except Exception as e:
            raise CommandError(f"Search failed: {e}") from e

        # Display results
        if json_output:
            self._output_json(query_text, results)
        else:
            self._output_pretty(query_text, results)

    def _build_acl_context(
        self, user_id: str | None, bypass_acl: bool, json_output: bool = False
    ) -> QueryACLContext:
        """Build ACL context for the search query.

        Args:
            user_id: User ID string or None
            bypass_acl: Whether to bypass ACL filtering
            json_output: Whether output will be JSON (suppresses informational messages)

        Returns:
            QueryACLContext for the search

        Raises:
            CommandError: If user_id is invalid or no users exist
        """
        if bypass_acl:
            if not json_output:
                self.stdout.write(
                    self.style.WARNING("⚠️  Bypassing ACL filtering (system access)")
                )
            return QueryACLContext.system_context()

        # Get user for ACL context
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except (User.DoesNotExist, ValueError, Exception) as e:
                # Catch ValueError for invalid UUID format, DoesNotExist for user not found
                # and any other exceptions that might occur during lookup
                raise CommandError(f"User with ID '{user_id}' not found") from e
        else:
            # Use first user if not specified
            user_or_none = User.objects.first()
            if not user_or_none:
                raise CommandError(
                    "No users found in database. Create a user first or use --bypass-acl"
                )
            user = user_or_none

        principal_id = str(user.id)

        # Build ACL context
        # Note: For now, we don't populate member_of_groups or tenant_id
        # In a real application, these would come from user profile/groups
        acl_context = QueryACLContext(
            principal_id=principal_id,
            member_of_groups=[],
            tenant_id=None,
            bypass_acl=False,
        )

        if not json_output:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Using ACL context for user: {user.email or principal_id}"
                )
            )

        return acl_context

    def _get_embedder(self) -> LiteLLMEmbedder:
        """Initialize embedder from Django settings.

        Returns:
            Configured LiteLLMEmbedder instance

        Raises:
            CommandError: If embedder configuration is invalid
        """
        from typing import cast, Literal

        provider_raw = getattr(settings, "RAG_EMBEDDING_PROVIDER", "local")
        provider = cast(Literal["local", "openai"], provider_raw)
        model = getattr(settings, "RAG_EMBEDDING_MODEL", None)
        batch_size = getattr(settings, "RAG_EMBEDDING_BATCH_SIZE", 50)

        try:
            embedder = LiteLLMEmbedder(
                provider=provider,
                model=model,
                batch_size=batch_size,
            )
            return embedder
        except Exception as e:
            raise CommandError(f"Failed to initialize embedder: {e}") from e

    def _get_vector_store(self) -> PgVectorStore:
        """Initialize vector store from Django settings.

        Returns:
            Configured PgVectorStore instance

        Raises:
            CommandError: If vector store initialization fails
        """
        # Get database connection string from Django settings
        db_config = settings.DATABASES["default"]
        connection_string = (
            f"postgresql://{db_config['USER']}:{db_config['PASSWORD']}"
            f"@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        )

        try:
            store = PgVectorStore(connection_string=connection_string)
            return store
        except Exception as e:
            raise CommandError(f"Failed to initialize vector store: {e}") from e

    def _output_json(self, query: str, results: list) -> None:
        """Output results as JSON.

        Args:
            query: Original query text
            results: List of SearchResult objects
        """
        output = {
            "query": query,
            "results": [
                {
                    "chunk_id": r.chunk.id,
                    "content": r.chunk.content,
                    "score": r.score,
                    "metadata": r.chunk.metadata,
                    "document_metadata": r.document_metadata,
                }
                for r in results
            ],
            "total": len(results),
        }

        self.stdout.write(json.dumps(output, indent=2))

    def _output_pretty(self, query: str, results: list) -> None:
        """Output results in a human-readable format with colors.

        Args:
            query: Original query text
            results: List of SearchResult objects
        """
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"Query: {query}"))
        self.stdout.write(self.style.MIGRATE_HEADING(f"Results: {len(results)}"))
        self.stdout.write("")

        if not results:
            self.stdout.write(self.style.WARNING("No results found."))
            return

        for i, result in enumerate(results, 1):
            # Header with score
            header = f"[{i}] Score: {result.score:.3f}"
            self.stdout.write(self.style.SUCCESS(header))

            # Chunk ID
            self.stdout.write(f"  Chunk ID: {result.chunk.id}")

            # Content (truncated if too long)
            content = result.chunk.content
            if len(content) > 300:
                content = content[:297] + "..."
            self.stdout.write(f"  Content: {content}")

            # Metadata
            metadata = result.chunk.metadata
            if "video_title" in metadata:
                self.stdout.write(
                    self.style.HTTP_INFO(f"  Video: {metadata['video_title']}")
                )

            if "start_time" in metadata and "end_time" in metadata:
                start = metadata["start_time"]
                end = metadata["end_time"]
                self.stdout.write(f"  Timestamp: {start:.1f}s - {end:.1f}s")

            # Timestamp URL if available
            enriched = result.document_metadata
            if "timestamp_url" in enriched:
                self.stdout.write(
                    self.style.HTTP_INFO(f"  URL: {enriched['timestamp_url']}")
                )

            self.stdout.write("")
