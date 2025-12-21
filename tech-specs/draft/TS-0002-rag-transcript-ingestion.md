---
tech_spec_id: TS-0002
title: RAG Transcript Ingestion & Search
status: DRAFT
author: ""
reviewers: []
created: 2025-12-21
last_updated: 2025-12-21
approved_date: ""
decision_ref: ""
related_rfcs:
  - RFC-0001 (RAG ACL Management)
  - RFC-0002 (Vector Storage for RAG - Phase 1)
related_tech_specs:
  - TS-0001 (RAG ACL Management)
related_frds:
  - FRD-001 (RAG Transcript Ingestion & Search)
implementation_branch: ""
---

# TS-0002: RAG Transcript Ingestion & Search

## Executive Summary

This Technical Specification details the implementation of transcript ingestion and semantic search capabilities for the RAG module. The feature enables automatic chunking of YouTube video transcripts, embedding generation via LiteLLM, storage in pgvector, and semantic search with ACL enforcement and timestamp-based video linking.

### Key Deliverables

1. `TranscriptChunker` - Timestamp-based transcript chunking
2. `LiteLLMEmbedder` - Embedding generation with provider abstraction
3. `IngestionService` - Orchestrates chunking, embedding, and storage
4. `DefaultRetriever` - Semantic search with ACL filtering
5. Search API endpoint (`/api/rag/search`)
6. CLI commands (`rag_search`, `rag_ingest`)
7. Admin interface for search and management
8. Django signal for auto-ingestion

### Dependencies

- TS-0001 (RAG ACL Management) - APPROVED
- FRD-001 (RAG Transcript Ingestion & Search) - Approved
- Existing `rag/core/` module with interfaces and schemas
- Existing `rag/stores/pgvector.py` with PgVectorStore
- `yt_sync.Video` model with transcript data

---

## Table of Contents

