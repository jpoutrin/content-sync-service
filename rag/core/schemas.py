from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


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
    source_id: Optional[str] = Field(default=None, description="Reference to source (e.g., video_id)")
    created_at: Optional[datetime] = None


class Chunk(BaseModel):
    """A chunk of text extracted from a document."""
    id: str = Field(..., description="Unique identifier for the chunk")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Text content of the chunk")
    index: int = Field(..., description="Position of chunk within document")
    start_char: Optional[int] = Field(default=None, description="Start character offset in original document")
    end_char: Optional[int] = Field(default=None, description="End character offset in original document")
    metadata: dict = Field(default_factory=dict, description="Chunk-specific metadata (e.g., timestamp)")


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
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum similarity score")
    filters: dict = Field(default_factory=dict, description="Metadata filters")


class SearchResult(BaseModel):
    """A single search result."""
    chunk: Chunk
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    document_metadata: dict = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Complete retrieval response."""
    query: str
    results: list[SearchResult]
    total_chunks_searched: Optional[int] = None
    retrieval_time_ms: Optional[float] = None
