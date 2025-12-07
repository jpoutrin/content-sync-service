---
rfc_id: RFC-0002
title: Vector Storage for RAG - Phase 1
status: APPROVED
author: Claude
reviewers:
  - name: Jeremie
    status: approved
created: 2025-12-06
last_updated: 2025-12-06
decision_date: 2025-12-06
related_prds: []
related_rfcs:
  - RFC-0001 (RAG ACL Management)
---

# RFC-0002: Vector Storage for RAG - Phase 1

## Overview

This RFC evaluates vector storage options for the Phase 1 RAG implementation in the Content Sync Service. The system needs to store and search YouTube video transcript embeddings for semantic retrieval.

Phase 1 focuses on a **minimal viable implementation** for a single-user or small-team use case, prioritizing simplicity and cost-effectiveness over scale.

## Table of Contents

- [Background & Context](#background--context)
- [Problem Statement](#problem-statement)
- [Goals & Non-Goals](#goals--non-goals)
- [Evaluation Criteria](#evaluation-criteria)
- [Options Analysis](#options-analysis)
- [Recommendation](#recommendation)
- [Technical Design](#technical-design)
- [Implementation Plan](#implementation-plan)
- [Open Questions](#open-questions)
- [Decision Record](#decision-record)

---

## Background & Context

### Current State

- **Database**: PostgreSQL via Supabase (local or cloud)
- **Task Queue**: Django-Q with ORM backend
- **RAG Module**: Basic schemas and interfaces defined in `rag/core/`
- **No vector storage** implementation exists yet
- **ACL Design**: RFC-0001 approved - vector store must support metadata filtering

### Project Characteristics

| Characteristic | Value |
|---------------|-------|
| Data Source | YouTube video transcripts |
| Expected Documents (Phase 1) | 100-1,000 videos |
| Chunks per Video | ~50-200 (based on transcript length) |
| Total Vectors (Phase 1) | 5,000-200,000 |
| Query Pattern | Low volume (<100 queries/day) |
| Embedding Model | TBD (likely OpenAI or Sentence Transformers) |
| Embedding Dimensions | 384-1536 (model dependent) |

### Infrastructure Constraints

- **Already using Supabase** for PostgreSQL
- **No Redis** (removed in favor of Django-Q ORM backend)
- **No Kubernetes** - simple deployment model
- **Budget**: Cost-sensitive for Phase 1

### Glossary

| Term | Definition |
|------|------------|
| Vector Store | Database optimized for similarity search on embeddings |
| ANN | Approximate Nearest Neighbor - algorithm for fast similarity search |
| HNSW | Hierarchical Navigable Small World - popular ANN index type |
| IVF | Inverted File Index - another ANN algorithm |
| pgvector | PostgreSQL extension for vector similarity search |
| Embedding | Dense vector representation of text for semantic similarity |

---

## Problem Statement

### The Problem

The RAG module has interfaces defined (`VectorStoreInterface`) but no implementation. To enable semantic search over YouTube transcripts, we need to select and implement a vector storage solution.

### Constraints from RFC-0001

The ACL system design requires:
- **Metadata filtering** combined with vector search
- **OR conditions** for visibility checks (owner, shared_with, visibility level)
- **delete_by_owner** capability for GDPR compliance
- **update_document_acl** to modify ACL without re-indexing vectors

### Scale Considerations

Phase 1 is intentionally small-scale:
- Single user or small team
- Hundreds to thousands of documents
- Low query volume
- Development and validation focus

---

## Goals & Non-Goals

### Goals (In Scope)

1. Select a vector storage solution for Phase 1
2. Implement `VectorStoreInterface` from `rag/core/interfaces.py`
3. Support metadata filtering for ACL (per RFC-0001)
4. Enable similarity search with configurable top_k
5. Keep operational complexity low
6. Minimize additional infrastructure

### Non-Goals (Out of Scope)

1. Horizontal scaling or sharding
2. Multi-region deployment
3. Sub-millisecond latency optimization
4. Support for millions of vectors
5. Real-time index updates at scale

### Success Criteria

- [ ] Vector store implementation passes interface contract
- [ ] Metadata filtering supports ACL patterns from RFC-0001
- [ ] Insert + search latency < 500ms for Phase 1 scale
- [ ] No additional infrastructure required beyond current stack
- [ ] Cost < $50/month for Phase 1 workload

---

## Evaluation Criteria

| Criterion | Weight | Description | Phase 1 Threshold |
|-----------|--------|-------------|-------------------|
| Operational Simplicity | High | Minimal infrastructure/ops burden | Self-managed or Supabase-integrated |
| Metadata Filtering | High | Support for ACL filter patterns | OR conditions, list contains |
| Cost | High | Monthly cost for Phase 1 scale | < $50/month |
| Implementation Effort | High | Time to implement and test | < 1 week |
| Integration | Medium | Compatibility with existing stack | Works with Django/Supabase |
| Query Performance | Medium | Search latency at Phase 1 scale | < 200ms p95 |
| Future Scalability | Low | Path to scale if needed | Migration path exists |

---

## Options Analysis

### Option 1: Supabase pgvector

**Description**

Use PostgreSQL's pgvector extension through Supabase. Supabase includes pgvector support out of the box, enabling vector storage and similarity search directly in the existing database.

**Technical Details**

- **Index Type**: HNSW (default) or IVFFlat
- **Max Dimensions**: No hard limit (recommend < 2000)
- **Metadata**: Native PostgreSQL columns/JSONB
- **Filtering**: SQL WHERE clauses combined with vector search

**Advantages**

- Zero additional infrastructure - uses existing Supabase PostgreSQL
- Native SQL metadata filtering (excellent for ACL patterns)
- Transactional consistency with other data
- No additional cost (included in Supabase plan)
- Django ORM integration possible via django-pgvector
- ACID compliance for updates
- Familiar PostgreSQL operations (backup, monitoring)

**Disadvantages**

- Performance degrades above ~1M vectors
- HNSW index rebuild on large updates
- Not purpose-built for vector search
- Query planner may not optimize mixed vector + filter queries
- Requires PostgreSQL 15+ for best performance

**Evaluation Against Criteria**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Operational Simplicity | Excellent | Already have Supabase |
| Metadata Filtering | Excellent | Native SQL, perfect for ACL |
| Cost | Excellent | $0 additional |
| Implementation Effort | Good | django-pgvector available |
| Integration | Excellent | Same DB as application |
| Query Performance | Good | ~50-100ms at Phase 1 scale |
| Future Scalability | Fair | 1M vector practical limit |

**Effort Estimate**

- Complexity: Low
- Resources: 1 developer, 2-3 days
- Dependencies: pgvector extension (already in Supabase)

**Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance at scale | Low (Phase 1) | Low | Migration path to dedicated store |
| Complex ACL queries slow | Medium | Low | Proper indexing strategy |

---

### Option 2: Qdrant (Cloud or Self-Hosted)

**Description**

Qdrant is a purpose-built vector database with excellent filtering capabilities. Available as a cloud service or self-hosted Docker container.

**Technical Details**

- **Index Type**: HNSW with payload filtering
- **Max Dimensions**: No limit
- **Metadata**: Payload fields with typed schema
- **Filtering**: Native filter DSL with AND/OR/NOT

**Advantages**

- Purpose-built for vector search (fast, optimized)
- Excellent metadata filtering (designed for this use case)
- Free tier (1GB) sufficient for Phase 1
- Docker self-hosted option (no vendor lock-in)
- REST + gRPC APIs
- Active development and good documentation

**Disadvantages**

- Additional service to manage
- Data lives outside PostgreSQL (no transactional consistency)
- Cloud free tier has limitations
- Self-hosted requires Docker infrastructure
- Additional operational complexity

**Evaluation Against Criteria**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Operational Simplicity | Fair | Additional service |
| Metadata Filtering | Excellent | Native filtering DSL |
| Cost | Good | Free tier or ~$10/mo |
| Implementation Effort | Good | Good Python SDK |
| Integration | Good | REST API, separate from Django |
| Query Performance | Excellent | ~10-20ms typical |
| Future Scalability | Excellent | Built for scale |

**Effort Estimate**

- Complexity: Medium
- Resources: 1 developer, 3-4 days
- Dependencies: Qdrant cloud account or Docker

**Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Service availability | Low | Medium | Self-hosted backup option |
| Data sync issues | Medium | Medium | Careful indexing pipeline |

---

### Option 3: Pinecone

**Description**

Pinecone is a fully managed vector database as a service. Known for ease of use and performance.

**Technical Details**

- **Index Type**: Proprietary (ANN optimized)
- **Max Dimensions**: 20,000
- **Metadata**: Key-value with filtering
- **Filtering**: Filter expressions with $eq, $in, $or, etc.

**Advantages**

- Fully managed (zero ops)
- Excellent documentation and SDKs
- Free tier (1 index, 100K vectors)
- Good metadata filtering
- Low latency queries

**Disadvantages**

- Vendor lock-in (proprietary)
- Free tier limits (1 index)
- No self-hosted option
- Data outside PostgreSQL
- Pricing scales with usage

**Evaluation Against Criteria**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Operational Simplicity | Excellent | Fully managed |
| Metadata Filtering | Good | Supports OR, but complex queries limited |
| Cost | Good | Free tier, then ~$70/mo starter |
| Implementation Effort | Excellent | Best SDK/docs |
| Integration | Good | REST API |
| Query Performance | Excellent | ~10-30ms |
| Future Scalability | Excellent | Designed for scale |

**Effort Estimate**

- Complexity: Low
- Resources: 1 developer, 2 days
- Dependencies: Pinecone account

**Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Vendor lock-in | Certain | Medium | Abstract via interface |
| Cost increase at scale | High | Medium | Budget monitoring |
| Free tier limitations | Medium | Low | Upgrade path clear |

---

### Option 4: ChromaDB (Embedded)

**Description**

ChromaDB is an open-source embedding database that can run in-process (embedded) or as a separate service. Popular for prototyping and small-scale applications.

**Technical Details**

- **Index Type**: HNSW
- **Max Dimensions**: No limit
- **Metadata**: Dict-based with filtering
- **Filtering**: Where clauses with operators

**Advantages**

- Embedded mode = no additional service
- Open source (Apache 2.0)
- Simple API, fast setup
- Good for prototyping
- Zero cost

**Disadvantages**

- Limited production readiness
- Persistence can be finicky
- Metadata filtering less powerful than alternatives
- Not recommended for production by maintainers
- Limited documentation for advanced use cases

**Evaluation Against Criteria**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Operational Simplicity | Excellent | Embedded option |
| Metadata Filtering | Fair | Basic filtering, $or limited |
| Cost | Excellent | Free |
| Implementation Effort | Excellent | Very simple API |
| Integration | Good | Python-native |
| Query Performance | Good | ~20-50ms embedded |
| Future Scalability | Poor | Not designed for scale |

**Effort Estimate**

- Complexity: Very Low
- Resources: 1 developer, 1 day
- Dependencies: None (pip install)

**Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Production stability | Medium | High | Use only for dev/prototype |
| Data persistence issues | Medium | Medium | Regular backups |
| Migration needed | High | Medium | Abstract via interface |

---

### Option 5: Weaviate

**Description**

Weaviate is an open-source vector database with GraphQL API and strong schema support.

**Technical Details**

- **Index Type**: HNSW
- **Max Dimensions**: 65,535
- **Metadata**: Class-based schema
- **Filtering**: GraphQL filters, BM25 + vector hybrid

**Advantages**

- Strong schema support
- Hybrid search (vector + keyword)
- Multi-modal support
- Open source with cloud option
- Good filtering capabilities

**Disadvantages**

- GraphQL adds complexity
- Heavier resource requirements
- Cloud pricing higher than alternatives
- More complex setup
- Over-engineered for Phase 1

**Evaluation Against Criteria**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Operational Simplicity | Fair | More complex setup |
| Metadata Filtering | Good | GraphQL-based |
| Cost | Fair | Cloud ~$25/mo minimum |
| Implementation Effort | Fair | GraphQL learning curve |
| Integration | Fair | GraphQL API |
| Query Performance | Excellent | ~10-30ms |
| Future Scalability | Excellent | Built for scale |

**Effort Estimate**

- Complexity: Medium-High
- Resources: 1 developer, 4-5 days
- Dependencies: Weaviate cloud or Docker

**Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Complexity overhead | High | Medium | Use simpler option |
| Cost | Medium | Low | Monitor usage |

---

## Options Comparison Summary

| Criterion | pgvector (Supabase) | Qdrant | Pinecone | ChromaDB | Weaviate |
|-----------|---------------------|--------|----------|----------|----------|
| Operational Simplicity | Excellent | Fair | Excellent | Excellent | Fair |
| Metadata Filtering | Excellent | Excellent | Good | Fair | Good |
| Cost | Excellent | Good | Good | Excellent | Fair |
| Implementation Effort | Good | Good | Excellent | Excellent | Fair |
| Integration | Excellent | Good | Good | Good | Fair |
| Query Performance | Good | Excellent | Excellent | Good | Excellent |
| Future Scalability | Fair | Excellent | Excellent | Poor | Excellent |
| **Phase 1 Fit** | **Best** | Good | Good | Dev Only | Over-engineered |

---

## Recommendation

### Recommended Option

**Option 1: Supabase pgvector**

### Justification

For Phase 1, pgvector via Supabase provides the best fit based on the evaluation criteria:

1. **Zero Additional Infrastructure**: Uses the existing Supabase PostgreSQL database. No new services to deploy, configure, or monitor.

2. **Excellent ACL Support**: Native SQL filtering provides the most flexible and powerful metadata filtering for the ACL patterns defined in RFC-0001. Complex OR conditions are straightforward in SQL.

3. **Cost Effective**: $0 additional cost - included in the existing Supabase plan.

4. **Transactional Consistency**: Vectors and ACL metadata can be updated atomically with other application data.

5. **Familiar Operations**: PostgreSQL is well-understood for backup, monitoring, and troubleshooting.

6. **Adequate Performance**: At Phase 1 scale (5,000-200,000 vectors), pgvector will provide sub-100ms query latency with proper indexing.

### Accepted Trade-offs

1. **Not Purpose-Built**: pgvector is not as optimized as dedicated vector databases. Accepted because Phase 1 scale doesn't require it.

2. **Scale Ceiling**: pgvector performance degrades above ~1M vectors. Accepted because:
   - Phase 1 target is < 200K vectors
   - Clear migration path to Qdrant/Pinecone if needed
   - `VectorStoreInterface` abstraction enables swap

3. **Mixed Query Optimization**: Complex vector + filter queries may not be perfectly optimized. Accepted with mitigation:
   - Proper index strategy
   - Query analysis during Phase 1

### Migration Path (If Needed)

If Phase 1 succeeds and scale increases:
1. Implement `QdrantVectorStore` as alternative
2. Use existing `VectorStoreInterface` abstraction
3. Migrate data during maintenance window
4. No application code changes (strategy pattern)

### Conditions

- Ensure pgvector extension is enabled in Supabase
- Use HNSW index for similarity search
- Add appropriate GiST/GIN indexes for ACL metadata columns

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Django Application                        │
│                                                                  │
│  ┌────────────────┐     ┌────────────────────────────────────┐  │
│  │   yt_sync      │     │           rag/                     │  │
│  │   module       │     │                                    │  │
│  │                │     │  ┌──────────────────────────────┐  │  │
│  │  Video ────────┼─────┼─►│   PgVectorStore              │  │  │
│  │  Transcript    │     │  │   (implements VectorStore)   │  │  │
│  │                │     │  └────────────┬─────────────────┘  │  │
│  └────────────────┘     │               │                    │  │
│                         └───────────────┼────────────────────┘  │
└─────────────────────────────────────────┼───────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Supabase PostgreSQL                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  rag_embeddings                                             │ │
│  │  ├─ id (UUID, PK)                                          │ │
│  │  ├─ chunk_id (VARCHAR, UNIQUE)                             │ │
│  │  ├─ document_id (VARCHAR, INDEX)                           │ │
│  │  ├─ embedding (vector(1536), HNSW INDEX)                   │ │
│  │  ├─ content (TEXT)                                         │ │
│  │  ├─ metadata (JSONB)                                       │ │
│  │  │   └─ chunk_index, start_char, end_char, timestamp...    │ │
│  │  │                                                         │ │
│  │  │  -- ACL Fields (per RFC-0001)                          │ │
│  │  ├─ owner_id (VARCHAR, INDEX)                              │ │
│  │  ├─ visibility (VARCHAR, INDEX)                            │ │
│  │  ├─ shared_with_users (VARCHAR[], GIN INDEX)               │ │
│  │  ├─ shared_with_groups (VARCHAR[], GIN INDEX)              │ │
│  │  ├─ tenant_id (VARCHAR, INDEX, NULLABLE)                   │ │
│  │  │                                                         │ │
│  │  ├─ created_at (TIMESTAMP)                                 │ │
│  │  └─ updated_at (TIMESTAMP)                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main embeddings table
CREATE TABLE rag_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id VARCHAR(255) UNIQUE NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,  -- Adjust dimensions per model
    metadata JSONB DEFAULT '{}',

    -- ACL fields (RFC-0001)
    owner_id VARCHAR(255) NOT NULL,
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',
    shared_with_users VARCHAR(255)[] DEFAULT '{}',
    shared_with_groups VARCHAR(255)[] DEFAULT '{}',
    tenant_id VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW index for vector similarity
CREATE INDEX rag_embeddings_embedding_idx
ON rag_embeddings
USING hnsw (embedding vector_cosine_ops);

-- Indexes for ACL filtering
CREATE INDEX rag_embeddings_owner_idx ON rag_embeddings(owner_id);
CREATE INDEX rag_embeddings_visibility_idx ON rag_embeddings(visibility);
CREATE INDEX rag_embeddings_document_idx ON rag_embeddings(document_id);
CREATE INDEX rag_embeddings_tenant_idx ON rag_embeddings(tenant_id) WHERE tenant_id IS NOT NULL;

-- GIN indexes for array contains
CREATE INDEX rag_embeddings_shared_users_idx ON rag_embeddings USING GIN(shared_with_users);
CREATE INDEX rag_embeddings_shared_groups_idx ON rag_embeddings USING GIN(shared_with_groups);
```

### ACL Query Pattern

```sql
-- Search with ACL filtering (per RFC-0001)
SELECT
    chunk_id,
    document_id,
    content,
    metadata,
    1 - (embedding <=> $1) as similarity
FROM rag_embeddings
WHERE
    -- ACL filter (OR conditions)
    (
        owner_id = $2                                    -- Owner access
        OR visibility IN ('public', 'internal')          -- Open visibility
        OR $2 = ANY(shared_with_users)                   -- Direct share
        OR shared_with_groups && $3::varchar[]           -- Group share (array overlap)
    )
    -- Tenant isolation (if applicable)
    AND (tenant_id IS NULL OR tenant_id = $4)
ORDER BY embedding <=> $1
LIMIT $5;
```

### Implementation Files

```
rag/
├── core/
│   ├── interfaces.py      # VectorStoreInterface (existing)
│   └── schemas.py         # Data models (existing)
├── stores/
│   ├── __init__.py
│   └── pgvector.py        # PgVectorStore implementation
└── migrations/
    └── 0001_create_embeddings.py  # Django migration
```

### PgVectorStore Interface

```python
# rag/stores/pgvector.py

class PgVectorStore(VectorStoreInterface):
    """PostgreSQL pgvector implementation of VectorStoreInterface."""

    def __init__(self, connection_string: str, table_name: str = "rag_embeddings"):
        ...

    def upsert(self, chunk: Chunk, embedding: Embedding) -> None:
        """Insert or update a chunk with its embedding."""
        ...

    def upsert_batch(self, chunks: list[Chunk], embeddings: list[Embedding]) -> None:
        """Batch insert/update."""
        ...

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
        acl_context: QueryACLContext | None = None
    ) -> list[tuple[Chunk, float]]:
        """Similarity search with ACL filtering."""
        ...

    def delete(self, chunk_ids: list[str]) -> None:
        """Delete chunks by ID."""
        ...

    def delete_by_document(self, document_id: str) -> None:
        """Delete all chunks for a document."""
        ...

    def delete_by_owner(self, owner_id: str) -> int:
        """Delete all chunks owned by user (GDPR)."""
        ...

    def update_document_acl(
        self,
        document_id: str,
        visibility: Visibility,
        shared_with_users: list[str],
        shared_with_groups: list[str]
    ) -> int:
        """Update ACL for all chunks of a document."""
        ...
```

---

## Implementation Plan

### Phase 1A: Basic Vector Storage

**Scope**: Core vector storage without ACL

**Deliverables**:
- Django migration for `rag_embeddings` table
- `PgVectorStore` class with basic CRUD
- `search()` method with top_k
- Unit tests

**Dependencies**: None

### Phase 1B: ACL Integration

**Scope**: Add ACL filtering per RFC-0001

**Deliverables**:
- ACL columns and indexes
- ACL-aware `search()` method
- `delete_by_owner()` implementation
- `update_document_acl()` implementation
- Integration tests with ACL scenarios

**Dependencies**: Phase 1A, RFC-0001 schemas

### Milestones

| Milestone | Description | Status |
|-----------|-------------|--------|
| Schema Created | Migration for rag_embeddings | Not Started |
| Basic Search Works | upsert + search without ACL | Not Started |
| ACL Filtering Works | search respects owner/visibility | Not Started |
| GDPR Deletion Works | delete_by_owner tested | Not Started |

### Rollback Strategy

- Database migration is additive (new table)
- Can drop table if needed without affecting other data
- `VectorStoreInterface` abstraction allows swap

---

## Open Questions

1. **Embedding Model Selection**
   - Context: What embedding model to use?
   - Options: OpenAI text-embedding-3-small (1536d), Sentence Transformers (384d)
   - Owner: Architect
   - Status: Open
   - Impact: Affects vector dimensions in schema

2. **Django ORM vs Raw SQL**
   - Context: Use django-pgvector or raw SQL?
   - Options: django-pgvector package, psycopg2 raw SQL
   - Owner: Developer
   - Status: Open
   - Note: django-pgvector is newer, raw SQL more flexible

3. **Index Tuning**
   - Context: HNSW parameters (m, ef_construction)?
   - Owner: Developer
   - Status: Open (defer to benchmarking)

4. **Connection Pooling**
   - Context: Should vector queries use separate pool?
   - Owner: Architect
   - Status: Open (likely not needed for Phase 1)

---

## Decision Record

### Decision

**Status**: APPROVED

**Date**: 2025-12-06

**Approvers**:
- Jeremie

### Decision Summary

Approved Option 1: Supabase pgvector. This approach provides the best fit for Phase 1 by leveraging the existing Supabase PostgreSQL infrastructure with zero additional cost or operational complexity, while providing excellent ACL filtering capabilities via native SQL.

### Key Discussion Points

- Zero infrastructure overhead - uses existing Supabase PostgreSQL
- Native SQL provides flexible metadata filtering for RFC-0001 ACL patterns
- Transactional consistency with application data
- Clear migration path to dedicated vector stores if scale requires

### Conditions of Approval

- pgvector extension must be enabled in Supabase
- HNSW index must be used for similarity search
- Appropriate indexes for ACL metadata columns required
- Migration path to Qdrant/Pinecone documented for future scale

### Dissenting Opinions

None recorded.

---

## References

### Related Documents

- [RFC-0001: RAG ACL Management](../approved/in-progress/RFC-0001-rag-acl-management.md)
- [RAG Core Interfaces](../../rag/core/interfaces.py)
- [RAG Core Schemas](../../rag/core/schemas.py)
- [Technical Specification](../../technical-specs/technical-specification.md)

### External Resources

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Supabase Vector Guide](https://supabase.com/docs/guides/ai/vector-columns)
- [django-pgvector](https://github.com/pgvector/pgvector-python#django)
- [HNSW Algorithm Paper](https://arxiv.org/abs/1603.09320)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Pinecone Documentation](https://docs.pinecone.io/)

### Appendix

#### Benchmark Estimates (Phase 1 Scale)

| Operation | pgvector (est.) | Qdrant (est.) | Pinecone (est.) |
|-----------|-----------------|---------------|-----------------|
| Insert 1 vector | ~5ms | ~2ms | ~5ms |
| Insert 1000 vectors | ~500ms | ~100ms | ~200ms |
| Search top-10 (100K vectors) | ~50-100ms | ~10-20ms | ~20-30ms |
| Search with ACL filter | ~75-150ms | ~15-30ms | ~30-50ms |

*Note: These are estimates based on documented benchmarks and similar workloads. Actual performance should be validated.*

#### Cost Comparison (Phase 1)

| Solution | Monthly Cost | Notes |
|----------|-------------|-------|
| pgvector (Supabase) | $0 | Included in Supabase plan |
| Qdrant Cloud (Free) | $0 | 1GB limit |
| Qdrant Cloud (Starter) | ~$10 | If exceeding free tier |
| Pinecone (Free) | $0 | 100K vectors, 1 index |
| Pinecone (Starter) | ~$70 | If exceeding free tier |
| Weaviate Cloud | ~$25 | Minimum tier |
