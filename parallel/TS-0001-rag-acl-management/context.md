# Context for TS-0001: RAG ACL Management

## Project Overview
Content Sync Service - Django-based content synchronization service using PostgreSQL (Supabase) and Django-Q.

## Tech Stack
- Python 3.12
- Django 5.0+
- PostgreSQL with pgvector extension v0.8.0
- Pydantic 2.5+ for schemas

## Existing Codebase State

### RAG Core Module (rag/core/)
- **schemas.py**: Has Document, Chunk, SearchQuery, SearchResult, Embedding models - NO ACL fields yet
- **interfaces.py**: Has VectorStoreInterface with basic upsert/search/delete - NO ACL methods yet
- **__init__.py**: Exports all schemas and interfaces

### RAG Stores Module (rag/stores/)
- Directory does NOT exist - must be created

### YouTube Sync Module (yt_sync/)
- **models.py**: Has User, Source, Video, ProcessedContent Django models

## Dependencies Already Present
- pydantic>=2.5.0
- psycopg2-binary>=2.9.9
- Django>=5.0

## Key Constraints
1. Existing schemas must be MODIFIED, not replaced
2. All existing fields must be preserved
3. Backward compatibility required
4. Database uses Supabase PostgreSQL with pgvector v0.8.0 enabled

## Related Documents
- Tech Spec: tech-specs/approved/TS-0001-rag-acl-management.md
- RFC-0001: RAG ACL Management (APPROVED)
- RFC-0002: Vector Storage for RAG - Phase 1 (APPROVED)
