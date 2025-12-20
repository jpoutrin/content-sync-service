# Architecture: RAG ACL Management (TS-0001)

## Architecture Overview

This Tech Spec implements Access Control List (ACL) management for the RAG module, enabling content visibility control based on user permissions and group memberships.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Django Application Layer                     │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │  yt_sync module  │                                            │
│  │                  │                                            │
│  │  rag_bridge.py   │ ◄── Converts Django User → QueryACLContext │
│  └────────┬─────────┘                                            │
│           │                                                       │
└───────────┼───────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         RAG Module Layer                         │
│                                                                   │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │  core/acl.py     │     │  core/schemas.py │                  │
│  │                  │     │                  │                  │
│  │  • Visibility    │────▶│  • Document      │                  │
│  │  • ACLContext    │     │  • Chunk         │                  │
│  │  • ACLFilter     │     │    (with ACL)    │                  │
│  └──────────────────┘     └──────────────────┘                  │
│           │                         │                            │
│           ▼                         │                            │
│  ┌──────────────────┐               │                            │
│  │ core/interfaces  │               │                            │
│  │                  │               │                            │
│  │ VectorStore      │               │                            │
│  │ Interface        │◄──────────────┘                            │
│  │ (ACL-aware)      │                                            │
│  └────────┬─────────┘                                            │
│           │                                                       │
└───────────┼───────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Implementation Layer                  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │  stores/pgvector.py                                          ││
│  │                                                              ││
│  │  PostgresPGVectorStore                                       ││
│  │  • similarity_search_with_acl()                              ││
│  │  • add_texts() - propagates ACL to chunks                    ││
│  │  • Native SQL ACL filtering                                  ││
│  └──────────────────────────────────────────────────────────────┘│
│           │                                                       │
└───────────┼───────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL + pgvector                       │
│                                                                   │
│  Tables:                                                         │
│  • rag_documents (visibility, owner_id, allowed_groups)          │
│  • rag_chunks (visibility, owner_id, allowed_groups, embedding)  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | File Path | Responsibilities |
|-----------|-----------|------------------|
| **ACL Core Types** | `rag/core/acl.py` | Define Visibility enum, QueryACLContext (user context), ACLFilter (query construction) |
| **Schema Extensions** | `rag/core/schemas.py` | Extend Document and Chunk models with ACL fields (visibility, owner_id, allowed_groups) |
| **Interface Updates** | `rag/core/interfaces.py` | Add ACL-aware methods to VectorStoreInterface (similarity_search_with_acl) |
| **pgvector Store** | `rag/stores/pgvector.py` | Implement ACL filtering in PostgreSQL queries, propagate ACL from documents to chunks |
| **Django Bridge** | `yt_sync/rag_bridge.py` | Convert Django User/request context to QueryACLContext, resolve group memberships |
| **Database Schema** | Migration file | Add ACL columns to rag_documents and rag_chunks tables with indexes |

## Design Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| **pgvector for storage** | Per RFC-0002, native SQL enables efficient ACL filtering alongside vector similarity | Couples ACL logic to PostgreSQL; harder to swap storage backends |
| **Denormalized ACL on chunks** | Query performance - avoid JOINs on every search | Storage overhead; must keep chunks in sync with parent document |
| **Group resolution at query time** | Flexibility - group changes immediately affect access | Slight query overhead vs. caching group memberships |
| **Required QueryACLContext** | Security by default - all searches must specify user context | More verbose API; cannot accidentally skip ACL checks |
| **Visibility enum** | Clear, type-safe access levels (PUBLIC, PRIVATE, GROUP) | Less flexible than role-based permissions |

## Data Flow

### Document Ingestion with ACL
```
1. Django view receives content + user context
   ↓
2. rag_bridge.py creates ACLContext from Django User
   ↓
3. Create Document with ACL fields (visibility, owner_id, allowed_groups)
   ↓
4. PostgresPGVectorStore.add_texts() chunks document
   ↓
5. ACL fields propagated to each Chunk
   ↓
6. Chunks stored in rag_chunks table with ACL columns + embedding
```

### ACL-Filtered Search
```
1. Django view receives search query + user context
   ↓
2. rag_bridge.py creates QueryACLContext from Django User
   ↓
3. QueryACLContext resolves user's group memberships
   ↓
4. PostgresPGVectorStore.similarity_search_with_acl()
   ↓
5. Build SQL with ACL WHERE clause:
   - visibility = PUBLIC OR
   - (visibility = PRIVATE AND owner_id = user_id) OR
   - (visibility = GROUP AND allowed_groups && user_groups)
   ↓
6. Execute vector similarity + ACL filter in single query
   ↓
7. Return filtered chunks
```

## Integration Points

### 1. Django Authentication → RAG ACL
**Location**: `yt_sync/rag_bridge.py`

Responsibilities:
- Convert `request.user` to `QueryACLContext`
- Resolve Django group memberships to group IDs
- Handle anonymous users (public-only access)

### 2. RAG Core → pgvector Storage
**Location**: `rag/stores/pgvector.py`

Responsibilities:
- Translate ACLFilter to SQL WHERE clauses
- Use PostgreSQL array operators for group checks (`&&`)
- Combine ACL filtering with vector similarity (`<=>` operator)

### 3. Document Lifecycle → Chunk ACL Sync
**Location**: `rag/stores/pgvector.py`

Responsibilities:
- On document creation: propagate ACL to new chunks
- On document update: update ACL on existing chunks
- On document deletion: cascade to chunks (via foreign key)

### 4. Database Schema
**Location**: Migration file

Responsibilities:
- Add ACL columns to `rag_documents` and `rag_chunks`
- Create indexes on `(visibility, owner_id)` for query performance
- Create GIN index on `allowed_groups` array for group checks

## Security Considerations

1. **Default-Deny**: All searches require QueryACLContext; no implicit public access
2. **Group Resolution**: Groups resolved at query time to prevent stale permissions
3. **SQL Injection**: Use parameterized queries for ACL filters
4. **Index Coverage**: Indexes on ACL columns prevent table scans on large datasets

## Performance Notes

1. **Query Performance**: ACL filtering adds minimal overhead due to indexes
2. **Storage Overhead**: ~40 bytes per chunk for ACL fields
3. **Group Checks**: PostgreSQL array operator (`&&`) is O(n*m) but fast for small arrays
4. **Critical Path**: Index on `(visibility, owner_id, allowed_groups)` is essential

## Testing Strategy

1. **Unit Tests**: ACL filter logic, group resolution, visibility rules
2. **Integration Tests**: End-to-end search with various ACL configurations
3. **Performance Tests**: Search performance with ACL filtering on 10k+ chunks
4. **Security Tests**: Verify unauthorized access is blocked
