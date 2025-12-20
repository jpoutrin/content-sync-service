---
id: task-001
component: rag-core-acl
wave: 1
deps: []
blocks: [task-002, task-003]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/acl-types.py, contracts/vector-store.py]
---
# task-001: RAG Core ACL

## Scope
CREATE: rag/core/acl.py
MODIFY: rag/core/__init__.py
BOUNDARY: rag/core/schemas.py, rag/core/interfaces.py

## Requirements
- Create `Visibility` enum with values: PRIVATE, SHARED, INTERNAL, PUBLIC
- Create `QueryACLContext` pydantic model with:
  - `principal_id` (str, required)
  - `member_of_groups` (list[str], default [])
  - `tenant_id` (Optional[str], default None)
  - `bypass_acl` (bool, default False)
- Add `system_context()` classmethod returning QueryACLContext with principal_id='system' and bypass_acl=True
- Create `ACLFilterSpec` pydantic model with:
  - `principal_id` (str)
  - `group_ids` (list[str])
  - `tenant_id` (Optional[str])
  - `include_public` (bool)
  - `include_internal` (bool)
- Implement `to_sql_conditions()` method returning tuple[str, list] for pgvector SQL WHERE clause
- SQL must use PostgreSQL positional parameters ($1, $2, etc.)
- Export Visibility, QueryACLContext, ACLFilterSpec from rag/core/__init__.py

## Checklist
- [ ] Visibility enum inherits from (str, Enum) for JSON serialization
- [ ] QueryACLContext validates principal_id is non-empty string
- [ ] ACLFilterSpec.to_sql_conditions() handles: owner match, visibility IN clause, shared_with_users array contains, shared_with_groups array overlap (&&), tenant filter
- [ ] SQL conditions use OR for access rules, AND for tenant isolation
- [ ] All types have docstrings per Tech Spec
- [ ] rag/core/__init__.py exports: Visibility, QueryACLContext, ACLFilterSpec
- [ ] No circular imports with schemas.py
