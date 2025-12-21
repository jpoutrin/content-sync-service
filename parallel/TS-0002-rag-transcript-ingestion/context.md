# Context: TS-0002 RAG Transcript Ingestion & Search

## Project Overview

The Content Sync Service is a Django-based application for synchronizing and processing content from multiple sources (primarily YouTube). This tech spec implements a Retrieval-Augmented Generation (RAG) system for ingesting video transcripts, chunking them semantically, generating embeddings, storing them in a vector database, and enabling semantic search with ACL enforcement.

## Tech Stack

- **Framework**: Django 5.0
- **Python Version**: 3.12
- **Database**: PostgreSQL with pgvector extension (via Supabase)
- **Task Queue**: Django-Q (ORM backend for async task processing)
- **Vector Store**: PostgreSQL with pgvector extension
- **Embeddings**: LiteLLM (for API-based models) and sentence-transformers (for local models)
- **Testing**: pytest with pytest-django, factory-boy for fixtures
- **Configuration**: django-environ for environment variable management

## Existing Modules

### RAG Core Module (`rag/core/`)

**Interfaces** - All interfaces are abstract base classes with type hints:

- `ChunkerInterface`: Abstract interface for chunking documents
  - `chunk(document: Document) -> List[Chunk]`

- `EmbedderInterface`: Abstract interface for generating embeddings
  - `embed(texts: List[str]) -> List[Embedding]`
  - `embed_query(query: str) -> Embedding`

- `VectorStoreInterface`: Abstract interface for vector storage operations
  - `store(chunks: List[Chunk], embeddings: List[Embedding], metadata: Dict[str, Any])`
  - `search(query_embedding: Embedding, top_k: int, filters: Optional[ACLFilterSpec]) -> List[SearchResult]`

- `RetrieverInterface`: Abstract interface for retrieval operations
  - `retrieve(query: SearchQuery) -> List[SearchResult]`

**Schemas** (`rag/core/schemas.py`) - Pydantic models:

- `Document`: Represents a source document
  - `id: str`
  - `content: str`
  - `metadata: Dict[str, Any]`
  - `source_type: str`
  - `source_id: str`

- `Chunk`: Represents a chunk of a document
  - `id: str`
  - `content: str`
  - `document_id: str`
  - `chunk_index: int`
  - `metadata: Dict[str, Any]`

- `Embedding`: Represents a vector embedding
  - `vector: List[float]`
  - `model: str`
  - `dimensions: int`

- `SearchQuery`: Represents a search query
  - `query_text: str`
  - `top_k: int`
  - `filters: Optional[ACLFilterSpec]`
  - `acl_context: Optional[QueryACLContext]`

- `SearchResult`: Represents a search result
  - `chunk: Chunk`
  - `score: float`
  - `document_metadata: Dict[str, Any]`

**ACL System** (`rag/core/acl.py`):

- `Visibility` enum: `PUBLIC`, `PRIVATE`, `SHARED`
- `QueryACLContext`: Context for ACL enforcement
  - `user_id: Optional[str]`
  - `org_id: Optional[str]`
  - `user_roles: List[str]`

- `ACLFilterSpec`: Specification for ACL filtering
  - `visibility: Optional[Visibility]`
  - `owner_id: Optional[str]`
  - `org_id: Optional[str]`
  - `allowed_user_ids: Optional[List[str]]`

**Vector Store** (`rag/stores/pgvector.py`):

- `PgVectorStore`: PostgreSQL-based vector store with ACL filtering
  - Implements `VectorStoreInterface`
  - Uses raw SQL with pgvector operators for efficient vector search
  - ACL filtering happens at SQL level using WHERE clauses
  - Supports cosine similarity search with `<=>` operator
  - Table: `rag_vector_chunks` with columns:
    - `id`, `chunk_id`, `document_id`, `content`, `embedding`, `metadata`
    - `visibility`, `owner_id`, `org_id`, `allowed_user_ids`

### YouTube Sync Module (`yt_sync/`)

**Models** (`yt_sync/models.py`):

- `User`: Django user model with Supabase integration
  - `id: UUID`
  - `email: str`
  - `org_id: Optional[UUID]`

- `Source`: YouTube channel or playlist source
  - `id: UUID`
  - `source_type: str` (channel/playlist)
  - `source_id: str` (YouTube ID)
  - `visibility: str`
  - `owner: ForeignKey(User)`

- `Video`: YouTube video metadata
  - `id: UUID`
  - `video_id: str` (YouTube ID)
  - `title: str`
  - `description: str`
  - `transcript: Optional[str]`
  - `source: ForeignKey(Source)`
  - `visibility: str`
  - `owner: ForeignKey(User)`

## Dependencies

