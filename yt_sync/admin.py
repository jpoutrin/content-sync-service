from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest

from rag.chunkers.transcript import TranscriptChunker
from rag.core.acl import QueryACLContext
from rag.core.schemas import SearchQuery
from rag.embedders.litellm import LiteLLMEmbedder
from rag.retrievers.default import DefaultRetriever
from rag.services.ingestion import IngestionService
from rag.stores.pgvector import PgVectorStore

from .models import ProcessedContent, Source, User, Video


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "user", "status", "last_sync_at", "created_at")
    list_filter = ("type", "status", "created_at")
    search_fields = ("title", "youtube_id", "user__username")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "youtube_video_id",
        "source",
        "transcript_status",
        "ai_analysis_status",
        "published_at",
    )
    list_filter = ("transcript_status", "ai_analysis_status", "published_at")
    search_fields = ("title", "youtube_video_id")
    readonly_fields = (
        "id",
        "created_at",
        "youtube_video_id",
        "url",
        "duration",
        "transcript_text",
        "transcript_data",
        "processing_error",
    )
    actions = ["ingest_selected_videos"]

    @admin.action(description="Ingest selected videos into RAG vector store")
    def ingest_selected_videos(
        self, request: HttpRequest, queryset: QuerySet[Video]
    ) -> None:
        """
        Admin action to ingest selected videos into the RAG vector store.

        This action processes each selected video's transcript, chunks it,
        generates embeddings, and stores them in the vector database for
        semantic search.

        Args:
            request: Django HTTP request from admin interface
            queryset: QuerySet of selected Video objects

        Note:
            Only processes videos that have transcript data. Videos without
            transcripts are skipped with an info message.
        """
        # Filter to only videos with transcript data
        videos_with_transcript = queryset.filter(transcript_data__isnull=False).exclude(
            transcript_data=[]
        )

        if not videos_with_transcript.exists():
            self.message_user(
                request,
                "No videos with transcript data selected.",
                messages.WARNING,
            )
            return

        # Initialize ingestion service
        try:
            chunker = TranscriptChunker()
            embedder = LiteLLMEmbedder(
                provider=settings.RAG_EMBEDDING_PROVIDER,
                model=settings.RAG_EMBEDDING_MODEL,
            )

            # Build PostgreSQL connection string from Django database settings
            db_settings = settings.DATABASES["default"]
            connection_string = (
                f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}"
                f"@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
            )

            store = PgVectorStore(connection_string=connection_string)
            ingestion_service = IngestionService(chunker, embedder, store)
        except Exception as e:
            self.message_user(
                request,
                f"Failed to initialize ingestion service: {e}",
                messages.ERROR,
            )
            return

        # Process each video
        success_count = 0
        error_count = 0
        total_chunks = 0

        for video in videos_with_transcript:
            try:
                chunk_count = ingestion_service.ingest_video(video)
                total_chunks += chunk_count
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Failed to ingest '{video.title}': {e}",
                    messages.ERROR,
                )

        # Show summary message
        if success_count > 0:
            self.message_user(
                request,
                f"Successfully ingested {success_count} video(s) "
                f"with {total_chunks} total chunks.",
                messages.SUCCESS,
            )

        if error_count > 0:
            self.message_user(
                request,
                f"Failed to ingest {error_count} video(s). See errors above.",
                messages.WARNING,
            )

    def changelist_view(self, request: HttpRequest, extra_context=None):
        """
        Custom changelist view with RAG search interface.

        Adds a search interface that uses semantic search when the 'rag_search'
        query parameter is present. Staff users can search across all indexed
        content using bypass_acl=True.

        Args:
            request: Django HTTP request
            extra_context: Additional context for the template

        Returns:
            HttpResponse: Rendered changelist with optional search results
        """
        extra_context = extra_context or {}

        # Check if RAG search was requested
        rag_query = request.GET.get("rag_search", "").strip()

        if rag_query:
            # Perform RAG search with staff bypass
            try:
                search_results = self._perform_rag_search(rag_query)
                extra_context["rag_search_query"] = rag_query
                extra_context["rag_search_results"] = search_results
            except Exception as e:
                messages.error(request, f"RAG search failed: {e}")

        return super().changelist_view(request, extra_context=extra_context)

    def _perform_rag_search(self, query_text: str) -> list[dict]:
        """
        Perform semantic search across RAG content with ACL bypass.

        This is a staff-only search that bypasses ACL checks to allow
        administrators to search across all indexed content.

        Args:
            query_text: The search query text

        Returns:
            List of search result dictionaries with enriched metadata

        Raises:
            RuntimeError: If search initialization or execution fails
        """
        # Create system context with ACL bypass for staff search
        acl_context = QueryACLContext.system_context()

        # Build search query
        search_query = SearchQuery(
            text=query_text,
            top_k=10,
            min_score=0.5,
            acl_context=acl_context,
        )

        # Initialize retriever
        embedder = LiteLLMEmbedder(
            provider=settings.RAG_EMBEDDING_PROVIDER,
            model=settings.RAG_EMBEDDING_MODEL,
        )

        db_settings = settings.DATABASES["default"]
        connection_string = (
            f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}"
            f"@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        )

        store = PgVectorStore(connection_string=connection_string)
        retriever = DefaultRetriever(embedder=embedder, store=store)

        # Execute search
        search_results = retriever.retrieve(search_query)

        # Transform to admin-friendly format
        results = []
        for result in search_results:
            chunk = result.chunk
            metadata = result.document_metadata

            # Extract video ID from chunk ID (format: video:{pk}:chunk:{index})
            video_id = chunk.id.split(":")[1] if ":" in chunk.id else ""

            result_item = {
                "chunk_id": chunk.id,
                "content": chunk.content,
                "score": round(result.score, 3),
                "video_id": video_id,
                "video_title": metadata.get("video_title", ""),
                "video_url": metadata.get("video_url", ""),
                "start_time": metadata.get("start_time", 0.0),
                "end_time": metadata.get("end_time", 0.0),
                "timestamp_url": metadata.get("timestamp_url", ""),
                "formatted_timestamp": self._format_timestamp(
                    metadata.get("start_time", 0.0)
                ),
            }
            results.append(result_item)

        return results

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format timestamp in seconds to MM:SS or HH:MM:SS format.

        Args:
            seconds: Timestamp in seconds

        Returns:
            Formatted timestamp string
        """
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


@admin.register(ProcessedContent)
class ProcessedContentAdmin(admin.ModelAdmin):
    list_display = ("video", "created_at", "updated_at")
    search_fields = ("video__title", "summary")
    readonly_fields = ("created_at", "updated_at")
