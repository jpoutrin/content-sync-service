---
id: task-005
component: rag-migration-embeddings-table
wave: 3
deps: [task-004]
blocks: []
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/database-schema.sql]
---
# task-005: RAG Migration Embeddings Table

## Scope
CREATE: rag/migrations/0001_initial.py
MODIFY: []
BOUNDARY: rag/models.py

## Requirements
- Create Django migration for rag_embeddings table
- Use RunSQL operation to execute raw SQL (pgvector not supported by Django ORM)
- Enable pgvector extension: CREATE EXTENSION IF NOT EXISTS vector
- Create table with columns:
  - id (UUID PK)
  - chunk_id (VARCHAR UNIQUE)
  - document_id (VARCHAR)
  - content (TEXT)
  - embedding (vector(1536))
  - metadata (JSONB)
  - owner_id (VARCHAR)
  - visibility (VARCHAR)
  - shared_with_users (VARCHAR[])
  - shared_with_groups (VARCHAR[])
  - tenant_id (VARCHAR nullable)
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)
- Create HNSW index on embedding column for vector similarity
- Create B-tree indexes on: owner_id, visibility, document_id, tenant_id
- Create GIN indexes on: shared_with_users, shared_with_groups arrays

## Checklist
- [ ] Migration class inherits from django.db.migrations.Migration
- [ ] dependencies = [] (first migration for rag app)
- [ ] Uses migrations.RunSQL for forward and reverse operations
- [ ] Reverse SQL includes DROP TABLE IF EXISTS rag_embeddings
- [ ] pgvector extension creation is idempotent
- [ ] HNSW index uses vector_cosine_ops for cosine similarity
- [ ] tenant_id index is partial (WHERE tenant_id IS NOT NULL)
- [ ] Default values: metadata='{}', visibility='private', shared arrays='{}'
- [ ] created_at and updated_at use NOW() default
