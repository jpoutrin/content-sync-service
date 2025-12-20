---
id: task-006
component: database-migration
wave: 3
deps: []
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: []
---
# task-006: Create Database Migration for RAG Embeddings Table

## Scope
CREATE: rag/migrations/0001_create_rag_embeddings.py
MODIFY: (none)
BOUNDARY: rag/core/*, rag/stores/*, yt_sync/*

## Requirements
- Create Django migration file with raw SQL (not ORM model)
- Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector`
- Create `rag_embeddings` table with columns:
  - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `chunk_id` VARCHAR(255) UNIQUE NOT NULL
  - `document_id` VARCHAR(255) NOT NULL
  - `content` TEXT NOT NULL
  - `embedding` vector(1536) NOT NULL
  - `metadata` JSONB DEFAULT '{}'
  - `owner_id` VARCHAR(255) NOT NULL
  - `visibility` VARCHAR(50) NOT NULL DEFAULT 'PRIVATE'
  - `shared_with_users` TEXT[] DEFAULT '{}'
  - `shared_with_groups` TEXT[] DEFAULT '{}'
  - `tenant_id` VARCHAR(255)
  - `created_at` TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
  - `updated_at` TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
- Create HNSW index on embedding column: `CREATE INDEX idx_rag_embeddings_embedding ON rag_embeddings USING hnsw (embedding vector_cosine_ops)`
- Create B-tree indexes:
  - `CREATE INDEX idx_rag_embeddings_owner ON rag_embeddings (owner_id)`
  - `CREATE INDEX idx_rag_embeddings_visibility ON rag_embeddings (visibility)`
  - `CREATE INDEX idx_rag_embeddings_document ON rag_embeddings (document_id)`
  - `CREATE INDEX idx_rag_embeddings_tenant ON rag_embeddings (tenant_id) WHERE tenant_id IS NOT NULL` (partial index)
- Create GIN indexes for array columns:
  - `CREATE INDEX idx_rag_embeddings_shared_users ON rag_embeddings USING gin (shared_with_users)`
  - `CREATE INDEX idx_rag_embeddings_shared_groups ON rag_embeddings USING gin (shared_with_groups)`
- Migration must be reversible (include DROP statements in reverse operation)
- Use idempotent operations (IF NOT EXISTS, IF EXISTS)

## Checklist
- [ ] Migration is reversible (has reverse_sql or operations)
- [ ] pgvector extension enabled with IF NOT EXISTS
- [ ] Table created with all required columns
- [ ] chunk_id has UNIQUE constraint
- [ ] HNSW index uses vector_cosine_ops
- [ ] B-tree indexes created for owner_id, visibility, document_id, tenant_id
- [ ] tenant_id index is partial (WHERE tenant_id IS NOT NULL)
- [ ] GIN indexes created for shared_with_users and shared_with_groups
- [ ] Timestamps have default values
- [ ] No files modified outside scope
