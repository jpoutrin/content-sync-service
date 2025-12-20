---
id: task-003
component: rag-core-interfaces-update
wave: 2
deps: [task-001, task-002]
blocks: [task-004]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/acl-types.py, contracts/vector-store.py]
---
# task-003: RAG Core Interfaces Update

## Scope
CREATE: []
MODIFY: rag/core/interfaces.py
BOUNDARY: rag/core/acl.py, rag/core/schemas.py

## Requirements
- Import QueryACLContext and Visibility from rag.core.acl
- Update `VectorStoreInterface.search()` signature to add `acl_context: Optional[QueryACLContext] = None` parameter
- Add `delete_by_owner(owner_id: str, tenant_id: Optional[str] = None) -> int` abstract method for GDPR deletion
- Add `update_document_acl(document_id: str, visibility: Optional[Visibility] = None, shared_with_users: Optional[list[str]] = None, shared_with_groups: Optional[list[str]] = None) -> int` abstract method
- Add comprehensive docstrings explaining ACL behavior and GDPR compliance

## Checklist
- [ ] VectorStoreInterface.search() has acl_context parameter with Optional type
- [ ] search() docstring explains ValueError if acl_context is None and bypass not enabled
- [ ] delete_by_owner() returns count of deleted chunks
- [ ] update_document_acl() returns count of updated chunks
- [ ] All new methods are @abstractmethod decorated
- [ ] Existing methods (upsert, upsert_batch, delete, delete_by_document) preserved unchanged
- [ ] Import statements added for QueryACLContext, Visibility
