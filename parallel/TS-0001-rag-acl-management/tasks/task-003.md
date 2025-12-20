---
id: task-003
component: schema-updates
wave: 2
deps: [task-001]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/types.py]
---
# task-003: Update Document and Chunk Schemas with ACL Fields

## Scope
CREATE: (none)
MODIFY: rag/core/schemas.py::Document, rag/core/schemas.py::Chunk, rag/core/schemas.py::SearchQuery, rag/core/__init__.py
BOUNDARY: rag/core/acl.py (owned by task-001), rag/core/interfaces.py, rag/stores/*

## Requirements
- Add ACL fields to `Document` model:
  - `owner_id` (required str): Document owner identifier
  - `visibility` (Visibility, default PRIVATE): Access level
  - `shared_with_users` (list[str], default []): User share list
  - `shared_with_groups` (list[str], default []): Group share list
  - `tenant_id` (Optional[str], default None): Multi-tenant isolation
- Add same ACL fields to `Chunk` model with same types and defaults
- Add `Chunk.from_document()` classmethod that accepts parent Document and copies all ACL fields
- Update `SearchQuery` model: add `acl_context` field (QueryACLContext, required, no default)
- Update `rag/core/__init__.py` exports to include `Visibility`, `QueryACLContext` from acl module
- Maintain backward compatibility: preserve all existing fields unchanged
- Import `Visibility` and `QueryACLContext` from `.acl` module

## Checklist
- [ ] Document has owner_id as required field (no default)
- [ ] Document.visibility defaults to Visibility.PRIVATE
- [ ] Document has shared_with_users with default []
- [ ] Document has shared_with_groups with default []
- [ ] Document has tenant_id as Optional[str]
- [ ] Chunk has identical ACL fields with same types/defaults
- [ ] Chunk.from_document() copies all 5 ACL fields from parent
- [ ] SearchQuery.acl_context is required (no default value)
- [ ] All existing fields preserved unchanged
- [ ] __init__.py exports Visibility and QueryACLContext
- [ ] Type hints complete and correct
- [ ] No files modified outside scope
