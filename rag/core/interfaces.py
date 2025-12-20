from abc import ABC, abstractmethod

from .acl import QueryACLContext, Visibility
from .schemas import Chunk, Document, Embedding, SearchQuery, SearchResult


class ChunkerInterface(ABC):
    """Interface for document chunking strategies."""

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """
        Split a document into chunks.

        Args:
            document: The document to chunk

        Returns:
            List of chunks with metadata
        """
        pass


class EmbedderInterface(ABC):
    """Interface for embedding generation."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass


class VectorStoreInterface(ABC):
    """Interface for vector storage and similarity search."""

    @abstractmethod
    def upsert(self, chunk: Chunk, embedding: Embedding) -> None:
        """
        Insert or update a chunk with its embedding.

        Args:
            chunk: The chunk to store
            embedding: The embedding for the chunk
        """
        pass

    @abstractmethod
    def upsert_batch(self, chunks: list[Chunk], embeddings: list[Embedding]) -> None:
        """
        Batch insert/update chunks with embeddings.

        Args:
            chunks: List of chunks to store
            embeddings: List of embeddings (same order as chunks)
        """
        pass

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
        acl_context: QueryACLContext | None = None
    ) -> list[tuple[Chunk, float]]:
        """
        Search for similar chunks with optional ACL filtering.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            acl_context: Optional ACL context for access control filtering.
                        If provided, results will be filtered based on the
                        principal's permissions. If None or bypass_acl=True,
                        no ACL filtering is applied.

        Returns:
            List of (chunk, score) tuples sorted by similarity
        """
        pass

    @abstractmethod
    def delete(self, chunk_ids: list[str]) -> None:
        """
        Delete chunks by ID.

        Args:
            chunk_ids: List of chunk IDs to delete
        """
        pass

    @abstractmethod
    def delete_by_document(self, document_id: str) -> None:
        """
        Delete all chunks belonging to a document.

        Args:
            document_id: Document ID whose chunks should be deleted
        """
        pass

    @abstractmethod
    def delete_by_owner(self, owner_id: str, tenant_id: str | None = None) -> int:
        """
        Delete all chunks owned by a specific principal (GDPR compliance).

        This method supports the "right to be forgotten" by removing all content
        owned by a user. If tenant_id is provided, deletion is scoped to that tenant.

        Args:
            owner_id: The principal ID (user/service) whose chunks should be deleted
            tenant_id: Optional tenant ID to scope deletion. If None, deletes across
                      all tenants (or in single-tenant deployments). If provided,
                      only deletes chunks where tenant_id matches.

        Returns:
            int: Count of chunks deleted

        Raises:
            ValueError: If owner_id is empty or invalid
        """
        pass

    @abstractmethod
    def update_document_acl(
        self,
        document_id: str,
        visibility: Visibility | None = None,
        shared_with_users: list[str] | None = None,
        shared_with_groups: list[str] | None = None
    ) -> int:
        """
        Update ACL settings for all chunks belonging to a document.

        This method allows updating ACL fields without re-embedding the document.
        Only non-None parameters are updated, allowing partial updates.

        Args:
            document_id: The document ID whose chunks should be updated
            visibility: New visibility level (if provided)
            shared_with_users: New list of user IDs with access (if provided).
                              Replaces existing list completely.
            shared_with_groups: New list of group IDs with access (if provided).
                               Replaces existing list completely.

        Returns:
            int: Count of chunks updated

        Raises:
            ValueError: If document_id is empty or no update parameters provided
        """
        pass


class RetrieverInterface(ABC):
    """High-level interface combining embedding and search."""

    @abstractmethod
    def retrieve(self, query: SearchQuery) -> list[SearchResult]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Search query with parameters

        Returns:
            List of search results with scores
        """
        pass

    @abstractmethod
    def index_document(self, document: Document) -> int:
        """
        Index a document (chunk, embed, store).

        Args:
            document: Document to index

        Returns:
            Number of chunks indexed
        """
        pass

    @abstractmethod
    def remove_document(self, document_id: str) -> None:
        """
        Remove a document from the index.

        Args:
            document_id: Document ID to remove
        """
        pass
