# Feature Requirements Document (FRD)

**Feature Name**: RAG Transcript Ingestion & Search
**Product**: Content Sync Service
**Document Version**: 1.0
**Last Updated**: 2025-12-20
**Author**: Claude
**Status**: Approved
**Feature ID**: FRD-001
**Epic Link**: N/A

## Executive Summary

### Feature Overview
Enable feeding YouTube video transcripts into the RAG (Retrieval-Augmented Generation) system and searching content via semantic similarity. The feature supports topic search, Q&A, and content discovery with timestamp-based video position linking, allowing users to jump directly to relevant moments in videos.

### Business Value
- **Content Discovery**: Find specific topics across all indexed video transcripts
- **Q&A Capability**: Ask natural language questions and find relevant transcript segments
- **Time Savings**: Jump directly to relevant video moments instead of watching entire videos
- **Knowledge Base**: Build a searchable knowledge base from video content

### Implementation Complexity
**Estimated Effort**: Medium (2-3 weeks)
**Risk Level**: Low (well-architected foundation exists)
**Priority**: P1-High

## Context & Problem Statement

### Current State
- YouTube transcripts are fetched and stored in the `Video` model (`transcript_text`, `transcript_data`)
- RAG infrastructure exists: ACL system, schemas, PgVectorStore, Django bridge
- Missing: chunking, embedding generation, ingestion pipeline, and search interface

### Problem to Solve
Users cannot search through their video transcript content. To find specific information, they must manually watch videos or read through entire transcripts. There's no way to semantically search across all video content.

### Impact of Not Implementing
- Users waste time manually searching through video content
- Valuable knowledge locked in video transcripts remains inaccessible
- No ability to answer questions based on video content
- Poor content discoverability across video library

## Feature Objectives & Success Metrics

### Objectives
1. Automatically ingest transcripts into RAG when videos are processed
2. Enable semantic search across all transcript content
3. Provide timestamp linking so users can jump to specific video moments
4. Support both API and CLI access to search functionality
5. Provide admin interface for testing and managing indexed content

### Success Metrics
| Metric | Target |
|--------|--------|
| Search latency (p95) | < 500ms |
| Ingestion success rate | > 99% |
| Search relevance (top-5 accuracy) | > 80% |
| Chunk generation per video | 10-100 chunks depending on length |

### Acceptance Criteria

**AC1: Transcript Ingestion**
- Given a video with `transcript_status=COMPLETED`
- When the transcript is saved
- Then chunks are automatically created, embedded, and stored in pgvector

**AC2: Semantic Search**
- Given indexed transcripts
- When a user searches with a query
- Then relevant chunks are returned with similarity scores

**AC3: Timestamp Linking**
- Given a search result
- When the result is returned
- Then it includes `start_time`, `end_time`, and `timestamp_url` for video linking

**AC4: ACL Enforcement**
- Given a user searching transcripts
- When results are returned
- Then only transcripts the user has access to are shown

**AC5: Admin Search**
- Given an admin user
- When using the admin search interface
- Then they can search all content with ACL bypass for debugging

## User Stories & Scenarios

### Primary User Story
**As a** content consumer
**I want to** search through my video transcripts
**So that** I can quickly find and jump to relevant content without watching entire videos

### Usage Scenarios

**Scenario 1: Topic Search**
1. User has 50 indexed videos about programming
2. User searches "how to handle authentication"
3. System returns top 5 chunks mentioning authentication
4. Each result shows video title, content snippet, and timestamp link
5. User clicks timestamp link and jumps to that moment in the video

**Scenario 2: Q&A Search**
1. User searches "what did the speaker say about database migrations?"
2. System semantically matches the query to relevant transcript segments
3. Results are ranked by similarity score
4. User reviews the most relevant segments

**Scenario 3: Admin Debugging**
1. Admin accesses `/admin/rag/search/`
2. Admin enters a test query
3. Results show all matching content (ACL bypassed)
4. Admin can verify ingestion worked correctly

### Edge Cases
- Video with no transcript (skip ingestion, log warning)
- Very short transcript < 100 chars (create single chunk)
- Very long transcript > 100k chars (batch processing)
- Non-English transcript (handled by multilingual embedding model)
- Duplicate video re-indexed (upsert behavior replaces existing chunks)

## Functional Requirements

### Core Functionality

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | Chunk transcripts by timestamp-based segments | Must Have |
| FR2 | Generate embeddings using configurable provider | Must Have |
| FR3 | Store chunks with ACL metadata in pgvector | Must Have |
| FR4 | Search with semantic similarity | Must Have |
| FR5 | Filter search by ACL context | Must Have |
| FR6 | Return timestamp URLs for video linking | Must Have |
| FR7 | Auto-ingest on transcript completion | Must Have |
| FR8 | Manual ingestion via CLI | Should Have |
| FR9 | Admin search interface | Should Have |
| FR10 | Admin ingestion controls | Should Have |

