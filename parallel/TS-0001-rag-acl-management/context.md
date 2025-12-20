# Context: RAG ACL Management

## Project Overview

Content Sync Service is a Django-based application for synchronizing and analyzing YouTube content. The service enables users to sync their YouTube videos, process content for RAG (Retrieval-Augmented Generation), and perform semantic searches across their video libraries.

## Technology Stack

- **Framework**: Django 5.x
- **Database**: PostgreSQL (via Supabase)
- **Vector Store**: pgvector extension
- **Python**: 3.12
- **Task Queue**: Django-Q (ORM backend)

## Current Architecture

### RAG Module (`rag/core/`)

The existing RAG module provides basic document processing and vector search capabilities:

- **Schemas** (`rag/core/schemas.py`):
  - `Document`: Represents a processable document with metadata
  - `Chunk`: Text segments with embeddings for vector search
  - `SearchQuery`: Query parameters for semantic search

- **Interfaces** (`rag/core/interfaces.py`):
  - `VectorStoreInterface`: Abstract base for vector storage implementations
  - Defines methods: `add_documents()`, `search()`, `delete_documents()`

- **Current Limitation**: No access control - all queries return all documents

### YouTube Sync Module (`yt_sync/`)

Manages YouTube content synchronization with Django models:

- **User Model**: Django's built-in User model for authentication
- **Source Model**: YouTube channels/playlists owned by users
- **Video Model**: Individual videos linked to sources and users
- **Relationship**: `Video.user` → `User` (ForeignKey, owner relationship)

## Tech Spec Goal

Add multi-user access control to the RAG system to enable secure, user-scoped queries. Users should only retrieve:
1. Documents they own (created from their YouTube videos)
2. Documents explicitly shared with them
3. Public documents (if visibility settings allow)

## Key Requirements

1. **ACL Context**: Query-time context specifying user identity and permissions
2. **Visibility Levels**: Private, shared, public document classifications
3. **Filter Specifications**: PostgreSQL-compatible WHERE clauses for ACL enforcement
4. **Vector Store Integration**: Extend `VectorStoreInterface` with ACL-aware methods
5. **Bridge Layer**: Connect `yt_sync` models to RAG ACL system

## Constraints

- Must maintain backward compatibility with existing `VectorStoreInterface`
- ACL filtering must happen at database level (not post-query filtering)
- No breaking changes to existing `Document` and `Chunk` schemas
- Must integrate with Django's existing User model
- PostgreSQL-specific optimizations allowed (pgvector + native arrays)

## Success Criteria

1. User A cannot retrieve User B's private documents via RAG queries
2. Shared documents are accessible only to authorized users
3. Public documents are accessible to all authenticated users
4. Performance overhead < 50ms for ACL filtering on 100k+ documents
5. All existing RAG functionality continues to work unchanged
