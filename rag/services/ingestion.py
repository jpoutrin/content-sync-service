"""Transcript ingestion orchestration service.

This module provides the IngestionService, which orchestrates the process of
ingesting video transcripts into the vector store for semantic search.

The service coordinates:
1. Building Document from Video with ACL metadata
2. Chunking transcript segments via TranscriptChunker
3. Embedding chunks via EmbedderInterface
4. Storing chunks and embeddings via VectorStoreInterface

Example:
    >>> from yt_sync.models import Video
    >>> from rag.services import IngestionService
    >>> from rag.chunkers.transcript import TranscriptChunker
    >>> from rag.embedders.litellm import LiteLLMEmbedder
    >>> from rag.stores.pgvector import PgVectorStore
    >>>
    >>> chunker = TranscriptChunker()
    >>> embedder = LiteLLMEmbedder(provider='local')
    >>> store = PgVectorStore(connection_string="postgresql://...")
    >>> service = IngestionService(chunker, embedder, store)
    >>>
    >>> video = Video.objects.get(pk=some_pk)
    >>> count = service.ingest_video(video)
    >>> print(f"Indexed {count} chunks")
"""

from typing import Any

from rag.core.acl import Visibility
from rag.core.interfaces import (
    ChunkerInterface,
    EmbedderInterface,
    VectorStoreInterface,
)
from rag.core.schemas import Document, DocumentType, Embedding


class IngestionService:
    """Orchestrates video transcript ingestion into the vector store.

    This service coordinates chunking, embedding, and storage of video transcripts,
    ensuring ACL metadata is properly propagated throughout the pipeline.

    Args:
        chunker: ChunkerInterface implementation for transcript chunking
        embedder: EmbedderInterface implementation for generating embeddings
        vector_store: VectorStoreInterface implementation for storage

    Example:
        >>> service = IngestionService(chunker, embedder, vector_store)
        >>> chunk_count = service.ingest_video(video)
    """

    def __init__(
        self,
        chunker: ChunkerInterface,
        embedder: EmbedderInterface,
        vector_store: VectorStoreInterface,
    ):
        """Initialize the IngestionService.

        Args:
            chunker: Chunker implementation for splitting transcripts
            embedder: Embedder implementation for generating vectors
            vector_store: Vector store implementation for persistence
        """
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store

    def ingest_video(self, video: Any) -> int:
        """Ingest a video's transcript into the vector store.

        Builds a Document from the Video model with proper ACL metadata,
        chunks the transcript, generates embeddings, and stores them in
        the vector store.

        Args:
            video: Video instance with transcript data and ACL info.
                   Must have:
                   - transcript_data: list of transcript segments
                   - source.user.id: owner user ID
                   - youtube_video_id: YouTube video identifier
                   - title: video title
                   - url: video URL

        Returns:
            Number of chunks indexed

        Raises:
            ValueError: If video has no transcript or invalid ACL metadata
            RuntimeError: If chunking, embedding, or indexing fails
        """
        # Validate transcript data
        if not video.transcript_data:
            raise ValueError(f"Video {video.id} has no transcript data")

        # Build Document from Video with ACL metadata
        document = self._build_document_from_video(video)

        # Chunk the document
        try:
            chunks = self.chunker.chunk(document)
        except Exception as e:
            raise RuntimeError(f"Chunking failed for video {video.id}: {e}") from e

        if not chunks:
            raise ValueError(f"No chunks generated for video {video.id}")

        # Generate embeddings for all chunks
        try:
            chunk_texts = [chunk.content for chunk in chunks]
            embedding_vectors = self.embedder.embed_batch(chunk_texts)
        except Exception as e:
            raise RuntimeError(f"Embedding failed for video {video.id}: {e}") from e

        # Create Embedding objects
        embeddings = [
            Embedding(
                chunk_id=chunk.id,
                vector=vector,
                model=self.embedder.model_name,
                dimensions=self.embedder.dimensions,
            )
            for chunk, vector in zip(chunks, embedding_vectors, strict=True)
        ]

        # Store chunks and embeddings in vector store
        try:
            self.vector_store.upsert_batch(chunks, embeddings)
        except Exception as e:
            raise RuntimeError(f"Storage failed for video {video.id}: {e}") from e

        return len(chunks)

    def _build_document_from_video(self, video: Any) -> Document:
        """Build a Document from a Video model instance.

        Extracts metadata and ACL information from the Video and its related
        Source to create a properly structured Document.

        Args:
            video: Video instance with transcript and ACL data

        Returns:
            Document with proper ID format and ACL metadata

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if not hasattr(video, "source") or video.source is None:
            raise ValueError(f"Video {video.id} missing source or user relationship")

        if not hasattr(video.source, "user") or video.source.user is None:
            raise ValueError(f"Video {video.id} missing source or user relationship")

        if not video.youtube_video_id:
            raise ValueError(f"Video {video.id} missing youtube_video_id")

        if not video.title:
            raise ValueError(f"Video {video.id} missing title")

        if not video.url:
            raise ValueError(f"Video {video.id} missing url")

        # Document ID format: video:{video_pk}
        document_id = f"video:{video.pk}"

        # Owner ID from source.user
        owner_id = str(video.source.user.id)

        # Build metadata for chunker
        metadata = {
            "transcript_segments": video.transcript_data,
            "video_title": video.title,
            "video_url": video.url,
            "youtube_video_id": video.youtube_video_id,
        }

        # Create Document with ACL metadata
        # Videos are typically PRIVATE by default - user owns their content
        # In future, this could be configurable based on Video model fields
        document = Document(
            id=document_id,
            content="",  # Not used for transcript chunking
            type=DocumentType.TRANSCRIPT,
            metadata=metadata,
            source_id=str(video.id),
            owner_id=owner_id,
            visibility=Visibility.PRIVATE,
            shared_with_users=[],
            shared_with_groups=[],
            tenant_id=None,  # Single-tenant for now
        )

        return document