### Input/Output Specifications

**Ingestion Input:**
```python
Video model instance with:
- transcript_text: str  # Full transcript text
- transcript_data: list[{text: str, start: float, duration: float}]  # Timed segments
- source.user: User  # For ACL owner_id
```

**Ingestion Output:**
```python
int  # Number of chunks indexed
```

**Search Input:**
```
GET /api/rag/search?q=<query>&top_k=5&min_score=0.5
```

**Search Output:**
```json
{
  "query": "search text",
  "results": [
    {
      "chunk_id": "video:123:chunk:0",
      "content": "transcript segment text...",
      "score": 0.89,
      "video_id": "abc123",
      "video_title": "Video Title",
      "video_url": "https://youtube.com/watch?v=abc123",
      "start_time": 45.2,
      "end_time": 62.8,
      "timestamp_url": "https://youtube.com/watch?v=abc123&t=45"
    }
  ],
  "total": 5
}
```

### Business Rules
1. Default visibility is PRIVATE (only owner can search)
2. Chunks inherit ACL from parent document
3. Minimum chunk size: 100 characters
4. Maximum chunk size: 1000 characters (soft limit)
5. Gap threshold for chunk boundary: 2 seconds
6. Auto-ingestion can be disabled via `RAG_AUTO_INGEST=False`

### Data Requirements
- Existing: `rag_embeddings` table with pgvector extension
- Existing: Video model with transcript data
- New: Chunk metadata includes `start_time`, `end_time`, `video_title`, `video_url`

## Technical Specifications

### API Design

**Search Endpoint:**
```
GET /api/rag/search

Query Parameters:
- q (required): Search query text
- top_k (optional): Number of results (default: 5, max: 100)
- min_score (optional): Minimum similarity score (0.0-1.0)

Headers:
- Authorization: Bearer <token> (required)

Response: 200 OK
{
  "query": "...",
  "results": [...],
  "total": 5
}

Errors:
- 400: Missing query parameter
- 401: Not authenticated
- 500: Embedding/search failure
```

### Data Model Changes
No new Django models required. Uses existing:
- `yt_sync.Video` - source of transcript data
- `rag_embeddings` table (raw SQL via PgVectorStore)

Chunk metadata stored in `metadata` JSONB column:
```json
{
  "start_time": 45.2,
  "end_time": 62.8,
  "segment_count": 5,
  "video_title": "...",
  "video_url": "...",
  "youtube_video_id": "..."
}
```

### System Architecture Impact
- Adds async task for ingestion (Django-Q)
- Adds signal listener on Video model
- No new database tables (uses existing pgvector table)
- Integrates with existing ACL system

### Integration Points
| System | Integration Type | Purpose |
|--------|-----------------|---------|
| PgVectorStore | Direct call | Store/search embeddings |
| LiteLLM | API call | Generate embeddings |
| Django-Q | Task queue | Async ingestion |
| Django Admin | Custom views | Admin interface |

### Performance Requirements
| Metric | Requirement |
|--------|-------------|
| Search latency | < 500ms p95 |
| Ingestion throughput | > 10 videos/minute |
| Embedding batch size | 50 chunks max per API call |
| Vector index type | IVFFLAT with cosine similarity |

## User Interface & Experience

### UI Components

**Admin Search Interface (`/admin/rag/search/`):**
- Query input field
- Top-K selector (dropdown: 5, 10, 20, 50)
- Min-score slider (0.0-1.0)
- Search button
- Results table: Content, Score, Video, Timestamp Link

**Admin Embeddings List (`/admin/rag/embeddings/`):**
- List view: Video title, Chunk count, Created date
- Filters: By video, by date range
- Actions: Delete selected, Re-index selected

### User Flow
1. User authenticates
2. User sends search query via API
3. System embeds query
4. System searches pgvector with ACL filter
5. System formats results with video metadata
6. User receives ranked results with timestamp links

### Mockups/Wireframes
N/A - API-first design, admin interface follows Django admin patterns

### Interaction Patterns
- Synchronous search via REST API
- Asynchronous ingestion via Django-Q tasks
- Real-time admin actions with status feedback

## Implementation Details

### Technical Approach
1. **Chunking**: Timestamp-based segmentation respecting natural pauses
2. **Embedding**: LiteLLM abstraction for provider switching
3. **Storage**: Existing PgVectorStore with ACL columns
4. **Search**: Cosine similarity with ACL filtering at SQL level
5. **Integration**: Django signals for auto-ingestion

### Code Structure

