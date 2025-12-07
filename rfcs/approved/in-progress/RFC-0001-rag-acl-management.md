---
rfc_id: RFC-0001
title: RAG ACL Management
status: IN_PROGRESS
author:
reviewers:
  - name: Jeremie
    status: approved
created: 2025-12-06
last_updated: 2025-12-06
decision_date: 2025-12-06
implementation_started: 2025-12-06
related_prds: []
related_rfcs: []
---

# RFC-0001: RAG ACL Management

## Overview

This RFC proposes an Access Control List (ACL) system for the RAG (Retrieval-Augmented Generation) module. The system will control which users can access which documents during vector similarity searches, supporting ownership, sharing, group permissions, and multi-tenancy while keeping the RAG core library framework-agnostic.

The ACL layer is essential for a production RAG system where users should only retrieve content they own or have been granted access to. Without it, any user could potentially retrieve any indexed document.

## Table of Contents

- [Background & Context](#background--context)
- [Problem Statement](#problem-statement)
- [Goals & Non-Goals](#goals--non-goals)
- [Evaluation Criteria](#evaluation-criteria)
- [Options Analysis](#options-analysis)
- [Recommendation](#recommendation)
- [Technical Design](#technical-design)
- [Security Considerations](#security-considerations)
- [Implementation Plan](#implementation-plan)
- [Open Questions](#open-questions)
- [Decision Record](#decision-record)
- [References](#references)

---

## Background & Context

### Current State

The RAG module (`rag/core/`) currently defines basic schemas and interfaces:
- `Document`, `Chunk`, `Embedding` - Data models
- `SearchQuery`, `SearchResult`, `RetrievalResult` - Query/response models
- `ChunkerInterface`, `EmbedderInterface`, `VectorStoreInterface`, `RetrieverInterface` - Abstract interfaces

There is **no access control**. Any query can potentially return any indexed document.

### Historical Context

The content-sync-service indexes YouTube video transcripts. Videos belong to Sources, and Sources belong to Users. The data model already has ownership semantics in Django, but the RAG layer has no awareness of this.

### Glossary

| Term | Definition |
|------|------------|
| Principal | An entity (user, group, or service) that can own or access documents |
| ACL | Access Control List - defines who can access a resource |
| Visibility | The access level of a document (private, shared, internal, public) |
| Tenant | An isolated organization/customer in multi-tenant deployments |
| Vector Store | Database optimized for similarity search (Pinecone, Qdrant, etc.) |

---

## Problem Statement

### The Problem

The RAG system has no mechanism to restrict document access based on ownership or permissions. When a user queries the system, they could potentially receive chunks from documents they don't have access to.

### Evidence

- Current `SearchQuery` schema has no principal/user context
- `VectorStoreInterface.search()` has no ACL filtering parameter
- Documents and Chunks have no ownership fields
- No mechanism exists to share documents between users

### Impact of Inaction

- **Security Risk**: Users could access other users' private content
- **Compliance Risk**: Potential GDPR violations if users access personal data
- **Trust Risk**: Users won't trust the system with sensitive content
- **Feature Block**: Cannot launch multi-user features without access control

---

## Goals & Non-Goals

### Goals (In Scope)

1. Add ownership (owner_id) to documents and chunks
2. Support 4 visibility levels: PRIVATE, SHARED, INTERNAL, PUBLIC
3. Enable sharing with individual users and groups
4. Filter search results based on ACL at query time
5. Keep RAG core library framework-agnostic (no Django imports)
6. Support GDPR deletion by owner (delete_by_owner)
7. Support optional multi-tenancy (tenant_id)

### Non-Goals (Out of Scope)

1. User/Group management (handled by host application)
2. Authentication (handled by Django)
3. Fine-grained permissions beyond READ (WRITE/MANAGE are future work)
4. Audit logging (future RFC)
5. Real-time permission sync (eventual consistency acceptable)

### Success Criteria

- [ ] All search queries require ACL context
- [ ] Users can only retrieve documents they own or have access to
- [ ] Sharing with users and groups works correctly
- [ ] delete_by_owner removes all user's chunks (GDPR compliance)
- [ ] No Django imports in rag/core/

---

## Evaluation Criteria

| Criterion | Weight | Description | Minimum Threshold |
|-----------|--------|-------------|-------------------|
| Security | High | No unauthorized access to documents | Zero leakage |
| Performance | High | Query latency impact from ACL filtering | < 50ms added |
| Framework Independence | High | RAG core has no Django imports | 100% |
| Maintainability | Medium | Code complexity and understandability | Reasonable |
| Flexibility | Medium | Support for various access patterns | 4 visibility levels |
| Implementation Effort | Medium | Time to implement | < 2 weeks |

---

## Options Analysis

### Option 1: Metadata Filtering at Vector Store Level

**Description**

Store ACL fields (owner_id, visibility, shared_with_users, shared_with_groups) as metadata on each chunk in the vector store. Filter at query time using the vector store's native metadata filtering capabilities.

**Advantages**

- Single query combines similarity search + ACL filtering
- No post-filtering required (efficient)
- Works with most vector stores (Pinecone, Qdrant, Weaviate)
- Denormalized data = fast queries
- ACL changes update metadata in place

**Disadvantages**

- Denormalization means duplicated ACL data across chunks
- Metadata storage limits may apply (varies by vector store)
- Complex OR queries for group-based access
- ACL updates require touching all chunks of a document

**Evaluation Against Criteria**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Security | Excellent | Filtering happens at data layer |
| Performance | Excellent | Native vector store filtering |
| Framework Independence | Excellent | Pure data model changes |
| Maintainability | Good | Some complexity in filter building |
| Flexibility | Good | Supports all visibility levels |
| Implementation Effort | Medium | Need to update schemas + interfaces |

**Effort Estimate**

- Complexity: Medium
- Resources: 1 developer, ~1 week
- Dependencies: Vector store must support metadata filtering

**Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Metadata size limits | Low | Medium | Monitor chunk metadata size |
| Complex filter queries | Medium | Low | Abstract filter builder |

---

### Option 2: Post-Query Filtering in Application Layer

**Description**

Perform vector similarity search without ACL filtering, then filter results in the application layer based on ACL rules. Retrieve more results than needed, filter, then return top_k.

**Advantages**

- Simpler vector store integration
- No metadata storage requirements
- ACL logic entirely in Python
- Easy to change ACL rules without re-indexing

**Disadvantages**

- Inefficient: fetch N*3 results to get N after filtering
- Latency increases with stricter ACL
- May miss relevant results if pre-filter count too low
- ACL checks on every returned chunk
- Doesn't scale well with large result sets

**Evaluation Against Criteria**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Security | Good | Filtering works but happens late |
| Performance | Poor | Over-fetching + post-filtering |
| Framework Independence | Excellent | Pure Python filtering |
| Maintainability | Good | Simple logic |
| Flexibility | Excellent | Any ACL logic possible |
| Implementation Effort | Low | Minimal changes to interfaces |

**Effort Estimate**

- Complexity: Low
- Resources: 1 developer, ~3 days
- Dependencies: None

**Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Missing relevant results | High | High | Increase over-fetch ratio |
| Poor performance at scale | High | High | None - architectural limit |

---

### Option 3: Separate Indexes Per Tenant/User

**Description**

Create separate vector store collections/indexes per tenant or per user. Route queries to the appropriate index.

**Advantages**

- Perfect isolation - no filter logic needed
- Potentially better performance (smaller indexes)
- Clear data boundaries for compliance
- Simple deletion (drop collection)

**Disadvantages**

- Cannot share documents across users/tenants
- Many small indexes = operational complexity
- Index management overhead (create/delete)
- Cross-tenant search impossible
- Doesn't support SHARED or INTERNAL visibility

**Evaluation Against Criteria**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Security | Excellent | Physical isolation |
| Performance | Good | Smaller indexes but routing overhead |
| Framework Independence | Good | Routing logic needed |
| Maintainability | Poor | Many indexes to manage |
| Flexibility | Poor | No sharing between users |
| Implementation Effort | High | Significant infrastructure changes |

**Effort Estimate**

- Complexity: High
- Resources: 1-2 developers, ~2-3 weeks
- Dependencies: Vector store multi-collection support

**Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Operational complexity | High | High | Automation required |
| No sharing support | Certain | High | Cannot mitigate |

---

### Options Comparison Summary

| Criterion | Option 1: Metadata Filter | Option 2: Post-Filter | Option 3: Separate Indexes |
|-----------|---------------------------|----------------------|---------------------------|
| Security | Excellent | Good | Excellent |
| Performance | Excellent | Poor | Good |
| Framework Independence | Excellent | Excellent | Good |
| Maintainability | Good | Good | Poor |
| Flexibility | Good | Excellent | Poor |
| Implementation Effort | Medium | Low | High |
| **Overall** | **Recommended** | Not Recommended | Not Recommended |

---

## Recommendation

### Recommended Option

**Option 1: Metadata Filtering at Vector Store Level**

### Justification

Option 1 provides the best balance of security, performance, and flexibility:

1. **Security**: ACL filtering happens at the data layer, preventing unauthorized chunks from ever reaching the application
2. **Performance**: Native vector store filtering is optimized and doesn't require over-fetching
3. **Flexibility**: Supports all 4 visibility levels including sharing with users and groups
4. **Framework Independence**: All changes are in Pydantic schemas and interfaces

### Accepted Trade-offs

1. **Denormalization**: ACL data duplicated on each chunk - acceptable because chunks are the unit of retrieval and updates are infrequent
2. **Complex filter queries**: OR conditions for group access - acceptable with abstract filter builder
3. **Metadata storage**: Additional fields per chunk - acceptable, well within limits

### Conditions

- Vector store implementation must support metadata filtering with OR conditions
- Group resolution happens at query time (host app provides group memberships)

---

## Technical Design

### Architecture Overview

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
│                          │   (Resolves groups, builds ACL)  │   │
│                          └───────────────────┬──────────────┘   │
└──────────────────────────────────────────────┼──────────────────┘
                                               │
┌──────────────────────────────────────────────▼──────────────────┐
│                    RAG Library (Framework-Agnostic)             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     rag/core/                             │   │
│  │                                                           │   │
│  │  Document ──────► Chunk ──────► Vector Store              │   │
│  │      │               │              │                     │   │
│  │      ├─ owner_id     ├─ owner_id    ├─ ACL metadata       │   │
│  │      ├─ visibility   ├─ visibility  │   filtering         │   │
│  │      ├─ shared_with  ├─ shared_with │                     │   │
│  │      └─ tenant_id    └─ tenant_id   │                     │   │
│  │                                     │                     │   │
│  │  SearchQuery ───────────────────────┘                     │   │
│  │      └─ acl_context (required)                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Key Components

#### New File: `rag/core/acl.py`

ACL-specific Pydantic schemas:

```python
class Visibility(str, Enum):
    PRIVATE = "private"    # Only owner
    SHARED = "shared"      # Owner + granted principals
    INTERNAL = "internal"  # All authenticated in tenant
    PUBLIC = "public"      # Anyone

class QueryACLContext(BaseModel):
    principal_id: str                    # Who is querying
    member_of_groups: list[str] = []     # Groups they belong to
    tenant_id: Optional[str] = None      # Tenant isolation
    bypass_acl: bool = False             # System operations only

class ACLFilterSpec(BaseModel):
    # Generated from QueryACLContext
    # Translates to vector store native filters
```

#### Modified: `rag/core/schemas.py`

Add ACL fields to existing models:

```python
class Document(BaseModel):
    # ... existing fields ...
    owner_id: str                        # Required
    visibility: Visibility = Visibility.PRIVATE
    shared_with_users: list[str] = []
    shared_with_groups: list[str] = []
    tenant_id: Optional[str] = None

class Chunk(BaseModel):
    # ... existing fields ...
    # Denormalized from Document:
    owner_id: str
    visibility: Visibility
    shared_with_users: list[str]
    shared_with_groups: list[str]
    tenant_id: Optional[str]

class SearchQuery(BaseModel):
    # ... existing fields ...
    acl_context: QueryACLContext         # Required
```

#### Modified: `rag/core/interfaces.py`

Add ACL methods to interfaces:

```python
class VectorStoreInterface(ABC):
    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: Optional[dict] = None,
        acl_context: Optional[QueryACLContext] = None  # New
    ) -> list[tuple[Chunk, float]]:
        pass

    @abstractmethod
    def delete_by_owner(self, owner_id: str) -> int:  # New - GDPR
        pass

    @abstractmethod
    def update_document_acl(                          # New
        self,
        document_id: str,
        visibility: Visibility,
        shared_with_users: list[str],
        shared_with_groups: list[str]
    ) -> int:
        pass
```

### Data Model

**Document/Chunk ACL Fields:**

| Field | Type | Description |
|-------|------|-------------|
| owner_id | str | Principal ID who owns this document |
| visibility | enum | PRIVATE, SHARED, INTERNAL, PUBLIC |
| shared_with_users | list[str] | User IDs with direct access |
| shared_with_groups | list[str] | Group IDs with access |
| tenant_id | str? | Optional tenant for isolation |

### Query-Time Filter Logic

```
Return chunks where:
  (owner_id == principal_id) OR
  (visibility IN [PUBLIC, INTERNAL]) OR
  (principal_id IN shared_with_users) OR
  (ANY(member_groups) IN shared_with_groups)

AND (if tenant_id set):
  tenant_id == context.tenant_id
```

---

## Security Considerations

### Threat Analysis

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| ACL bypass via direct vector store access | High | Low | Vector store credentials restricted |
| Privilege escalation via group manipulation | High | Low | Group resolution in trusted host app |
| Information leakage via timing attacks | Medium | Low | Consistent query patterns |
| Stale ACL after permission change | Medium | Medium | Eventual consistency documented |

### Security Measures

- [ ] ACL context is required on all search queries
- [ ] No default visibility - must be explicitly set
- [ ] Group resolution happens in trusted host application
- [ ] System bypass requires explicit flag (logged)
- [ ] delete_by_owner for GDPR right to erasure

### Compliance

- GDPR: delete_by_owner enables right to erasure
- Multi-tenancy: tenant_id provides data isolation

---

## Implementation Plan

### Phases

#### Phase 1: Core ACL Schemas (MVP)

- **Scope**: Add ACL schemas and basic filtering
- **Deliverables**:
  - `rag/core/acl.py` with Visibility, QueryACLContext, ACLFilterSpec
  - Update Document, Chunk with owner_id, visibility
  - Update SearchQuery with required acl_context
  - Update VectorStoreInterface with acl_context parameter
- **Dependencies**: None

#### Phase 2: Group Support

- **Scope**: Add sharing with groups
- **Deliverables**:
  - Add shared_with_users, shared_with_groups to schemas
  - Implement group filter logic
  - Add GroupResolverInterface
  - Create Django bridge (yt_sync/rag_bridge.py)
- **Dependencies**: Phase 1

#### Phase 3: Multi-tenancy & GDPR

- **Scope**: Tenant isolation and deletion capabilities
- **Deliverables**:
  - Add tenant_id to schemas
  - Implement delete_by_owner, delete_by_tenant
  - Implement update_document_acl
- **Dependencies**: Phase 2

### Milestones

| Milestone | Description | Target | Status |
|-----------|-------------|--------|--------|
| ACL Schemas Complete | Core acl.py created | TBD | Not Started |
| MVP Search Filtering | Owner-based filtering works | TBD | Not Started |
| Group Sharing | Group-based access works | TBD | Not Started |
| GDPR Compliance | delete_by_owner implemented | TBD | Not Started |

### Rollback Strategy

- ACL changes are additive - existing code continues to work
- New acl_context field can default to system_context() initially
- Phase rollout allows validation at each step

---

## Open Questions

1. **Group Resolution Caching**
   - Context: Should group memberships be cached?
   - Owner: Architect
   - Status: Open

2. **Default Visibility for Existing Documents**
   - Context: What visibility for documents indexed before ACL?
   - Owner: Product
   - Status: Open (suggest: PRIVATE)

3. **Permission Levels Beyond READ**
   - Context: Do we need WRITE/MANAGE now or later?
   - Owner: Product
   - Status: Open (suggest: defer to future RFC)

4. **Audit Logging**
   - Context: Should ACL checks be logged?
   - Owner: Security
   - Status: Open (suggest: separate RFC)

---

## Implementation Tracking

Task List: [RFC-0001-rag-acl-management-tasks.md](../../../tasks/RFC-0001-rag-acl-management-tasks.md)
Generated: 2025-12-06
Status: See task file for current progress

---

## Decision Record

### Decision

**Status**: APPROVED

**Date**: 2025-12-06

**Approvers**:
- Jeremie

### Decision Summary

Approved Option 1: Metadata Filtering at Vector Store Level. This approach provides the best balance of security (ACL filtering at data layer), performance (native vector store filtering), and flexibility (supports all 4 visibility levels including sharing).

### Key Discussion Points

- Framework independence maintained (no Django imports in rag/core/)
- Denormalization trade-off accepted for query performance
- Group resolution delegated to host application at query time

### Conditions of Approval

- Vector store implementation must support metadata filtering with OR conditions
- Group resolution happens at query time (host app provides group memberships)

### Dissenting Opinions

None recorded.

---

## References

### Related Documents

- [RAG Core Interfaces](../../rag/core/interfaces.py)
- [RAG Core Schemas](../../rag/core/schemas.py)
- [Architect Design Notes](../../.claude/plans/sharded-snacking-floyd-agent-8f10aa97.md)

### External Resources

**Industry Best Practices & Guides:**
- [Pinecone: RAG with Access Control](https://www.pinecone.io/learn/rag-access-control/) - Comprehensive guide on implementing ACL with metadata filtering
- [AWS: Access Control for Vector Stores using Metadata Filtering](https://aws.amazon.com/blogs/machine-learning/access-control-for-vector-stores-using-metadata-filtering-with-knowledge-bases-for-amazon-bedrock/) - Amazon Bedrock Knowledge Bases approach
- [AWS: Authorizing Access to Data with RAG Implementations](https://aws.amazon.com/blogs/security/authorizing-access-to-data-with-rag-implementations/) - Security-focused implementation patterns
- [Databricks: Mastering RAG Chatbot Security with ACL and Metadata Filtering](https://community.databricks.com/t5/technical-blog/mastering-rag-chatbot-security-acl-and-metadata-filtering-with/ba-p/101946) - Enterprise approach with Mosaic AI
- [Paragon: Strategies for Managing Permissions in RAG](https://www.useparagon.com/blog/respecting-3rd-party-data-permissions-with-rag) - Multi-source permission reconciliation
- [Cerbos: Authorization for RAG Applications with LangChain](https://www.cerbos.dev/blog/authorization-for-rag-applications-langchain-chromadb-cerbos) - Open-source authorization patterns

**Enterprise Solutions:**
- [Privacera: Access Control and Data Filtering for Vector DB/RAG](https://privacera.com/newsroom/press-releases/privacera-enhances-ai-governance-solution-with-new-access-control-and-data-filtering-functionality-for-vector-db-rag/) - Enterprise governance with GDPR/CCPA support

**Vector Store Documentation:**
- [Pinecone Metadata Filtering](https://docs.pinecone.io/docs/metadata-filtering)
- [Qdrant Filtering](https://qdrant.tech/documentation/concepts/filtering/)

### Appendix

#### Filter Query Example (Pinecone)

```python
{
    "$or": [
        {"owner_id": {"$eq": "user-123"}},
        {"visibility": {"$in": ["public", "internal"]}},
        {"shared_with_users": {"$in": ["user-123"]}},
        {"shared_with_groups": {"$in": ["team-eng", "team-product"]}}
    ]
}
```

#### Filter Query Example (Qdrant)

```python
Filter(
    should=[
        FieldCondition(key="owner_id", match=MatchValue(value="user-123")),
        FieldCondition(key="visibility", match=MatchAny(any=["public", "internal"])),
        FieldCondition(key="shared_with_users", match=MatchAny(any=["user-123"])),
        FieldCondition(key="shared_with_groups", match=MatchAny(any=["team-eng"])),
    ]
)
```
