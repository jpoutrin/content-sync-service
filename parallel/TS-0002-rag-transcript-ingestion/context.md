# RAG Transcript Ingestion & Search - Parallel Development Context

## Tech Spec Reference
- **ID**: TS-0002
- **Title**: RAG Transcript Ingestion & Search
- **Source**: tech-specs/approved/TS-0002-rag-transcript-ingestion.md

## Project Overview
Django-based content synchronization service implementing transcript ingestion and semantic search capabilities for the RAG module.

## Tech Stack
- **Framework**: Django 5.0
- **Python**: 3.12
- **Database**: PostgreSQL (via Supabase) with pgvector extension
- **Task Queue**: Django-Q (ORM backend)
- **API**: Django REST Framework

## Existing Infrastructure (from TS-0001)

### Core Interfaces (rag/core/interfaces.py)
- `ChunkerInterface`: Abstract base for document chunking strategies
- `EmbedderInterface`: Abstract base for embedding generation
  - `embed(text: str) -> list[float]` - single text embedding
  - `embed_batch(texts: list[str]) -> list[list[float]]` - batch embedding
- `VectorStoreInterface`: Abstract base for vector storage and search
- `RetrieverInterface`: High-level interface combining embedding and search

### Schemas (rag/core/schemas.py)
- `Document`: Source document with ACL fields (owner_id, visibility, shared_with_users, shared_with_groups, tenant_id)
- `Chunk`: Text segment with inherited ACL fields, uses `Chunk.from_document()` for ACL inheritance
- `Embedding`: Vector representation with chunk_id, vector, model, dimensions
- `SearchQuery`: Query with text, top_k, min_score, filters, acl_context
- `SearchResult`: Result with chunk, score, document_metadata

### ACL System (rag/core/acl.py)
- `Visibility`: Enum (PRIVATE, SHARED, INTERNAL, PUBLIC)
- `QueryACLContext`: Context with principal_id, member_of_groups, tenant_id, bypass_acl
- `ACLFilterSpec`: SQL filter generation for pgvector ACL filtering

### Vector Store (rag/stores/pgvector.py)
- `PgVectorStore`: PostgreSQL pgvector implementation with ACL-filtered search
- Uses cosine distance for similarity
- Supports upsert, batch operations, and document deletion

## YouTube Sync Models (yt_sync/models.py)

### User Model
- UUID primary key
- Custom user model

### Source Model
- `id`: UUID primary key
- `user`: ForeignKey to User (owner)
- `type`: CHANNEL or PLAYLIST
- `youtube_id`: Channel/playlist ID
- `title`, `url`, `status`

### Video Model
- `id`: UUID primary key
- `source`: ForeignKey to Source
- `youtube_video_id`: Unique YouTube video ID
- `title`, `url`, `duration`, `published_at`
- `transcript_text`: Full transcript text
- `transcript_data`: JSONField with timed segments [{"text": str, "start": float, "duration": float}]
- `transcript_status`: PENDING, PROCESSING, COMPLETED, FAILED

## Key Implementation Notes

### Chunk ID Convention
```
video:{video_pk}:chunk:{chunk_index}
Example: video:123e4567-e89b-12d3-a456-426614174000:chunk:0
```

### Document ID Convention
```
video:{video_pk}
Example: video:123e4567-e89b-12d3-a456-426614174000
```

### ACL Inheritance
Chunks inherit ACL fields from parent Document using `Chunk.from_document()`:
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

### Transcript Data Format
```python
[
    {"text": "Hello and welcome", "start": 0.0, "duration": 2.0},
    {"text": "to this tutorial", "start": 2.0, "duration": 1.5},
    {"text": "Let's talk about", "start": 6.5, "duration": 3.0},  # gap > 2.0s
]
```

### Embedding Dimensions
- Local (sentence-transformers/all-MiniLM-L6-v2): 384 dimensions
- OpenAI (text-embedding-3-small): 1536 dimensions

## Configuration Settings (to be added in task-003)
```python
RAG_EMBEDDING_PROVIDER = env('RAG_EMBEDDING_PROVIDER', default='local')
RAG_EMBEDDING_MODEL = env('RAG_EMBEDDING_MODEL', default='sentence-transformers/all-MiniLM-L6-v2')
RAG_AUTO_INGEST = env.bool('RAG_AUTO_INGEST', default=True)
RAG_CHUNK_GAP_THRESHOLD = env.float('RAG_CHUNK_GAP_THRESHOLD', default=2.0)
RAG_CHUNK_MAX_CHARS = env.int('RAG_CHUNK_MAX_CHARS', default=1000)
RAG_CHUNK_MIN_CHARS = env.int('RAG_CHUNK_MIN_CHARS', default=100)
RAG_EMBEDDING_BATCH_SIZE = env.int('RAG_EMBEDDING_BATCH_SIZE', default=50)
```

## Directory Structure
```
rag/
├── core/                    # Existing - interfaces, schemas, ACL
│   ├── __init__.py
│   ├── acl.py
│   ├── interfaces.py
│   └── schemas.py
├── stores/                  # Existing - PgVectorStore
│   └── pgvector.py
├── chunkers/                # NEW - task-001
│   ├── __init__.py
│   ├── transcript.py
│   └── tests/
├── embedders/               # NEW - task-002
│   ├── __init__.py
│   ├── litellm.py
│   └── tests/
├── services/                # NEW - task-004
│   ├── __init__.py
│   ├── ingestion.py
│   └── tests/
├── retrievers/              # NEW - task-005
│   ├── __init__.py
│   ├── default.py
│   └── tests/
├── api/                     # NEW - task-006
│   ├── __init__.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── tests/
├── management/              # NEW - tasks 007-008
│   └── commands/
│       ├── rag_search.py
│       ├── rag_ingest.py
│       └── tests/
├── admin.py                 # MODIFY - task-010
└── tests/                   # NEW - task-011
    ├── __init__.py
    ├── conftest.py
    └── test_acl_security.py

yt_sync/
├── signals.py               # NEW - task-009
├── apps.py                  # MODIFY - task-009
└── tests/
    └── test_signals.py      # NEW - task-009

config/
├── settings.py              # MODIFY - task-003
└── urls.py                  # MODIFY - task-006
```