**New Packages:**
```
rag/
├── chunkers/
│   ├── __init__.py
│   └── transcript.py        # TranscriptChunker
├── embedders/
│   ├── __init__.py
│   └── litellm.py           # LiteLLMEmbedder
├── retrievers/
│   ├── __init__.py
│   └── default.py           # DefaultRetriever
├── services/
│   ├── __init__.py
│   └── ingestion.py         # IngestionService
├── api/
│   ├── __init__.py
│   ├── views.py             # Search view
│   ├── serializers.py       # DRF serializers
│   └── urls.py              # URL routing
├── management/
│   └── commands/
│       ├── rag_search.py    # CLI search
│       └── rag_ingest.py    # CLI ingest
└── admin.py                 # Admin views

yt_sync/
└── signals.py               # Auto-ingestion signal
```

### Database Changes
None - uses existing `rag_embeddings` table created by `0001_create_rag_embeddings.py`

### Configuration Requirements

Add to `config/settings.py`:
```python
# RAG Configuration
RAG_EMBEDDING_PROVIDER = env('RAG_EMBEDDING_PROVIDER', default='local')
RAG_EMBEDDING_MODEL = env('RAG_EMBEDDING_MODEL', default='sentence-transformers/all-MiniLM-L6-v2')
RAG_AUTO_INGEST = env.bool('RAG_AUTO_INGEST', default=True)

# Chunking configuration
RAG_CHUNK_GAP_THRESHOLD = env.float('RAG_CHUNK_GAP_THRESHOLD', default=2.0)
RAG_CHUNK_MAX_CHARS = env.int('RAG_CHUNK_MAX_CHARS', default=1000)
RAG_CHUNK_MIN_CHARS = env.int('RAG_CHUNK_MIN_CHARS', default=100)
```

Environment variables:
```bash
# Development (local embeddings, no API costs)
RAG_EMBEDDING_PROVIDER=local
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Production (OpenAI embeddings)
RAG_EMBEDDING_PROVIDER=openai
RAG_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-...
```

## Task Breakdown

### Development Tasks

**Phase 1: Core Components**
- [ ] Create `rag/chunkers/__init__.py`
- [ ] Create `rag/chunkers/transcript.py` - TranscriptChunker implementation
- [ ] Create `rag/embedders/__init__.py`
- [ ] Create `rag/embedders/litellm.py` - LiteLLMEmbedder implementation
- [ ] Add RAG configuration to `config/settings.py`

**Phase 2: Ingestion Service**
- [ ] Create `rag/services/__init__.py`
- [ ] Create `rag/services/ingestion.py` - IngestionService
- [ ] Create `rag/retrievers/__init__.py`
- [ ] Create `rag/retrievers/default.py` - DefaultRetriever

**Phase 3: API & CLI**
- [ ] Create `rag/api/__init__.py`
- [ ] Create `rag/api/views.py` - Search endpoint
- [ ] Create `rag/api/serializers.py` - Request/response serializers
- [ ] Create `rag/api/urls.py` - URL routing
- [ ] Update `config/urls.py` - Add RAG routes
- [ ] Create `rag/management/commands/rag_search.py`
- [ ] Create `rag/management/commands/rag_ingest.py`

**Phase 4: Integration**
- [ ] Create `yt_sync/signals.py` - Auto-ingestion signal
- [ ] Update `yt_sync/apps.py` - Connect signals

**Phase 5: Admin Views**
- [ ] Update `rag/admin.py` - Search interface and ingestion controls

### Testing Requirements
- [ ] Unit tests for TranscriptChunker
- [ ] Unit tests for LiteLLMEmbedder (mocked)
- [ ] Unit tests for IngestionService
- [ ] Integration tests for search API
- [ ] Integration tests for auto-ingestion signal

### Documentation Tasks
- [ ] Update CLAUDE.md with RAG commands
- [ ] API documentation for search endpoint
- [ ] Admin user guide for RAG features

### Deployment Tasks
- [ ] Add `sentence-transformers` to dev dependencies (optional)
- [ ] Configure OPENAI_API_KEY in production
- [ ] Enable pgvector extension in Supabase (if not already)

## Dependencies & Constraints

### Technical Dependencies
| Dependency | Version | Purpose |
|------------|---------|---------|
| litellm | >=1.0.0 | Embedding generation |
| pgvector | PostgreSQL ext | Vector similarity search |
| djangorestframework | existing | REST API |
| django-q | existing | Async task queue |

### External Dependencies
- OpenAI API (production) or local sentence-transformers (development)
- PostgreSQL with pgvector extension (via Supabase)

### Constraints
- Embedding dimensions must match between provider and vector store
- Local embeddings require ~500MB model download
- OpenAI embeddings incur per-token costs

## Security & Compliance