**Already Installed**:
- `litellm` - For API-based embedding models
- `pydantic>=2.0` - For data validation and schemas
- `psycopg2-binary` - PostgreSQL adapter
- `pgvector` - PostgreSQL vector extension client
- `django-q2` - Task queue
- `djangorestframework` - REST API framework
- `django-environ` - Environment variable management
- `pytest`, `pytest-django` - Testing framework
- `factory-boy` - Test fixture factory

**New Dependency to Add**:
- `sentence-transformers>=2.2.0` - For local embedding models (e.g., all-MiniLM-L6-v2)

## Authentication & Authorization

The service uses dual authentication via Django REST Framework:

1. **SupabaseAuthentication**: JWT-based authentication for Supabase users
   - Validates JWT tokens from Supabase
   - Extracts user context (user_id, org_id, roles)

2. **SessionAuthentication**: Cookie-based authentication for Django admin
   - Standard Django session authentication
   - Used for admin interface

All API endpoints use `SupabaseAuthentication` for access control. The ACL system enforces permissions at the query level based on the authenticated user's context.

## Configuration

The project uses `django-environ` for environment variables. Key settings:

- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anonymous key
- `SUPABASE_JWT_SECRET`: Secret for JWT validation
- `DATABASE_URL`: PostgreSQL connection string
- `EMBEDDING_MODEL`: Model name for embeddings (e.g., "all-MiniLM-L6-v2")
- `CHUNK_SIZE`: Default chunk size for transcript chunking
- `CHUNK_OVERLAP`: Overlap size between chunks

## Testing Strategy

- **Framework**: pytest with pytest-django
- **Fixtures**: factory-boy for creating test data
- **Test Structure**:
  - Unit tests for individual components (chunkers, embedders, retrievers)
  - Integration tests for services (ingestion, search)
  - API tests for endpoints
  - Security tests for ACL enforcement

**Key Test Scenarios**:
- ACL filtering prevents unauthorized access
- Chunk boundaries respect semantic units
- Embeddings are generated correctly
- Search results respect visibility rules
- Signal handlers trigger ingestion correctly

## File Organization

```
content-sync-service/
├── rag/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── interfaces.py          # Abstract interfaces
│   │   ├── schemas.py              # Pydantic models
│   │   └── acl.py                  # ACL system
│   ├── stores/
│   │   ├── __init__.py
│   │   └── pgvector.py             # Vector store (existing)
│   ├── chunkers/                   # NEW
│   │   ├── __init__.py
│   │   └── transcript.py           # Transcript chunker
│   ├── embedders/                  # NEW
│   │   ├── __init__.py
│   │   └── litellm.py              # LiteLLM embedder
│   ├── retrievers/                 # NEW
│   │   ├── __init__.py
│   │   └── default.py              # Default retriever
│   ├── services/                   # NEW
│   │   ├── __init__.py
│   │   └── ingestion.py            # Ingestion service
│   ├── api/                        # NEW
│   │   ├── __init__.py
│   │   ├── views.py                # API views
│   │   └── serializers.py          # DRF serializers
│   └── management/commands/        # NEW
│       ├── ingest_transcript.py    # CLI ingest
│       └── search_transcripts.py   # CLI search
├── yt_sync/
│   ├── models.py                   # Video, Source models
│   ├── signals.py                  # NEW - Auto-ingest signal
│   └── admin.py                    # Admin interface updates
└── tests/
    └── rag/
        ├── test_chunker.py
        ├── test_embedder.py
        ├── test_ingestion.py
        ├── test_retriever.py
        ├── test_search_api.py
        └── test_acl_security.py
```

## Implementation Notes

1. **Chunking Strategy**: Use semantic chunking with overlap to preserve context across chunk boundaries. Respect sentence boundaries and time markers in transcript format.

2. **Embedding Models**: Support both API-based (via LiteLLM) and local (via sentence-transformers) models. Configuration determines which to use.

3. **ACL Enforcement**: All search queries MUST include ACL context. The vector store applies ACL filters at SQL level for performance.

4. **Async Processing**: Ingestion should be async via Django-Q tasks. Signal handlers enqueue tasks rather than blocking.

5. **Error Handling**: All services should handle errors gracefully with proper logging and retry logic for transient failures.

6. **Performance**: Vector search should be optimized with proper indexes on pgvector columns and ACL fields.

## Wave Dependencies

- **Wave 1**: Core components (chunker, embedder, config) - No dependencies
- **Wave 2**: Services (ingestion, retriever) - Depends on Wave 1
- **Wave 3**: APIs and CLI - Depends on Wave 2
- **Wave 4**: Automation (signals, admin) - Depends on Wave 3
- **Wave 5**: Security testing - Depends on all previous waves

## Key Contracts

All contracts are defined in `contracts/` subdirectory:
- `types.py`: Shared type definitions and Pydantic models
- `api-schema.yaml`: OpenAPI schema for REST endpoints

Agents should import from contracts rather than redefining types.