- [Design Overview](#design-overview)
- [Detailed Design](#detailed-design)
- [API Specification](#api-specification)
- [Data Model](#data-model)
- [Configuration](#configuration)
- [Testing Strategy](#testing-strategy)
- [Implementation Plan](#implementation-plan)

---

## Design Overview

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Ingestion Flow                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌───────────────────┐    ┌─────────────────────────┐  │
│  │  Video   │    │ Django Signal     │    │    Django-Q Task        │  │
│  │  Model   │───▶│ (transcript_saved)│───▶│  (async_ingest_video)   │  │
│  └──────────┘    └───────────────────┘    └───────────┬─────────────┘  │
│                                                        │                 │
│                                           ┌────────────▼─────────────┐  │
│                                           │   IngestionService       │  │
│                                           │                          │  │
│                                           │  ┌────────────────────┐  │  │
│                                           │  │ TranscriptChunker  │  │  │
│                                           │  │ (timestamp-based)  │  │  │
│                                           │  └─────────┬──────────┘  │  │
│                                           │            │             │  │
│                                           │  ┌─────────▼──────────┐  │  │
│                                           │  │  LiteLLMEmbedder   │  │  │
│                                           │  │ (batch embedding)  │  │  │
│                                           │  └─────────┬──────────┘  │  │
│                                           │            │             │  │
│                                           │  ┌─────────▼──────────┐  │  │
│                                           │  │   PgVectorStore    │  │  │
│                                           │  │ (upsert with ACL)  │  │  │
│                                           │  └────────────────────┘  │  │
│                                           └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          Search Flow                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌───────────────────┐    ┌─────────────────────────┐  │
│  │  Client  │    │   Search API      │    │   DefaultRetriever      │  │
│  │  Request │───▶│  /api/rag/search  │───▶│                         │  │
│  └──────────┘    └───────────────────┘    │  ┌────────────────────┐ │  │
│                                            │  │ LiteLLMEmbedder    │ │  │
│                                            │  │ (query embedding)  │ │  │
│                                            │  └─────────┬──────────┘ │  │
│                                            │            │            │  │
│                                            │  ┌─────────▼──────────┐ │  │
│                                            │  │  PgVectorStore     │ │  │
│                                            │  │ (similarity + ACL) │ │  │
│                                            │  └─────────┬──────────┘ │  │
│                                            └────────────┼────────────┘  │
│                                                         │               │
│  ┌──────────┐    ┌───────────────────┐                 │               │
│  │  Client  │◀───│   JSON Response   │◀────────────────┘               │
│  │ Response │    │ (results + links) │                                  │
│  └──────────┘    └───────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Location | Purpose |
|-----------|----------|---------|
| TranscriptChunker | `rag/chunkers/transcript.py` | Split transcripts by timestamp gaps |
| LiteLLMEmbedder | `rag/embedders/litellm.py` | Generate embeddings via LiteLLM |
| IngestionService | `rag/services/ingestion.py` | Orchestrate ingestion pipeline |
| DefaultRetriever | `rag/retrievers/default.py` | Handle search queries |
| SearchView | `rag/api/views.py` | REST API endpoint |
| rag_search | `rag/management/commands/` | CLI search command |
| rag_ingest | `rag/management/commands/` | CLI ingest command |

---

## Detailed Design

### 1. TranscriptChunker

Implements `ChunkerInterface` from `rag/core/interfaces.py`.

#### Algorithm

1. Parse `transcript_data` (list of timed segments)
2. Iterate through segments, accumulating text
3. Create chunk boundary when:
   - Gap between segments > `RAG_CHUNK_GAP_THRESHOLD` (default: 2.0s)
   - Accumulated text > `RAG_CHUNK_MAX_CHARS` (default: 1000)
4. Each chunk includes:
   - Combined text from segments
   - `start_time` from first segment
   - `end_time` from last segment
   - Segment count for debugging

#### Interface

```python
from rag.core.interfaces import ChunkerInterface
from rag.core.schemas import Document, Chunk

class TranscriptChunker(ChunkerInterface):
    def __init__(
        self,
        gap_threshold: float = 2.0,
        max_chars: int = 1000,
        min_chars: int = 100
    ):
        self.gap_threshold = gap_threshold
        self.max_chars = max_chars
        self.min_chars = min_chars

    def chunk(self, document: Document) -> list[Chunk]:
        """
        Chunk transcript by timestamp gaps.

        Uses Chunk.from_document() to automatically inherit ACL fields
        from the parent Document (owner_id, visibility, shared_with_users,
        shared_with_groups, tenant_id).

        Args:
            document: Document with transcript_data in metadata

        Returns:
            List of Chunk objects with ACL and timestamp metadata
        """
        ...
```

#### ACL Inheritance

Chunks automatically inherit ACL fields from the parent Document using `Chunk.from_document()`:

```python
# From rag/core/schemas.py
class Chunk(BaseModel):
    # Core fields
    id: str
    document_id: str
    content: str
    index: int
    metadata: dict  # Contains timestamp metadata (see below)

    # ACL fields (denormalized from parent Document)
    owner_id: str                    # Principal ID who owns the document
    visibility: Visibility           # PRIVATE, SHARED, INTERNAL, PUBLIC
    shared_with_users: list[str]     # User IDs with direct access
    shared_with_groups: list[str]    # Group IDs with access
    tenant_id: str | None            # Tenant ID for multi-tenant

    @classmethod
    def from_document(cls, document: Document, **chunk_fields) -> Chunk:
        """Create Chunk with ACL fields copied from parent Document."""
```

**Usage in TranscriptChunker:**
```python
chunk = Chunk.from_document(
    document,
    id=f"video:{video_id}:chunk:{index}",
    document_id=document.id,
    content=chunk_text,
    index=index,
    metadata={"start_time": start, "end_time": end, ...}
)
```

See **TS-0001 (RAG ACL Management)** for full ACL system documentation.

#### Chunk Timestamp Metadata

The `Chunk.metadata` dict contains transcript-specific fields:

```python
{
    "start_time": 45.2,      # float, seconds from video start
    "end_time": 62.8,        # float, seconds
    "segment_count": 5,      # int, number of original segments
    "video_title": "...",    # str, from Video model
    "video_url": "...",      # str, YouTube URL
    "youtube_video_id": "..." # str, for timestamp URL generation
}
```

### 2. LiteLLMEmbedder

Implements `EmbedderInterface` from `rag/core/interfaces.py`.

#### Provider Configuration

| Provider | Model | Dimensions | Cost |
|----------|-------|------------|------|
| local | sentence-transformers/all-MiniLM-L6-v2 | 384 | Free |
| openai | text-embedding-3-small | 1536 | $0.02/1M tokens |
| openai | text-embedding-3-large | 3072 | $0.13/1M tokens |

#### Interface

```python
from rag.core.interfaces import EmbedderInterface
from rag.core.schemas import Chunk, Embedding

class LiteLLMEmbedder(EmbedderInterface):
    def __init__(
        self,
        provider: str = "local",
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        batch_size: int = 50
    ):
        self.provider = provider
        self.model = model
        self.batch_size = batch_size

    def embed(self, chunks: list[Chunk]) -> list[Embedding]:
        """
        Generate embeddings for chunks using LiteLLM.

        Args:
            chunks: List of Chunk objects

        Returns:
            List of Embedding objects with vectors
        """
        ...

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector as list of floats
        """
        ...

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions for configured model."""
        ...
```

#### LiteLLM Integration

```python
import litellm

def _embed_batch(self, texts: list[str]) -> list[list[float]]:
    """Call LiteLLM embedding API."""
    if self.provider == "local":
        # Use sentence-transformers directly
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(self.model)
        return model.encode(texts).tolist()
    else:
        # Use LiteLLM for OpenAI/other providers
        response = litellm.embedding(
            model=f"{self.provider}/{self.model}",
            input=texts
        )
        return [r["embedding"] for r in response.data]
```

### 3. IngestionService

Orchestrates the ingestion pipeline.

#### Interface

```python
from yt_sync.models import Video
from rag.core.acl import ACLContext

class IngestionService:
    def __init__(
        self,
        chunker: ChunkerInterface,
        embedder: EmbedderInterface,
        store: VectorStoreInterface
    ):
        self.chunker = chunker
        self.embedder = embedder
        self.store = store

    def ingest_video(self, video: Video) -> int:
        """
        Ingest a video transcript into the RAG system.

        Args:
            video: Video model instance with transcript data

        Returns:
            Number of chunks indexed

        Raises:
            ValueError: If video has no transcript data
        """
        ...

    def _build_document(self, video: Video) -> Document:
        """Create Document from Video model."""
        ...

    def _build_acl_context(self, video: Video) -> ACLContext:
        """Build ACL context from video ownership."""
        ...
```

#### Ingestion Workflow

```python
def ingest_video(self, video: Video) -> int:
    # 1. Validate transcript exists
    if not video.transcript_data:
        raise ValueError(f"No transcript data for video {video.id}")

    # 2. Build Document
    document = self._build_document(video)

    # 3. Chunk transcript
    chunks = self.chunker.chunk(document)

    if not chunks:
        logger.warning(f"No chunks generated for video {video.id}")
        return 0

    # 4. Generate embeddings
    embeddings = self.embedder.embed(chunks)

    # 5. Build ACL context
    acl_context = self._build_acl_context(video)

    # 6. Upsert to vector store
    self.store.upsert(embeddings, acl_context)

    logger.info(f"Indexed {len(chunks)} chunks for video {video.id}")
    return len(chunks)
```

### 4. DefaultRetriever

Implements `RetrieverInterface` from `rag/core/interfaces.py`.

#### Interface

```python
from rag.core.interfaces import RetrieverInterface
from rag.core.schemas import SearchQuery, SearchResult

class DefaultRetriever(RetrieverInterface):
    def __init__(
        self,
        embedder: EmbedderInterface,
        store: VectorStoreInterface
    ):
        self.embedder = embedder
        self.store = store

    def retrieve(self, query: SearchQuery) -> list[SearchResult]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: SearchQuery with text and ACL context

        Returns:
            List of SearchResult objects with scores and metadata
        """
        # 1. Embed query
        query_vector = self.embedder.embed_query(query.query)

        # 2. Search with ACL filtering
        results = self.store.search(
            query_vector=query_vector,
            top_k=query.top_k,
            acl_context=query.acl_context,
            min_score=query.min_score
        )

        # 3. Enrich results with timestamp URLs
        return self._enrich_results(results)

    def _enrich_results(self, results: list[SearchResult]) -> list[SearchResult]:
        """Add timestamp URLs to results."""
        for result in results:
            if "youtube_video_id" in result.metadata:
                video_id = result.metadata["youtube_video_id"]
                start = int(result.metadata.get("start_time", 0))
                result.metadata["timestamp_url"] = (
                    f"https://youtube.com/watch?v={video_id}&t={start}"
                )
        return results
```

---

## API Specification

### Search Endpoint

```yaml
openapi: 3.0.0
paths:
  /api/rag/search:
    get:
      summary: Search transcript content
      description: Semantic search across indexed transcripts with ACL enforcement
      security:
        - bearerAuth: []
        - sessionAuth: []
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
            minLength: 1
            maxLength: 500
          description: Search query text
        - name: top_k
          in: query
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 5
          description: Number of results to return
        - name: min_score
          in: query
          required: false
          schema:
            type: number
            minimum: 0.0
            maximum: 1.0
            default: 0.0
          description: Minimum similarity score threshold
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SearchResponse'
        '400':
          description: Invalid request (missing query)
        '401':
          description: Not authenticated
        '500':
          description: Search/embedding failure

components:
  schemas:
    SearchResponse:
      type: object
      properties:
        query:
          type: string
          description: Original query text
        results:
          type: array
          items:
            $ref: '#/components/schemas/SearchResultItem'
        total:
          type: integer
          description: Number of results returned

    SearchResultItem:
      type: object
      properties:
        chunk_id:
          type: string
          description: Unique chunk identifier
        content:
          type: string
          description: Transcript segment text
        score:
          type: number
          description: Similarity score (0-1)
        video_id:
          type: string
          description: YouTube video ID
        video_title:
          type: string
          description: Video title
        video_url:
          type: string
          description: YouTube video URL
        start_time:
          type: number
          description: Start time in seconds
        end_time:
          type: number
          description: End time in seconds
        timestamp_url:
          type: string
          description: YouTube URL with timestamp
```

### DRF Serializers

```python
# rag/api/serializers.py

from rest_framework import serializers

class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=True, min_length=1, max_length=500)
    top_k = serializers.IntegerField(required=False, default=5, min_value=1, max_value=100)
    min_score = serializers.FloatField(required=False, default=0.0, min_value=0.0, max_value=1.0)


class SearchResultSerializer(serializers.Serializer):
    chunk_id = serializers.CharField()
    content = serializers.CharField()
    score = serializers.FloatField()
    video_id = serializers.CharField()
    video_title = serializers.CharField()
    video_url = serializers.URLField()
    start_time = serializers.FloatField()
    end_time = serializers.FloatField()
    timestamp_url = serializers.URLField()


class SearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    results = SearchResultSerializer(many=True)
    total = serializers.IntegerField()
```

---

## Data Model

### Existing Models Used

#### Video Model (yt_sync.models)

```python
class Video(models.Model):
    # Relevant fields for RAG ingestion
    youtube_id = models.CharField(max_length=20)
    title = models.CharField(max_length=500)
    transcript_text = models.TextField(blank=True)  # Full transcript
    transcript_data = models.JSONField(default=list)  # Timed segments
    transcript_status = models.CharField(choices=TranscriptStatus.choices)
    source = models.ForeignKey(YouTubeSource)  # Has .user for ACL
```

#### rag_embeddings Table (existing)

```sql
-- From rag/migrations/0001_create_rag_embeddings.py
CREATE TABLE rag_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    embedding vector(1536),  -- Or 384 for local embeddings
    metadata JSONB DEFAULT '{}',
    owner_id TEXT,
    group_ids TEXT[] DEFAULT '{}',
    visibility TEXT DEFAULT 'PRIVATE',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON rag_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON rag_embeddings (owner_id);
CREATE INDEX ON rag_embeddings (visibility);
CREATE INDEX ON rag_embeddings USING GIN (group_ids);
```

### Chunk ID Convention

```
video:{video_pk}:chunk:{chunk_index}

Example: video:123:chunk:0
```

### Document ID Convention

```
video:{video_pk}

Example: video:123
```

---

## Configuration

### Settings (config/settings.py)

```python
# RAG Ingestion Configuration
RAG_EMBEDDING_PROVIDER = env('RAG_EMBEDDING_PROVIDER', default='local')
RAG_EMBEDDING_MODEL = env('RAG_EMBEDDING_MODEL', default='sentence-transformers/all-MiniLM-L6-v2')
RAG_AUTO_INGEST = env.bool('RAG_AUTO_INGEST', default=True)

# Chunking Configuration
RAG_CHUNK_GAP_THRESHOLD = env.float('RAG_CHUNK_GAP_THRESHOLD', default=2.0)
RAG_CHUNK_MAX_CHARS = env.int('RAG_CHUNK_MAX_CHARS', default=1000)
RAG_CHUNK_MIN_CHARS = env.int('RAG_CHUNK_MIN_CHARS', default=100)

# Embedding batch size
RAG_EMBEDDING_BATCH_SIZE = env.int('RAG_EMBEDDING_BATCH_SIZE', default=50)
```

### Environment Variables

```bash
# Development (local embeddings)
RAG_EMBEDDING_PROVIDER=local
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_AUTO_INGEST=True

# Production (OpenAI embeddings)
RAG_EMBEDDING_PROVIDER=openai
RAG_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-...
RAG_AUTO_INGEST=True
```

---

## Testing Strategy

**Coverage Target**: >90% on core components
**Total Test Scenarios**: ~90 tests across 8 test classes

### 1. TranscriptChunker Tests

```python
# rag/chunkers/tests/test_transcript.py
class TestTranscriptChunker:
    # Happy Path
    def test_chunk_by_timestamp_gaps(self):
        """Chunks split at gaps > threshold (default 2.0s)."""

    def test_chunk_respects_max_chars(self):
        """Long segments split at max_chars (default 1000)."""

    def test_chunk_minimum_size_merges_small_segments(self):
        """Short segments merged until min_chars (default 100)."""

    def test_chunk_metadata_includes_timestamps(self):
        """Each chunk has start_time, end_time, segment_count."""

    def test_chunk_inherits_acl_from_document(self):
        """Chunks created via Chunk.from_document() with ACL fields."""

    # Edge Cases
    def test_empty_transcript_returns_empty_list(self):
        """No error on empty transcript_data."""

    def test_single_segment_creates_one_chunk(self):
        """Single segment becomes single chunk."""

    def test_very_long_transcript_batches_correctly(self):
        """Transcript > 100k chars processed without memory issues."""

    def test_no_gaps_creates_single_chunk(self):
        """Continuous speech without pauses becomes one chunk."""

    def test_all_gaps_creates_per_segment_chunks(self):
        """Every segment separated by > threshold becomes own chunk."""

    def test_unicode_content_handled_correctly(self):
        """Non-ASCII characters (emoji, CJK) preserved."""

    def test_special_characters_in_content(self):
        """Quotes, newlines, HTML entities handled."""

    # Boundary Conditions
    def test_chunk_at_exact_max_chars(self):
        """Segment at exactly max_chars boundary."""

    def test_chunk_at_exact_min_chars(self):
        """Segment at exactly min_chars boundary."""

    def test_gap_at_exact_threshold(self):
        """Gap at exactly threshold (2.0s) - inclusive or exclusive."""
```

### 2. LiteLLMEmbedder Tests

```python
# rag/embedders/tests/test_litellm.py
class TestLiteLLMEmbedder:
    # Provider Tests
    def test_local_provider_returns_384_dims(self):
        """sentence-transformers/all-MiniLM-L6-v2 returns 384-dim vectors."""

    def test_openai_provider_returns_1536_dims(self):
        """text-embedding-3-small returns 1536-dim vectors."""

    def test_provider_switching_at_runtime(self):
        """Can switch providers without restart."""

    # Embedding Tests
    def test_embed_single_text(self):
        """Single chunk produces one embedding."""

    def test_embed_batch_respects_batch_size(self):
        """Batch of 100 chunks split into batches of 50."""

    def test_embed_empty_list_returns_empty(self):
        """Empty chunk list returns empty embedding list."""

    def test_embed_query_returns_list_of_floats(self):
        """Query embedding returns list[float] not nested."""

    # Error Handling
    def test_api_timeout_raises_exception(self):
        """Timeout from embedding API raises EmbeddingError."""

    def test_invalid_model_raises_exception(self):
        """Unknown model name raises ConfigurationError."""

    def test_rate_limit_retry_behavior(self):
        """429 response triggers retry with backoff."""
```

### 3. IngestionService Tests

```python
# rag/services/tests/test_ingestion.py
class TestIngestionService:
    # Happy Path
    def test_ingest_video_creates_chunks(self):
        """Video with transcript creates expected chunk count."""

    def test_ingest_video_generates_embeddings(self):
        """Each chunk gets corresponding embedding."""

    def test_ingest_video_stores_with_acl(self):
        """Chunks stored with owner_id and visibility."""

    def test_ingest_returns_chunk_count(self):
        """Returns integer count of indexed chunks."""

    # ACL Inheritance
    def test_chunks_inherit_owner_id(self):
        """Chunk owner_id matches video.source.user.id."""

    def test_chunks_inherit_visibility(self):
        """Chunk visibility defaults to PRIVATE."""

    def test_chunks_inherit_shared_with_groups(self):
        """Group sharing propagates to chunks."""

    # Error Handling
    def test_ingest_video_no_transcript_raises(self):
        """ValueError raised for video without transcript_data."""

    def test_ingest_video_empty_transcript_data(self):
        """Empty list returns 0, no error."""

    def test_embedding_failure_rolls_back(self):
        """No partial state if embedding fails mid-batch."""

    def test_store_failure_rolls_back(self):
        """No partial state if pgvector upsert fails."""

    # Upsert Behavior
    def test_reingest_replaces_existing_chunks(self):
        """Re-indexing same video replaces all chunks."""

    def test_reingest_updates_embeddings(self):
        """New embeddings replace old ones."""

    def test_reingest_preserves_document_id(self):
        """Document ID remains video:{pk}."""
```

### 4. DefaultRetriever Tests

```python
# rag/retrievers/tests/test_default.py
class TestDefaultRetriever:
    # Search Quality
    def test_retrieve_returns_relevant_results(self):
        """Query 'authentication' finds auth-related chunks."""

    def test_retrieve_ranks_by_similarity(self):
        """Higher similarity scores ranked first."""

    def test_retrieve_respects_top_k(self):
        """top_k=5 returns at most 5 results."""

    def test_retrieve_filters_by_min_score(self):
        """Results below min_score excluded."""

    # Timestamp Enrichment
    def test_results_include_timestamp_url(self):
        """Each result has timestamp_url field."""

    def test_timestamp_url_format_correct(self):
        """URL format: youtube.com/watch?v={id}&t={seconds}."""

    def test_missing_youtube_id_no_timestamp_url(self):
        """Graceful handling if youtube_video_id missing."""

    # Empty Results
    def test_no_matches_returns_empty_list(self):
        """Query with no matches returns []."""

    def test_all_below_min_score_returns_empty(self):
        """All results below threshold returns []."""
```

### 5. ACL Security Tests (Critical)

```python
# rag/tests/test_acl_security.py
class TestACLSecurity:
    """Critical security tests for ACL enforcement."""

    # PRIVATE Visibility
    def test_private_visible_only_to_owner(self):
        """Owner can search their PRIVATE content."""

    def test_private_not_visible_to_other_users(self):
        """Other authenticated users cannot see PRIVATE."""

    def test_private_not_visible_to_group_members(self):
        """Group membership alone doesn't grant PRIVATE access."""

    # SHARED Visibility
    def test_shared_visible_to_owner(self):
        """Owner always sees SHARED content."""

    def test_shared_visible_to_shared_users(self):
        """Users in shared_with_users can see content."""

    def test_shared_visible_to_shared_groups(self):
        """Users in shared_with_groups can see content."""

    def test_shared_not_visible_to_non_shared_users(self):
        """Users not in shared lists cannot see SHARED."""

    # INTERNAL Visibility
    def test_internal_visible_to_all_authenticated(self):
        """Any authenticated user sees INTERNAL content."""

    def test_internal_not_visible_to_anonymous(self):
        """Anonymous requests cannot see INTERNAL."""

    def test_internal_respects_tenant_isolation(self):
        """INTERNAL only visible within same tenant."""

    # PUBLIC Visibility
    def test_public_visible_to_anonymous(self):
        """PUBLIC content visible without authentication."""

    def test_public_visible_to_all_authenticated(self):
        """PUBLIC visible to any authenticated user."""

    # Tenant Isolation
    def test_different_tenant_cannot_access(self):
        """User in tenant A cannot see tenant B content."""

    def test_same_tenant_can_access_internal(self):
        """User in same tenant sees INTERNAL content."""

    def test_null_tenant_accessible_to_all(self):
        """Content with NULL tenant_id visible to all tenants."""

    # Admin Bypass
    def test_admin_bypass_sees_all_private(self):
        """Staff user with bypass_acl=True sees all content."""

    def test_bypass_requires_staff_user(self):
        """Non-staff cannot use bypass_acl."""

    def test_bypass_logged_for_audit(self):
        """ACL bypass operations are logged."""
```

### 6. Search API Tests

```python
# rag/api/tests/test_search.py
class TestSearchAPI:
    # Authentication
    def test_search_requires_authentication(self):
        """401 returned without authentication."""

    def test_search_accepts_bearer_token(self):
        """Supabase JWT authentication works."""

    def test_search_accepts_session_auth(self):
        """Django session authentication works."""

    # Request Validation
    def test_missing_query_returns_400(self):
        """GET /api/rag/search without q= returns 400."""

    def test_empty_query_returns_400(self):
        """GET /api/rag/search?q= returns 400."""

    def test_query_too_long_returns_400(self):
        """Query > 500 chars returns 400."""

    def test_invalid_top_k_returns_400(self):
        """top_k=0 or top_k=101 returns 400."""

    def test_invalid_min_score_returns_400(self):
        """min_score=-0.1 or min_score=1.5 returns 400."""

    # Response Format
    def test_response_includes_query(self):
        """Response JSON has 'query' field."""

    def test_response_includes_results_array(self):
        """Response JSON has 'results' array."""

    def test_response_includes_total_count(self):
        """Response JSON has 'total' integer."""

    def test_result_includes_all_fields(self):
        """Each result has chunk_id, content, score, video_*, timestamp_url."""

    # ACL Integration
    def test_results_filtered_by_user_ownership(self):
        """User only sees own PRIVATE content in results."""

    def test_user_sees_only_own_private_content(self):
        """Other users' PRIVATE content excluded."""

    def test_user_sees_shared_content(self):
        """Content shared with user appears in results."""

    # Error Handling
    def test_embedding_failure_returns_500(self):
        """Embedding API error returns 500 with message."""

    def test_database_failure_returns_500(self):
        """pgvector query error returns 500."""
```

### 7. Auto-Ingestion Signal Tests

```python
# yt_sync/tests/test_signals.py
class TestAutoIngestionSignal:
    # Happy Path
    def test_signal_triggers_on_transcript_complete(self):
        """transcript_status=COMPLETED triggers signal."""

    def test_signal_queues_django_q_task(self):
        """Signal creates async Django-Q task."""

    def test_task_calls_ingestion_service(self):
        """Task invokes IngestionService.ingest_video()."""

    # Configuration
    def test_auto_ingest_disabled_no_task(self):
        """RAG_AUTO_INGEST=False prevents task creation."""

    def test_auto_ingest_enabled_creates_task(self):
        """RAG_AUTO_INGEST=True (default) creates task."""

    # Edge Cases
    def test_incomplete_transcript_no_trigger(self):
        """transcript_status=PENDING does not trigger."""

    def test_failed_transcript_no_trigger(self):
        """transcript_status=FAILED does not trigger."""

    def test_duplicate_save_idempotent(self):
        """Multiple saves don't create duplicate tasks."""
```

### 8. CLI Command Tests

```python
# rag/management/commands/tests/test_rag_ingest.py
class TestRagIngestCommand:
    def test_ingest_single_video(self):
        """--video-id=123 ingests one video."""

    def test_ingest_all_videos(self):
        """--all ingests all videos with transcripts."""

    def test_ingest_by_source(self):
        """--source=XYZ ingests videos from source."""

    def test_reingest_flag(self):
        """--reingest replaces existing chunks."""

    def test_dry_run_mode(self):
        """--dry-run shows what would be ingested."""

# rag/management/commands/tests/test_rag_search.py
class TestRagSearchCommand:
    def test_search_with_query(self):
        """python manage.py rag_search 'query' returns results."""

    def test_search_with_top_k(self):
        """--top-k=10 returns 10 results."""

    def test_search_output_format(self):
        """Output includes content, score, timestamp."""

    def test_search_as_user(self):
        """--user=123 searches as specific user."""
```

### Test Fixtures

```python
# conftest.py

@pytest.fixture
def sample_transcript_data():
    """Realistic transcript with timestamp gaps."""
    return [
        {"text": "Hello and welcome", "start": 0.0, "duration": 2.0},
        {"text": "to this tutorial", "start": 2.0, "duration": 1.5},
        # Gap of 3 seconds (> threshold)
        {"text": "Let's talk about authentication", "start": 6.5, "duration": 3.0},
        {"text": "which is a critical topic", "start": 9.5, "duration": 2.0},
    ]

@pytest.fixture
def video_with_transcript(db, sample_transcript_data):
    """Video model with completed transcript."""
    source = YouTubeSourceFactory(user=UserFactory())
    return VideoFactory(
        source=source,
        transcript_status="COMPLETED",
        transcript_data=sample_transcript_data,
    )

@pytest.fixture
def indexed_video(video_with_transcript, ingestion_service):
    """Video with chunks already indexed in pgvector."""
    ingestion_service.ingest_video(video_with_transcript)
    return video_with_transcript

@pytest.fixture
def multi_user_scenario(db):
    """Setup with multiple users and visibility levels for ACL tests."""
    owner = UserFactory()
    shared_user = UserFactory()
    other_user = UserFactory()

    return {
        "owner": owner,
        "shared_user": shared_user,
        "other_user": other_user,
        "private_video": VideoFactory(source__user=owner, visibility="private"),
        "shared_video": VideoFactory(
            source__user=owner,
            visibility="shared",
            shared_with_users=[str(shared_user.id)]
        ),
        "public_video": VideoFactory(source__user=owner, visibility="public"),
    }

@pytest.fixture
def mock_embedder():
    """Mock LiteLLM embedder for unit tests."""
    embedder = Mock(spec=LiteLLMEmbedder)
    embedder.embed.return_value = [
        Embedding(chunk_id="test:0", vector=[0.1] * 384, metadata={})
    ]
    embedder.embed_query.return_value = [0.1] * 384
    embedder.dimensions = 384
    return embedder
```

### Mocking Strategy

| Test Type | Embedder | Database | Django-Q |
|-----------|----------|----------|----------|
| Unit tests | Mocked | Mocked/SQLite | Mocked |
| Integration tests | Mocked | PostgreSQL + pgvector | Real |
| E2E tests | Real (local) | PostgreSQL + pgvector | Real |

---

## Implementation Plan

### Phase 1: Core Components (Tasks 1-3)

| Task | Description | Files |
|------|-------------|-------|
| 1 | TranscriptChunker implementation | `rag/chunkers/__init__.py`, `rag/chunkers/transcript.py` |
| 2 | LiteLLMEmbedder implementation | `rag/embedders/__init__.py`, `rag/embedders/litellm.py` |
| 3 | Add RAG configuration | `config/settings.py` |

### Phase 2: Services (Tasks 4-5)

| Task | Description | Files |
|------|-------------|-------|
| 4 | IngestionService implementation | `rag/services/__init__.py`, `rag/services/ingestion.py` |
| 5 | DefaultRetriever implementation | `rag/retrievers/__init__.py`, `rag/retrievers/default.py` |

### Phase 3: API & CLI (Tasks 6-8)

| Task | Description | Files |
|------|-------------|-------|
| 6 | Search API endpoint | `rag/api/views.py`, `rag/api/serializers.py`, `rag/api/urls.py` |
| 7 | CLI search command | `rag/management/commands/rag_search.py` |
| 8 | CLI ingest command | `rag/management/commands/rag_ingest.py` |

### Phase 4: Integration (Task 9)

| Task | Description | Files |
|------|-------------|-------|
| 9 | Auto-ingestion signal | `yt_sync/signals.py`, `yt_sync/apps.py` |

### Phase 5: Admin (Task 10)

| Task | Description | Files |
|------|-------------|-------|
| 10 | Admin search interface | `rag/admin.py` |

---

## Appendix

### Related Documentation

| Document | Purpose |
|----------|---------|
| FRD-001 | Feature requirements and acceptance criteria |
| TS-0001 | ACL system implementation details |
| `rag/core/interfaces.py` | Interface definitions |
| `rag/core/schemas.py` | Data model schemas |
| `rag/stores/pgvector.py` | Vector store implementation |

### Glossary

| Term | Definition |
|------|------------|
| Chunk | A segment of transcript text with timestamp metadata |
| Embedding | Vector representation of text for similarity search |
| ACL | Access Control List for visibility filtering |
| pgvector | PostgreSQL extension for vector similarity search |

---

**Document History**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-21 | Claude | Initial version from FRD-001 |
