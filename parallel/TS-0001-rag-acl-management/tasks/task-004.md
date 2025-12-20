---
id: task-004
component: rag-stores-pgvector
wave: 2
deps: [task-001, task-002]
blocks: [task-005, task-007]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/acl-types.py, contracts/vector-store.py]
---
# task-004: RAG Stores PgVector

## Scope
CREATE: rag/stores/__init__.py, rag/stores/pgvector.py
MODIFY: []
BOUNDARY: rag/core/interfaces.py, rag/core/schemas.py, rag/core/acl.py

## Requirements
- Create rag/stores/__init__.py exporting PgVectorStore
- Create PgVectorStore class implementing VectorStoreInterface
- Constructor takes connection_string, table_name='rag_embeddings', dimensions=1536
- Implement `_get_connection()` method using psycopg2.connect()
- Implement `search()` with native SQL ACL filtering using ACLFilterSpec.to_sql_conditions()
- Implement `upsert()` and `upsert_batch()` using psycopg2.extras.execute_values
- Implement `delete_by_owner()` with SQL DELETE and owner_id filter
- Implement `delete_by_document()` with SQL DELETE and document_id filter
- Implement `delete()` for chunk_ids
- Implement `update_document_acl()` with SQL UPDATE for ACL fields

## Checklist
- [ ] PgVectorStore inherits from VectorStoreInterface
- [ ] search() raises ValueError if acl_context is None (unless bypass_acl=True)
- [ ] search() uses cosine similarity via embedding <=> operator
- [ ] search() returns list[tuple[Chunk, float]] with similarity scores
- [ ] upsert_batch() handles ACL fields in INSERT
- [ ] delete_by_owner() supports optional tenant_id scope
- [ ] update_document_acl() builds dynamic UPDATE query based on provided fields
- [ ] All methods use context managers for connection/cursor
- [ ] Transactions committed after write operations
- [ ] rag/stores/__init__.py exports PgVectorStore
