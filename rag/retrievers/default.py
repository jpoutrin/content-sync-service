"""Default retriever implementation with ACL-aware semantic search."""

from rag.core.interfaces import (
    EmbedderInterface,
    RetrieverInterface,
    VectorStoreInterface,
)
from rag.core.schemas import Chunk, Document, SearchQuery, SearchResult


class DefaultRetriever(RetrieverInterface):
    """
    ACL-aware semantic search retriever for YouTube transcripts.

    This retriever implements semantic search with ACL filtering and enriches
    results with YouTube timestamp URLs for direct video navigation.

    The retrieval flow:
    1. Embed the query text using the configured embedder
    2. Search the vector store with ACL context for permission filtering
    3. Enrich results with timestamp URLs for YouTube videos
    4. Apply min_score filtering if specified
    5. Return sorted results (highest score first)

    Args:
        embedder: Embedding service for query vectorization
        store: Vector store for similarity search with ACL filtering

    Example:
        >>> from rag.embedders import LiteLLMEmbedder
        >>> from rag.stores.pgvector import PgVectorStore
        >>> from rag.core.acl import QueryACLContext
        >>>
        >>> embedder = LiteLLMEmbedder(provider='local')
        >>> store = PgVectorStore("postgresql://localhost/db")
        >>> retriever = DefaultRetriever(embedder, store)
        >>>
        >>> query = SearchQuery(
        ...     text="How to configure Django?",
        ...     top_k=5,
        ...     acl_context=QueryACLContext(principal_id="user-123")
        ... )
        >>> results = retriever.retrieve(query)
    """

    def __init__(self, embedder: EmbedderInterface, store: VectorStoreInterface):
        """
        Initialize the retriever.

        Args:
            embedder: Embedding service for query vectorization
            store: Vector store for similarity search with ACL filtering
        """
        self.embedder = embedder
        self.store = store

    def retrieve(self, query: SearchQuery) -> list[SearchResult]:
        """
        Execute semantic search with ACL enforcement.

        Embeds the query text, performs vector similarity search with ACL filtering,
        and enriches results with timestamp URLs for YouTube videos.

        Args:
            query: SearchQuery instance with query text, top_k, min_score,
                   and ACLContext for permission filtering

        Returns:
            List of SearchResult objects, sorted by score descending

        Raises:
            ValueError: If query is invalid (empty text, invalid parameters)
            RuntimeError: If embedding or search fails
        """
        # Validate query
        if not query.text or not query.text.strip():
            raise ValueError("Query text cannot be empty")

        if query.top_k < 1:
            raise ValueError("top_k must be at least 1")

        if query.min_score is not None and not (0.0 <= query.min_score <= 1.0):
            raise ValueError("min_score must be between 0.0 and 1.0")

        # Embed the query text
        try:
            query_vector = self.embedder.embed(query.text)
        except Exception as e:
            raise RuntimeError(f"Failed to embed query: {e}") from e

        # Search the vector store with ACL filtering
        try:
            search_results = self.store.search(
                query_vector=query_vector,
                top_k=query.top_k,
                filters=query.filters,
                acl_context=query.acl_context
            )
        except Exception as e:
            raise RuntimeError(f"Vector store search failed: {e}") from e

        # Convert to SearchResult objects with enriched metadata
        results = []
        for chunk, score in search_results:
            # Apply min_score filter if specified
            if query.min_score is not None and score < query.min_score:
                continue

            # Enrich metadata with timestamp URL if available
            enriched_metadata = self._enrich_chunk_metadata(chunk)

            result = SearchResult(
                chunk=chunk,
                score=score,
                document_metadata=enriched_metadata
            )
            results.append(result)

        return results

    def _enrich_chunk_metadata(self, chunk: Chunk) -> dict:
        """
        Enrich chunk metadata with YouTube timestamp URL.

        Extracts video metadata from chunk and constructs a timestamp URL
        for direct navigation to the relevant video segment.

        Args:
            chunk: Chunk object with metadata

        Returns:
            Enriched metadata dict with timestamp_url

        Example metadata format:
            {
                "start_time": 125.5,
                "end_time": 185.2,
                "video_title": "Django Tutorial",
                "video_url": "https://youtube.com/watch?v=abc123",
                "youtube_video_id": "abc123",
                "timestamp_url": "https://youtube.com/watch?v=abc123&t=125"
            }
        """
        enriched = dict(chunk.metadata)

        # Generate timestamp URL if we have the necessary metadata
        youtube_video_id = chunk.metadata.get("youtube_video_id")
        start_time = chunk.metadata.get("start_time")

        if youtube_video_id and start_time is not None:
            # Convert start_time to integer seconds for URL
            start_seconds = int(start_time)
            timestamp_url = f"https://youtube.com/watch?v={youtube_video_id}&t={start_seconds}"
            enriched["timestamp_url"] = timestamp_url

        return enriched

    def index_document(self, document: Document) -> int:
        """
        Index a document (chunk, embed, store).

        This is a placeholder implementation. For transcript ingestion,
        use the dedicated IngestionService which handles the complete
        chunking -> embedding -> indexing pipeline.

        Args:
            document: Document to index

        Returns:
            Number of chunks indexed

        Raises:
            NotImplementedError: This retriever focuses on search,
                                not indexing. Use IngestionService instead.
        """
        raise NotImplementedError(
            "DefaultRetriever does not support document indexing. "
            "Use rag.services.ingestion.IngestionService for indexing transcripts."
        )

    def remove_document(self, document_id: str) -> None:
        """
        Remove a document from the index.

        Delegates to the vector store's delete_by_document method.

        Args:
            document_id: Document ID to remove

        Raises:
            ValueError: If document_id is empty
        """
        if not document_id or not document_id.strip():
            raise ValueError("document_id cannot be empty")

        self.store.delete_by_document(document_id)
