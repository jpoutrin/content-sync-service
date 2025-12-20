---
id: task-002
component: rag-core-schemas-update
wave: 1
deps: []
blocks: [task-003, task-004]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/acl-types.py, contracts/document-schema.py]
---
# task-002: RAG Core Schemas Update

## Scope
CREATE: []
MODIFY: rag/core/schemas.py
BOUNDARY: rag/core/__init__.py

## Requirements
- Import Visibility from rag.core.acl (conditional import to avoid circular deps)
- Add ACL fields to Document:
  - `owner_id` (str, required)
  - `visibility` (Visibility, default PRIVATE)
  - `shared_with_users` (list[str], default [])
  - `shared_with_groups` (list[str], default [])
  - `tenant_id` (Optional[str], default None)
- Add same ACL fields to Chunk model (denormalized from Document)
- Add `from_document()` classmethod to Chunk that creates chunk inheriting ACL fields from parent Document
- Update SearchQuery to include acl_context field using forward reference to avoid circular import

## Checklist
- [ ] Document model has all 5 ACL fields with correct types and defaults
- [ ] Chunk model has all 5 ACL fields with correct types and defaults
- [ ] Chunk.from_document() copies owner_id, visibility, shared_with_users (copy), shared_with_groups (copy), tenant_id
- [ ] SearchQuery has acl_context field (can be Optional for backward compat initially)
- [ ] Visibility import uses TYPE_CHECKING guard or late import to prevent circular dependency
- [ ] All new fields have Field() with description
- [ ] Existing fields preserved (id, content, metadata, source_id, etc.)
