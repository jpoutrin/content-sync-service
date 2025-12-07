---
tech_spec_id: TS-0001
title: RAG ACL Management
status: APPROVED
author: ""
reviewers:
  - name: Jeremie
    status: approved
created: 2025-12-06
last_updated: 2025-12-06
approved_date: 2025-12-06
decision_ref: RFC-0001
related_rfcs:
  - RFC-0001 (RAG ACL Management)
  - RFC-0002 (Vector Storage for RAG - Phase 1)
related_tech_specs: []
implementation_branch: ""
---

# TS-0001: RAG ACL Management

## Executive Summary

This Technical Specification details the implementation of an Access Control List (ACL) system for the RAG module, as approved in RFC-0001. The implementation adds ownership and visibility controls to documents and chunks, enabling secure multi-user RAG queries where users can only retrieve content they own or have been granted access to.

**Vector Storage**: Per RFC-0002, the implementation uses **Supabase pgvector** (PostgreSQL) as the vector store, leveraging native SQL for ACL filtering.

### Key Deliverables

1. New `rag/core/acl.py` module with ACL schemas
2. Updated `Document` and `Chunk` models with ownership fields
3. Updated `SearchQuery` with required ACL context
4. Updated `VectorStoreInterface` with ACL filtering and GDPR deletion methods
5. `PgVectorStore` implementation with native SQL ACL filtering
6. Django bridge layer for group resolution

### Dependencies

- RFC-0001 (RAG ACL Management) - APPROVED
- RFC-0002 (Vector Storage for RAG - Phase 1) - APPROVED
- Existing `rag/core/` module structure
- Supabase PostgreSQL with pgvector extension (v0.8.0)

---

## Table of Contents

