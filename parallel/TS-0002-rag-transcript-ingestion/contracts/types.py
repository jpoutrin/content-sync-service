"""
Contract Types for TS-0002: RAG Transcript Ingestion

IMPORTANT: These are DESIGN DOCUMENTS only. Agents should read these contracts
and recreate the types in the actual project code. DO NOT import from this file.

These contracts define the interfaces between parallel tasks in the transcript
ingestion and search pipeline.

Related types from rag/core/:
- Video (rag.core.schemas.VideoSchema)
- SearchQuery (rag.core.schemas.SearchQuery)
- SearchResult (rag.core.schemas.SearchResult)
- ACLContext (rag.core.acl.ACLContext)
"""

from typing import Protocol, TypedDict, runtime_checkable


# ============================================================================
# ID Format Constants
# ============================================================================

DOCUMENT_ID_FORMAT = "video:{video_pk}"
"""Format for document IDs in vector store: video:{video_pk}"""

CHUNK_ID_FORMAT = "video:{video_pk}:chunk:{chunk_index}"
"""Format for chunk IDs in vector store: video:{video_pk}:chunk:{chunk_index}"""


# ============================================================================
# Metadata Types
# ============================================================================

class ChunkTimestampMetadata(TypedDict, total=True):
    """
    Metadata attached to each transcript chunk.

    This metadata is stored with each chunk in the vector database and used
    to enrich search results with video context.
    """
    start_time: float
    """Start timestamp in seconds"""

    end_time: float
    """End timestamp in seconds"""

    segment_count: int
    """Number of transcript segments merged into this chunk"""

    video_title: str
    """Title of the source video"""

    video_url: str
    """URL to the video page"""

    youtube_video_id: str
    """YouTube video ID (e.g., 'dQw4w9WgXcQ')"""


class EnrichedSearchResult(TypedDict, total=True):
    """
    Search result item returned by the search API.

    Combines semantic search results with video metadata for client consumption.
    """
    chunk_id: str
    """Unique chunk identifier (format: video:{pk}:chunk:{index})"""

    content: str
    """The text content of the chunk"""

    score: float
    """Similarity score (0.0-1.0)"""

    video_id: str
    """Video primary key as string"""

    video_title: str
    """Title of the source video"""

    video_url: str
    """URL to the video page"""

    start_time: float
    """Chunk start timestamp in seconds"""

    end_time: float
    """Chunk end timestamp in seconds"""

    timestamp_url: str
    """Direct URL to video at start timestamp (e.g., with &t=123s)"""


# ============================================================================
# Service Contracts
# ============================================================================

@runtime_checkable
class TranscriptChunkerContract(Protocol):
    """
    Contract for transcript chunking service.

    Implementations must split timestamped transcript segments into semantic
    chunks suitable for embedding, respecting gap thresholds and size limits.

    Reference: rag/core/schemas.py for TranscriptSegment structure
    """

    gap_threshold: float
    """Maximum gap in seconds between segments to merge into one chunk"""

    max_chars: int
    """Maximum characters per chunk"""

    min_chars: int
    """Minimum characters per chunk (avoid tiny fragments)"""

    def chunk(
        self,
        segments: list[dict],  # List of TranscriptSegment-like dicts
        video_metadata: dict,   # Video metadata for chunk annotations
    ) -> list[tuple[str, ChunkTimestampMetadata]]:
        """
        Split transcript segments into chunks with metadata.

        Args:
            segments: List of dicts with 'text', 'start', 'duration' keys
            video_metadata: Dict with 'title', 'url', 'youtube_video_id' keys

        Returns:
            List of (chunk_text, metadata) tuples

        Raises:
            ValueError: If segments are invalid or empty
        """
        ...


@runtime_checkable
class LiteLLMEmbedderContract(Protocol):
    """
    Contract for embedding service using LiteLLM.

    Implementations must support configurable providers (OpenAI, Cohere, etc.)
    and batch processing for efficiency.

    Configuration comes from rag/core/settings.py
    """

    provider: str
    """LiteLLM provider name (e.g., 'openai', 'cohere')"""

    model: str
    """Model identifier (e.g., 'text-embedding-3-small')"""

    batch_size: int
    """Number of texts to embed in one API call"""

    @property
    def dimensions(self) -> int:
        """
        Embedding vector dimensions for this model.

        Returns:
            Number of dimensions in output vectors
        """
        ...

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector (dimensions determined by model)

        Raises:
            ValueError: If text is empty
            RuntimeError: If API call fails
        """
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors, same order as input

        Raises:
            ValueError: If texts is empty or contains empty strings
            RuntimeError: If API call fails
        """
        ...


@runtime_checkable
class IngestionServiceContract(Protocol):
    """
    Contract for transcript ingestion orchestration service.

    Implementations coordinate chunking, embedding, and vector store indexing
    for a video's transcript, with ACL metadata attachment.

    Reference: rag/core/schemas.py for Video model
    """

    def ingest_video(self, video: object) -> int:
        """
        Ingest a video's transcript into the vector store.

        Args:
            video: Video instance with transcript data and ACL info

        Returns:
            Number of chunks indexed

        Raises:
            ValueError: If video has no transcript or invalid ACL
            RuntimeError: If indexing fails
        """
        ...


@runtime_checkable
class DefaultRetrieverContract(Protocol):
    """
    Contract for semantic search retrieval service.

    Implementations perform vector similarity search with ACL filtering,
    returning enriched results with video metadata.

    Reference:
    - rag/core/schemas.py for SearchQuery, SearchResult
    - rag/core/acl.py for ACLContext
    """

    def retrieve(self, query: object) -> list[dict]:
        """
        Execute semantic search with ACL enforcement.

        Args:
            query: SearchQuery instance with query text, top_k, min_score,
                   and ACLContext for permission filtering

        Returns:
            List of EnrichedSearchResult dicts, sorted by score descending

        Raises:
            ValueError: If query is invalid
            RuntimeError: If search fails
        """
        ...
