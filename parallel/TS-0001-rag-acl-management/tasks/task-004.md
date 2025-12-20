---
id: task-004
component: interface-updates
wave: 2
deps: [task-001]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-004: Update VectorStoreInterface with ACL Methods

## Scope
CREATE: (none)
MODIFY: rag/core/interfaces.py::VectorStoreInterface
BOUNDARY: rag/core/acl.py (owned by task-001), rag/core/schemas.py, rag/stores/*, ChunkerInterface, EmbedderInterface, RetrieverInterface

## Requirements
- Update `VectorStoreInterface.search()` signature: add `acl_context: Optional[QueryACLContext] = None` parameter
- Add abstract method `delete_by_owner(owner_id: str, tenant_id: Optional[str] = None) -> int`
  - Returns count of deleted chunks
  - Supports optional tenant_id filtering
- Add abstract method `update_document_acl(document_id: str, visibility: Optional[Visibility] = None, shared_with_users: Optional[list[str]] = None, shared_with_groups: Optional[list[str]] = None) -> int`
  - Returns count of updated chunks
  - Updates only non-None parameters
- Ensure existing `upsert` and `upsert_batch` methods accept chunks with ACL fields (already compatible via Chunk model)
- All new methods must be decorated with `@abstractmethod`
- Include comprehensive docstrings with Args/Returns/Raises sections
- Import `Visibility` and `QueryACLContext` from `.acl` module
- Do NOT modify other interfaces: ChunkerInterface, EmbedderInterface, RetrieverInterface

## Checklist
- [ ] VectorStoreInterface.search() has acl_context parameter
- [ ] delete_by_owner() is abstract method with correct signature
- [ ] delete_by_owner() returns int (count of deleted chunks)
- [ ] update_document_acl() is abstract method with correct signature
- [ ] update_document_acl() returns int (count of updated chunks)
- [ ] All methods have comprehensive docstrings (Args/Returns/Raises)
- [ ] Imports Visibility and QueryACLContext from .acl
- [ ] ChunkerInterface unchanged
- [ ] EmbedderInterface unchanged
- [ ] RetrieverInterface unchanged
- [ ] No files modified outside scope