### Security Considerations
- ACL filtering at SQL level prevents unauthorized access
- API requires authentication (SupabaseAuthentication or SessionAuthentication)
- Admin ACL bypass limited to staff users only
- No sensitive data stored in embeddings (just transcript text)

### Data Privacy
- Transcripts processed by embedding API (OpenAI or local)
- When using OpenAI, transcript content is sent to their API
- Consider data processing agreements for production use
- GDPR: `delete_by_owner()` supports right to be forgotten

### Compliance Requirements
- Standard Django authentication/authorization
- Audit logging via existing Django patterns

## Testing Strategy

### Unit Tests
```python
# rag/chunkers/tests/test_transcript.py
- test_chunk_by_timestamp_gaps
- test_chunk_respects_max_chars
- test_chunk_minimum_size
- test_chunk_metadata_includes_timestamps
- test_empty_transcript_returns_empty_list
- test_single_segment_creates_one_chunk

# rag/embedders/tests/test_litellm.py
- test_embed_single_text
- test_embed_batch
- test_provider_switching
- test_dimension_mapping
```

### Integration Tests
```python
# rag/api/tests/test_search.py
- test_search_requires_auth
- test_search_returns_results
- test_search_respects_acl
- test_search_filters_by_min_score
- test_search_limits_by_top_k

# yt_sync/tests/test_signals.py
- test_auto_ingestion_on_transcript_complete
- test_no_ingestion_when_disabled
```

### User Acceptance Tests
1. Index a video transcript
2. Search for content mentioned in the video
3. Verify timestamp link works
4. Verify only owned content is returned

### Performance Tests
- Search latency under load (100 concurrent requests)
- Ingestion throughput (batch of 100 videos)

## Rollout Plan

### Feature Flags
- `RAG_AUTO_INGEST` - Enable/disable automatic ingestion

### Rollout Phases
1. **Phase 1**: Deploy with auto-ingest disabled, test CLI manually
2. **Phase 2**: Enable auto-ingest for new videos only
3. **Phase 3**: Backfill existing videos via management command

### Rollback Strategy
- Disable `RAG_AUTO_INGEST=False`
- Existing search returns empty results (graceful degradation)
- No data loss (transcripts remain in Video model)

## Monitoring & Analytics

### Key Metrics to Track
- Search request count and latency
- Ingestion success/failure rate
- Chunk count per video
- Top search queries

### Logging Requirements
```python
logger.info(f"Indexed {chunk_count} chunks for video {video.id}")
logger.warning(f"No transcript data for video {video.id}")
logger.error(f"Embedding failed for video {video.id}: {error}")
```

### Analytics Events
- `rag.search` - Query text, result count, latency
- `rag.ingest` - Video ID, chunk count, success/failure
- `rag.admin.search` - Admin search usage

## Documentation & Communication

### Technical Documentation
- API reference in OpenAPI/Swagger format
- Architecture diagram showing data flow
- Configuration guide for embedding providers

### User Documentation
- How to search transcripts via API
- How to use CLI commands
- Admin interface guide

### Internal Communication
N/A - Single user project

### Training Materials
N/A - Self-service documentation

## Business Deliverables

### Demo Scenarios
1. **Basic Search**: Search for a topic, show results with timestamps
2. **Video Jump**: Click timestamp link, video opens at exact position
3. **Admin Control**: Show admin re-indexing a video

### Stakeholder Reports
N/A - Personal project

### Success Criteria Validation
- [ ] Can search transcripts via API
- [ ] Results include timestamp links
- [ ] Auto-ingestion works on new videos
- [ ] Admin interface functional
- [ ] ACL filtering works correctly

## Open Questions & Decisions

### Open Questions
None - all questions resolved during planning.

### Decisions Needed
None - all decisions made.

### Assumptions
1. pgvector extension is already enabled in Supabase
2. LiteLLM handles both OpenAI and HuggingFace models
3. Existing PgVectorStore implementation is correct
4. Django-Q is configured and running

## Appendix

### Related Features
- YouTube transcript fetching (`yt_sync`)
- AI analysis (`ProcessedContent`)

### Technical References
| File | Purpose |
|------|---------|
| `rag/core/interfaces.py` | ChunkerInterface, EmbedderInterface definitions |
| `rag/core/schemas.py` | Document, Chunk, Embedding schemas |
| `rag/stores/pgvector.py` | PgVectorStore implementation |
| `yt_sync/rag_bridge.py` | build_acl_context, get_vector_store |
| `yt_sync/services/transcript.py` | Transcript fetching service |
| `yt_sync/models.py` | Video model with transcript fields |

### Business Context
This feature enables semantic search over video transcript content, transforming passive video content into an actively searchable knowledge base.

---

**Document History**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-20 | Claude | Initial version |