- [Design Overview](#design-overview)
- [Detailed Design](#detailed-design)
- [API Specification](#api-specification)
- [Data Model](#data-model)
- [Implementation Details](#implementation-details)
- [Testing Strategy](#testing-strategy)
- [Deployment Plan](#deployment-plan)
- [Appendices](#appendices)

---

## Design Overview

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Host Application (Django)                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────┐  │
│  │   User    │  │   Group   │  │  Source   │  │    Video    │  │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └──────┬──────┘  │
│        │              │              │               │          │
│        └──────────────┴──────────────┴───────┬───────┘          │
│                                              │                   │
│                          ┌───────────────────▼──────────────┐   │
│                          │         Bridge Layer             │   │
│                          │   (yt_sync/rag_bridge.py)        │   │
│                          │   - Group resolution             │   │
│                          │   - ACL context building         │   │
│                          └───────────────────┬──────────────┘   │
└──────────────────────────────────────────────┼──────────────────┘
                                               │
┌──────────────────────────────────────────────▼──────────────────┐
│                    RAG Library (Framework-Agnostic)             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     rag/core/                             │   │
│  │                                                           │   │
│  │  ┌─────────────┐      ┌─────────────┐                    │   │
│  │  │   acl.py    │      │ schemas.py  │                    │   │
│  │  │             │      │  (updated)  │                    │   │
│  │  │ Visibility  │      │             │                    │   │
│  │  │ QueryACL    │◄─────│  Document   │                    │   │
│  │  │ ACLFilter   │      │  Chunk      │                    │   │
│  │  └─────────────┘      │  SearchQuery│                    │   │
│  │         │             └──────┬──────┘                    │   │
│  │         │                    │                            │   │
│  │         ▼                    ▼                            │   │
│  │  ┌──────────────────────────────────────┐                │   │
│  │  │          interfaces.py               │                │   │
│  │  │  VectorStoreInterface (updated)      │                │   │
│  │  │    - search(acl_context)             │                │   │
│  │  │    - delete_by_owner()               │                │   │
│  │  │    - update_document_acl()           │                │   │
│  │  └──────────────────────────────────────┘                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────▼──────────────────────────────┐   │
│  │               rag/stores/pgvector.py                      │   │
│  │               PgVectorStore                               │   │
│  │  - Implements VectorStoreInterface                        │   │
│  │  - Native SQL ACL filtering                               │   │
│  │  - HNSW index for similarity search                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                                               │
┌──────────────────────────────────────────────▼──────────────────┐
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
│  │  │                                                         │ │
│  │  │  -- ACL Fields (per RFC-0001)                          │ │
│  │  ├─ owner_id (VARCHAR, INDEX)                              │ │
│  │  ├─ visibility (VARCHAR, INDEX)                            │ │
│  │  ├─ shared_with_users (VARCHAR[], GIN INDEX)               │ │
│  │  ├─ shared_with_groups (VARCHAR[], GIN INDEX)              │ │
│  │  └─ tenant_id (VARCHAR, INDEX, NULLABLE)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  pgvector extension v0.8.0 enabled                              │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| `rag/core/acl.py` | ACL enums, schemas, and filter building logic |
| `rag/core/schemas.py` | Document, Chunk, SearchQuery with ACL fields |
| `rag/core/interfaces.py` | Abstract interfaces with ACL method signatures |
| `rag/stores/pgvector.py` | PostgreSQL pgvector implementation (per RFC-0002) |
| `yt_sync/rag_bridge.py` | Django integration layer for group resolution |

### Design Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| pgvector (not Pinecone/Qdrant) | Zero additional infrastructure, excellent SQL filtering (RFC-0002) | Scale ceiling ~1M vectors |
| Native SQL ACL filtering | Best filtering flexibility, ACID compliance | Slightly more complex queries |
| ACL context required on all searches | Security - prevents accidental unfiltered queries | Slightly more verbose API |
| Group resolution at query time | Flexibility - groups managed by host app | Extra lookup per query |
| Visibility enum (4 levels) | Covers common access patterns | Cannot express complex policies |

---

## Detailed Design

### Component: rag/core/acl.py

New module containing all ACL-related schemas.

#### Visibility Enum

```python
from enum import Enum

class Visibility(str, Enum):
    """Document visibility levels."""
    PRIVATE = "private"    # Only owner can access
    SHARED = "shared"      # Owner + explicitly granted principals
    INTERNAL = "internal"  # All authenticated users in tenant
    PUBLIC = "public"      # Anyone (including anonymous)
```

#### QueryACLContext Schema

```python
from pydantic import BaseModel
from typing import Optional

class QueryACLContext(BaseModel):
    """
    ACL context provided with every search query.
    Built by the host application from authenticated user info.
    """
    principal_id: str
    """The ID of the user/service making the query."""

    member_of_groups: list[str] = []
    """Group IDs the principal belongs to (resolved by host app)."""

    tenant_id: Optional[str] = None
    """Tenant ID for multi-tenant isolation. None for single-tenant."""

    bypass_acl: bool = False
    """
    Skip ACL filtering (system operations only).
    Should be logged/audited when True.
    """

    @classmethod
    def system_context(cls) -> "QueryACLContext":
        """Create a system context that bypasses ACL checks."""
        return cls(principal_id="system", bypass_acl=True)
```

#### ACLFilterSpec Schema

```python
class ACLFilterSpec(BaseModel):
    """
    Specification for ACL filtering.
    For pgvector, this translates directly to SQL WHERE clauses.
    """
    principal_id: str
    group_ids: list[str]
    tenant_id: Optional[str]
    include_public: bool = True
    include_internal: bool = True

    def to_sql_conditions(self) -> tuple[str, list]:
        """
        Generate SQL WHERE clause for pgvector ACL filtering.

        Returns:
            Tuple of (SQL string, parameters list)
        """
        conditions = []
        params = []
        param_idx = 1

        # Owner match
        conditions.append(f"owner_id = ${param_idx}")
        params.append(self.principal_id)
        param_idx += 1

        # Visibility-based access
        visibility_values = []
        if self.include_public:
            visibility_values.append("public")
        if self.include_internal:
            visibility_values.append("internal")
        if visibility_values:
            placeholders = ", ".join(f"${param_idx + i}" for i in range(len(visibility_values)))
            conditions.append(f"visibility IN ({placeholders})")
            params.extend(visibility_values)
            param_idx += len(visibility_values)

        # Direct user sharing (array contains)
        conditions.append(f"${param_idx} = ANY(shared_with_users)")
        params.append(self.principal_id)
        param_idx += 1

        # Group-based sharing (array overlap)
        if self.group_ids:
            conditions.append(f"shared_with_groups && ${param_idx}::varchar[]")
            params.append(self.group_ids)
            param_idx += 1

        # Combine with OR
        acl_clause = f"({' OR '.join(conditions)})"

        # Add tenant filter if applicable
        if self.tenant_id:
            acl_clause = f"{acl_clause} AND (tenant_id IS NULL OR tenant_id = ${param_idx})"
            params.append(self.tenant_id)

        return acl_clause, params
```

### Component: rag/core/schemas.py (Updates)

#### Document Schema Updates

```python
class Document(BaseModel):
    """Represents a document in the RAG system."""
    id: str
    source_id: str
    content: str
    metadata: dict = {}

    # ACL fields (new)
    owner_id: str
    """Principal ID who owns this document."""

    visibility: Visibility = Visibility.PRIVATE
    """Access visibility level."""

    shared_with_users: list[str] = []
    """User IDs with direct access (for SHARED visibility)."""

    shared_with_groups: list[str] = []
    """Group IDs with access (for SHARED visibility)."""

    tenant_id: Optional[str] = None
    """Tenant ID for multi-tenant deployments."""
```

#### Chunk Schema Updates

```python
class Chunk(BaseModel):
    """A chunk of a document with embedding."""
    id: str
    document_id: str
    content: str
    embedding: Optional[list[float]] = None
    metadata: dict = {}

    # ACL fields (denormalized from Document)
    owner_id: str
    visibility: Visibility
    shared_with_users: list[str] = []
    shared_with_groups: list[str] = []
    tenant_id: Optional[str] = None

    @classmethod
    def from_document(
        cls,
        document: Document,
        chunk_id: str,
        content: str,
        embedding: Optional[list[float]] = None,
        **metadata
    ) -> "Chunk":
        """Create a chunk inheriting ACL from parent document."""
        return cls(
            id=chunk_id,
            document_id=document.id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            owner_id=document.owner_id,
            visibility=document.visibility,
            shared_with_users=document.shared_with_users.copy(),
            shared_with_groups=document.shared_with_groups.copy(),
            tenant_id=document.tenant_id,
        )
```

#### SearchQuery Schema Updates

```python
class SearchQuery(BaseModel):
    """Query for vector similarity search."""
    query_text: str
    top_k: int = 10
    filters: dict = {}

    # ACL context (new, required)
    acl_context: QueryACLContext
    """Required ACL context for filtering results."""
```

### Component: rag/core/interfaces.py (Updates)

#### VectorStoreInterface Updates

```python
from abc import ABC, abstractmethod
from typing import Optional
from .acl import QueryACLContext, Visibility

class VectorStoreInterface(ABC):
    """Abstract interface for vector store implementations."""

    @abstractmethod
    def upsert(self, chunks: list[Chunk]) -> int:
        """Insert or update chunks in the vector store."""
        pass

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: Optional[dict] = None,
        acl_context: Optional[QueryACLContext] = None,
    ) -> list[tuple[Chunk, float]]:
        """
        Search for similar chunks.

        Args:
            query_vector: Query embedding vector
            top_k: Maximum results to return
            filters: Additional metadata filters
            acl_context: ACL context for filtering (required unless bypass)

        Returns:
            List of (chunk, score) tuples, highest scores first

        Raises:
            ValueError: If acl_context is None and bypass not enabled
        """
        pass

    @abstractmethod
    def delete_by_owner(self, owner_id: str, tenant_id: Optional[str] = None) -> int:
        """
        Delete all chunks owned by a principal (GDPR right to erasure).

        Args:
            owner_id: Principal ID whose chunks to delete
            tenant_id: Optional tenant scope

        Returns:
            Number of chunks deleted
        """
        pass

    @abstractmethod
    def delete_by_document(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        pass

    @abstractmethod
    def update_document_acl(
        self,
        document_id: str,
        visibility: Optional[Visibility] = None,
        shared_with_users: Optional[list[str]] = None,
        shared_with_groups: Optional[list[str]] = None,
    ) -> int:
        """
        Update ACL fields on all chunks of a document.

        Args:
            document_id: Document whose chunks to update
            visibility: New visibility (if provided)
            shared_with_users: New user list (if provided)
            shared_with_groups: New group list (if provided)

        Returns:
            Number of chunks updated
        """
        pass
```

### Component: rag/stores/pgvector.py (New - per RFC-0002)

```python
"""PostgreSQL pgvector implementation of VectorStoreInterface."""

from typing import Optional
import psycopg2
from psycopg2.extras import execute_values

from rag.core.interfaces import VectorStoreInterface
from rag.core.schemas import Chunk
from rag.core.acl import QueryACLContext, Visibility, ACLFilterSpec


class PgVectorStore(VectorStoreInterface):
    """
    PostgreSQL pgvector implementation of VectorStoreInterface.

    Uses native SQL for ACL filtering, providing excellent performance
    and full support for complex OR conditions required by RFC-0001.
    """

    def __init__(
        self,
        connection_string: str,
        table_name: str = "rag_embeddings",
        dimensions: int = 1536,
    ):
        self.connection_string = connection_string
        self.table_name = table_name
        self.dimensions = dimensions

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.connection_string)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: Optional[dict] = None,
        acl_context: Optional[QueryACLContext] = None,
    ) -> list[tuple[Chunk, float]]:
        """
        Similarity search with ACL filtering using native SQL.

        The ACL filter is applied as a WHERE clause combined with
        the vector similarity search, leveraging PostgreSQL's
        query planner for optimal execution.
        """
        if acl_context is None:
            raise ValueError("acl_context is required for search")

        if acl_context.bypass_acl:
            acl_clause = "TRUE"
            acl_params = []
        else:
            filter_spec = ACLFilterSpec(
                principal_id=acl_context.principal_id,
                group_ids=acl_context.member_of_groups,
                tenant_id=acl_context.tenant_id,
            )
            acl_clause, acl_params = filter_spec.to_sql_conditions()

        # Build query with ACL filtering
        query = f"""
            SELECT
                chunk_id,
                document_id,
                content,
                metadata,
                owner_id,
                visibility,
                shared_with_users,
                shared_with_groups,
                tenant_id,
                1 - (embedding <=> %s::vector) as similarity
            FROM {self.table_name}
            WHERE {acl_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        params = [query_vector] + acl_params + [query_vector, top_k]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                results = []
                for row in cur.fetchall():
                    chunk = Chunk(
                        id=row[0],
                        document_id=row[1],
                        content=row[2],
                        metadata=row[3],
                        owner_id=row[4],
                        visibility=Visibility(row[5]),
                        shared_with_users=row[6] or [],
                        shared_with_groups=row[7] or [],
                        tenant_id=row[8],
                    )
                    similarity = row[9]
                    results.append((chunk, similarity))
                return results

    def delete_by_owner(self, owner_id: str, tenant_id: Optional[str] = None) -> int:
        """
        Delete all chunks owned by a principal (GDPR compliance).

        Simple SQL DELETE with owner_id filter.
        """
        if tenant_id:
            query = f"""
                DELETE FROM {self.table_name}
                WHERE owner_id = %s AND tenant_id = %s
            """
            params = (owner_id, tenant_id)
        else:
            query = f"""
                DELETE FROM {self.table_name}
                WHERE owner_id = %s
            """
            params = (owner_id,)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                deleted = cur.rowcount
                conn.commit()
                return deleted

    def update_document_acl(
        self,
        document_id: str,
        visibility: Optional[Visibility] = None,
        shared_with_users: Optional[list[str]] = None,
        shared_with_groups: Optional[list[str]] = None,
    ) -> int:
        """
        Update ACL fields on all chunks of a document.

        Atomic UPDATE across all chunks - ACID compliant.
        """
        updates = []
        params = []

        if visibility is not None:
            updates.append("visibility = %s")
            params.append(visibility.value)
        if shared_with_users is not None:
            updates.append("shared_with_users = %s")
            params.append(shared_with_users)
        if shared_with_groups is not None:
            updates.append("shared_with_groups = %s")
            params.append(shared_with_groups)

        if not updates:
            return 0

        updates.append("updated_at = NOW()")
        params.append(document_id)

        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(updates)}
            WHERE document_id = %s
        """

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                updated = cur.rowcount
                conn.commit()
                return updated
```

---

## API Specification

### Python API

#### Creating Documents with ACL

```python
from rag.core.schemas import Document
from rag.core.acl import Visibility

# Private document (default)
doc = Document(
    id="doc-123",
    source_id="source-456",
    content="...",
    owner_id="user-789",
)

# Shared document
doc = Document(
    id="doc-123",
    source_id="source-456",
    content="...",
    owner_id="user-789",
    visibility=Visibility.SHARED,
    shared_with_users=["user-111", "user-222"],
    shared_with_groups=["team-engineering"],
)

# Internal document (all authenticated users in tenant)
doc = Document(
    id="doc-123",
    source_id="source-456",
    content="...",
    owner_id="user-789",
    visibility=Visibility.INTERNAL,
    tenant_id="acme-corp",
)
```

#### Searching with ACL

```python
from rag.core.acl import QueryACLContext
from rag.stores.pgvector import PgVectorStore

# Initialize store (connection from Django settings)
store = PgVectorStore(
    connection_string="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
)

# Build ACL context from authenticated user
acl_context = QueryACLContext(
    principal_id=str(request.user.id),
    member_of_groups=[str(g.id) for g in request.user.groups.all()],
    tenant_id=getattr(request.user, 'tenant_id', None),
)

# Search with ACL filtering
results = store.search(
    query_vector=embedder.embed(query),
    top_k=10,
    acl_context=acl_context,
)
```

#### GDPR Deletion

```python
# Delete all content owned by a user
deleted_count = store.delete_by_owner(
    owner_id="user-to-delete",
    tenant_id="acme-corp",  # optional scope
)
```

---

## Data Model

### Database Schema (pgvector - per RFC-0002)

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

-- HNSW index for vector similarity (per RFC-0002)
CREATE INDEX rag_embeddings_embedding_idx
ON rag_embeddings
USING hnsw (embedding vector_cosine_ops);

-- Indexes for ACL filtering
CREATE INDEX rag_embeddings_owner_idx ON rag_embeddings(owner_id);
CREATE INDEX rag_embeddings_visibility_idx ON rag_embeddings(visibility);
CREATE INDEX rag_embeddings_document_idx ON rag_embeddings(document_id);
CREATE INDEX rag_embeddings_tenant_idx ON rag_embeddings(tenant_id) WHERE tenant_id IS NOT NULL;

-- GIN indexes for array contains (critical for ACL performance)
CREATE INDEX rag_embeddings_shared_users_idx ON rag_embeddings USING GIN(shared_with_users);
CREATE INDEX rag_embeddings_shared_groups_idx ON rag_embeddings USING GIN(shared_with_groups);
```

### ACL Query Pattern (Native SQL)

```sql
-- Search with ACL filtering (per RFC-0001 + RFC-0002)
SELECT
    chunk_id,
    document_id,
    content,
    metadata,
    1 - (embedding <=> $1) as similarity
FROM rag_embeddings
WHERE
    -- ACL filter (OR conditions - native SQL)
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

**Why pgvector excels for ACL filtering:**
- Native SQL OR conditions (no proprietary filter DSL)
- GIN indexes for efficient array operations
- ACID-compliant ACL updates
- Single database for vectors + ACL metadata

---

## Implementation Details

### File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `rag/core/acl.py` | New | Visibility, QueryACLContext, ACLFilterSpec |
| `rag/core/schemas.py` | Modify | Add ACL fields to Document, Chunk, SearchQuery |
| `rag/core/interfaces.py` | Modify | Add ACL params to VectorStoreInterface |
| `rag/core/__init__.py` | Modify | Export new ACL types |
| `rag/stores/__init__.py` | New | Stores module |
| `rag/stores/pgvector.py` | New | PgVectorStore implementation (RFC-0002) |
| `rag/migrations/0001_*.py` | New | Django migration for rag_embeddings table |
| `yt_sync/rag_bridge.py` | New | Django-to-RAG integration layer |

### Implementation Order

1. **Phase 1: Core ACL Types** (rag/core/acl.py)
   - Visibility enum
   - QueryACLContext schema
   - ACLFilterSpec with to_sql_conditions()

2. **Phase 2: Schema Updates** (rag/core/schemas.py)
   - Add ACL fields to Document
   - Add ACL fields to Chunk with from_document() helper
   - Add acl_context to SearchQuery

3. **Phase 3: Interface Updates** (rag/core/interfaces.py)
   - Add acl_context param to search()
   - Add delete_by_owner() method
   - Add update_document_acl() method

4. **Phase 4: PgVectorStore Implementation** (rag/stores/pgvector.py)
   - Implement VectorStoreInterface with pgvector
   - Native SQL ACL filtering
   - GDPR deletion support

5. **Phase 5: Database Migration**
   - Create rag_embeddings table with ACL columns
   - Create HNSW and GIN indexes

6. **Phase 6: Django Bridge** (yt_sync/rag_bridge.py)
   - build_acl_context(user) helper
   - Group resolution integration

---

## Testing Strategy

### Unit Tests

| Test Case | Component | Description |
|-----------|-----------|-------------|
| `test_visibility_enum` | acl.py | Verify enum values and string conversion |
| `test_query_acl_context_validation` | acl.py | Required fields, defaults |
| `test_system_context_bypass` | acl.py | System context has bypass=True |
| `test_acl_filter_spec_to_sql` | acl.py | SQL generation for pgvector |
| `test_document_acl_defaults` | schemas.py | Default visibility is PRIVATE |
| `test_chunk_from_document` | schemas.py | ACL fields copied correctly |
| `test_search_query_requires_acl` | schemas.py | acl_context is required |

### Integration Tests (with pgvector)

| Test Case | Description |
|-----------|-------------|
| `test_search_owner_access` | Owner can retrieve own documents |
| `test_search_no_cross_user_access` | User A cannot see User B's private docs |
| `test_search_shared_user_access` | Shared docs visible to granted users |
| `test_search_shared_group_access` | Shared docs visible to group members |
| `test_search_internal_visibility` | Internal docs visible to tenant users |
| `test_search_public_visibility` | Public docs visible to anyone |
| `test_delete_by_owner` | All owner's chunks deleted |
| `test_update_document_acl` | ACL changes propagate to chunks atomically |

### Test Data Fixtures

```python
FIXTURES = {
    "users": [
        {"id": "user-alice", "groups": ["team-eng"]},
        {"id": "user-bob", "groups": ["team-sales"]},
        {"id": "user-charlie", "groups": ["team-eng", "team-sales"]},
    ],
    "documents": [
        {
            "id": "doc-private",
            "owner_id": "user-alice",
            "visibility": "private",
        },
        {
            "id": "doc-shared-user",
            "owner_id": "user-alice",
            "visibility": "shared",
            "shared_with_users": ["user-bob"],
        },
        {
            "id": "doc-shared-group",
            "owner_id": "user-alice",
            "visibility": "shared",
            "shared_with_groups": ["team-sales"],
        },
        {
            "id": "doc-internal",
            "owner_id": "user-alice",
            "visibility": "internal",
            "tenant_id": "tenant-1",
        },
        {
            "id": "doc-public",
            "owner_id": "user-alice",
            "visibility": "public",
        },
    ],
}
```

---

## Deployment Plan

### Prerequisites

- [ ] All tests passing
- [ ] Code review completed
- [ ] RFC-0001 approved (done)
- [ ] RFC-0002 approved (done)
- [ ] pgvector extension enabled in Supabase (done - v0.8.0)

### Migration Steps

1. **Deploy database migration**
   - Run Django migration to create rag_embeddings table
   - Verify HNSW and GIN indexes created

2. **Deploy code changes** (non-breaking)
   - ACL fields have defaults, existing code continues to work
   - New acl_context param is optional initially

3. **Migrate existing data** (if applicable)
   - Set owner_id from existing source ownership
   - Set visibility to PRIVATE (safe default)

4. **Enable ACL enforcement**
   - Update Django bridge to build ACL context
   - Flip feature flag to require acl_context

5. **Verify and monitor**
   - Check query latency metrics (target: <100ms p95)
   - Verify no unauthorized access in logs

### Rollback Plan

1. Disable ACL enforcement (feature flag)
2. acl_context param ignored, returns all results
3. Investigate and fix issues
4. Re-enable incrementally

---

## Appendices

### A. Related Documents

- [RFC-0001: RAG ACL Management](../rfcs/approved/in-progress/RFC-0001-rag-acl-management.md)
- [RFC-0002: Vector Storage for RAG - Phase 1](../rfcs/approved/RFC-0002-vector-storage-phase1.md)
- [RAG Core Interfaces](rag/core/interfaces.py)
- [RAG Core Schemas](rag/core/schemas.py)

### B. Open Questions from RFCs

| Question | Source | Status | Resolution |
|----------|--------|--------|------------|
| Group Resolution Caching | RFC-0001 | Open | Defer to implementation |
| Default Visibility for Existing | RFC-0001 | Resolved | PRIVATE |
| Permission Levels Beyond READ | RFC-0001 | Deferred | Future RFC |
| Audit Logging | RFC-0001 | Deferred | Future RFC |
| Embedding Model Selection | RFC-0002 | Open | TBD (affects vector dimensions) |
| Django ORM vs Raw SQL | RFC-0002 | Resolved | Raw SQL for flexibility |
| HNSW Index Tuning | RFC-0002 | Open | Defer to benchmarking |

### C. pgvector vs Alternatives (Summary from RFC-0002)

| Feature | pgvector (chosen) | Pinecone | Qdrant |
|---------|------------------|----------|--------|
| ACL Filtering | Native SQL (excellent) | Filter DSL | Filter DSL |
| Additional Infrastructure | None | Cloud service | Cloud/Docker |
| Cost (Phase 1) | $0 | $0-70/mo | $0-10/mo |
| ACID Compliance | Yes | No | No |
| Scale Ceiling | ~1M vectors | Unlimited | Unlimited |
| **Phase 1 Fit** | **Best** | Good | Good |

### D. Changelog

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-12-06 | 0.1 | - | Initial draft from RFC-0001 |
| 2025-12-06 | 0.2 | - | Updated with RFC-0002 pgvector decision |
