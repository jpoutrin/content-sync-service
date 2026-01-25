from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .acl import QueryACLContext, Visibility


class DocumentType(str, Enum):
    """Type of source document."""
    TRANSCRIPT = "transcript"
    ARTICLE = "article"
    NOTE = "note"
    OTHER = "other"


class Document(BaseModel):
    """A source document to be chunked and indexed."""
    id: str = Field(..., description="Unique identifier for the document")
    content: str = Field(..., description="Full text content of the document")
    type: DocumentType = Field(default=DocumentType.OTHER)
    metadata: dict = Field(default_factory=dict, description="Arbitrary metadata")
    source_id: str | None = Field(default=None, description="Reference to source (e.g., video_id)")
    created_at: datetime | None = None

    # ACL fields
    owner_id: str = Field(..., description="Principal ID who owns this document")
    visibility: Visibility = Field(default=Visibility.PRIVATE, description="Access visibility level")
    shared_with_users: list[str] = Field(default_factory=list, description="User IDs with direct access")
    shared_with_groups: list[str] = Field(default_factory=list, description="Group IDs with access")
    tenant_id: str | None = Field(default=None, description="Tenant ID for multi-tenant deployments")


class Chunk(BaseModel):
    """A chunk of text extracted from a document."""
    id: str = Field(..., description="Unique identifier for the chunk")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Text content of the chunk")
    index: int = Field(..., description="Position of chunk within document")
    start_char: int | None = Field(default=None, description="Start character offset in original document")
    end_char: int | None = Field(default=None, description="End character offset in original document")
    metadata: dict = Field(default_factory=dict, description="Chunk-specific metadata (e.g., timestamp)")

    # ACL fields (denormalized from parent Document)
    owner_id: str = Field(..., description="Principal ID who owns the parent document")
    visibility: Visibility = Field(default=Visibility.PRIVATE, description="Access visibility level")
    shared_with_users: list[str] = Field(default_factory=list, description="User IDs with direct access")
    shared_with_groups: list[str] = Field(default_factory=list, description="Group IDs with access")
    tenant_id: str | None = Field(default=None, description="Tenant ID for multi-tenant deployments")

    @classmethod
    def from_document(cls, document: "Document", **chunk_fields) -> "Chunk":
        """Create a Chunk from a parent Document, copying all ACL fields.

        Args:
            document: Parent Document to copy ACL fields from
            **chunk_fields: Additional chunk-specific fields (id, content, index, etc.)

        Returns:
            Chunk: A new Chunk instance with ACL fields copied from the document
        """
        acl_fields = {
            "owner_id": document.owner_id,
            "visibility": document.visibility,
            "shared_with_users": document.shared_with_users,
            "shared_with_groups": document.shared_with_groups,
            "tenant_id": document.tenant_id,
        }
        return cls(**chunk_fields, **acl_fields)  # type: ignore[arg-type]


class Embedding(BaseModel):
    """Vector embedding for a chunk."""
    chunk_id: str = Field(..., description="Associated chunk ID")
    vector: list[float] = Field(..., description="Embedding vector")
    model: str = Field(..., description="Model used to generate embedding")
    dimensions: int = Field(..., description="Vector dimensions")


class SearchQuery(BaseModel):
    """A search query for retrieval."""
    text: str = Field(..., description="Query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    min_score: float | None = Field(default=None, ge=0.0, le=1.0, description="Minimum similarity score")
    filters: dict = Field(default_factory=dict, description="Metadata filters")
    acl_context: QueryACLContext = Field(..., description="ACL context for filtering search results")


class SearchResult(BaseModel):
    """A single search result."""
    chunk: Chunk
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    document_metadata: dict = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Complete retrieval response."""
    query: str
    results: list[SearchResult]
    total_chunks_searched: int | None = None
    retrieval_time_ms: float | None = None
