---
id: task-005
component: pgvector-store
wave: 3
deps: [task-003, task-004]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-005: Implement PgVectorStore with ACL Filtering

## Scope
CREATE: rag/stores/__init__.py, rag/stores/pgvector.py
MODIFY: (none)
BOUNDARY: rag/core/*, rag/migrations/*, yt_sync/*

## Requirements
- Create `PgVectorStore` class implementing `VectorStoreInterface`
- Constructor parameters:
  - `connection_string` (str): PostgreSQL connection URL
  - `table_name` (str, default 'rag_embeddings'): Table name
  - `dimensions` (int, default 1536): Embedding vector dimensions
- Implement `search()` method:
  - Use native SQL with ACL filtering via `ACLFilterSpec.to_sql_conditions()`
  - Validate that `acl_context` is not None (unless bypass_acl=True)
  - Raise ValueError if acl_context is None and bypass not enabled
  - Bypass ACL filtering when acl_context.bypass_acl=True
  - Use cosine distance for vector similarity
- Implement `upsert()` and `upsert_batch()` for chunks with embeddings
- Implement `delete()`, `delete_by_document()`, `delete_by_owner()`
- Implement `update_document_acl()` with atomic UPDATE statement
  - Update only non-None parameters
  - Return count of updated rows
- Use context managers for connection handling (with statement)
- All SQL queries must use parameterized queries to prevent SQL injection
- Use psycopg2 for database connections

## Checklist
- [ ] PgVectorStore inherits from VectorStoreInterface
- [ ] All abstract methods implemented
- [ ] search() validates acl_context requirement
- [ ] search() bypasses ACL when bypass_acl=True
- [ ] search() uses ACLFilterSpec.to_sql_conditions()
- [ ] SQL uses parameterized queries throughout
- [ ] Connection management uses context managers (with)
- [ ] delete_by_owner() supports optional tenant_id
- [ ] update_document_acl() returns count of updated rows
- [ ] update_document_acl() updates only non-None parameters
- [ ] upsert_batch() handles ACL fields correctly
- [ ] No files modified outside scope
