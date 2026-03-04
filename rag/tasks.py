"""Django-Q async tasks for RAG operations.

This module contains async task functions that can be queued via Django-Q
for background processing of RAG operations like transcript ingestion.
"""

import logging
from uuid import UUID

from django.conf import settings

from rag.chunkers.transcript import TranscriptChunker
from rag.embedders.litellm import LiteLLMEmbedder
from rag.services import IngestionService
from rag.stores.pgvector import PgVectorStore
from yt_sync.models import Video

logger = logging.getLogger(__name__)


def ingest_video_task(video_pk: UUID | str, **kwargs) -> int:
    """Ingest a video's transcript into the RAG vector store.

    This is a Django-Q async task that processes a video's transcript by:
    1. Fetching the Video from the database
    2. Initializing RAG components (chunker, embedder, vector store)
    3. Ingesting the transcript via IngestionService
    4. Logging the result

    Args:
        video_pk: Primary key of the Video to ingest
        **kwargs: Additional task metadata (e.g., task_id from Django-Q)

    Returns:
        Number of chunks indexed

    Raises:
        Video.DoesNotExist: If video not found
        ValueError: If video has no transcript or invalid data
        RuntimeError: If ingestion fails

    Example:
        >>> from django_q.tasks import async_task
        >>> async_task('rag.tasks.ingest_video_task', video_id)
    """
    logger.info(f"Starting ingestion task for video pk={video_pk}")

    # Fetch video with related data
    try:
        video = Video.objects.select_related("source", "source__user").get(pk=video_pk)
    except Video.DoesNotExist:
        logger.error(f"Video pk={video_pk} not found")
        raise

    logger.info(f"Processing video: '{video.title}' (ID: {video.id})")

    # Initialize RAG components from settings
    try:
        chunker = _create_chunker()
        embedder = _create_embedder()
        vector_store = _create_vector_store()
        service = IngestionService(chunker, embedder, vector_store)
    except Exception as e:
        logger.error(f"Failed to initialize RAG components for video {video.id}: {e}")
        raise RuntimeError(f"RAG component initialization failed: {e}") from e

    # Perform ingestion
    try:
        chunk_count = service.ingest_video(video)
        logger.info(
            f"Successfully ingested video {video.id} "
            f"('{video.title}'): {chunk_count} chunks"
        )
        return chunk_count
    except Exception as e:
        logger.error(
            f"Failed to ingest video {video.id} ('{video.title}'): {e}",
            exc_info=True,
        )
        raise


def _create_chunker() -> TranscriptChunker:
    """Create TranscriptChunker from settings.

    Returns:
        Configured TranscriptChunker instance
    """
    return TranscriptChunker(
        gap_threshold=settings.RAG_CHUNK_GAP_THRESHOLD,
        max_chars=settings.RAG_CHUNK_MAX_CHARS,
        min_chars=settings.RAG_CHUNK_MIN_CHARS,
    )


def _create_embedder() -> LiteLLMEmbedder:
    """Create LiteLLMEmbedder from settings.

    Returns:
        Configured LiteLLMEmbedder instance
    """
    provider = settings.RAG_EMBEDDING_PROVIDER
    model = settings.RAG_EMBEDDING_MODEL
    batch_size = settings.RAG_EMBEDDING_BATCH_SIZE

    return LiteLLMEmbedder(
        provider=provider,
        model=model,
        batch_size=batch_size,
    )


def _create_vector_store() -> PgVectorStore:
    """Create PgVectorStore using Django database connection.

    Returns:
        Configured PgVectorStore instance
    """
    # Get database connection settings from Django
    db_settings = settings.DATABASES["default"]

    # Build PostgreSQL connection string
    connection_string = (
        f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}"
        f"@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
    )

    # Get embedder to determine dimensions
    embedder = _create_embedder()

    return PgVectorStore(
        connection_string=connection_string,
        table_name="rag_embeddings",
        dimensions=embedder.dimensions,
    )
