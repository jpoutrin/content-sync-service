---
id: task-006
component: yt-sync-rag-bridge
wave: 3
deps: [task-001]
blocks: [task-007]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/acl-types.py, contracts/user-bridge.py]
---
# task-006: YT Sync RAG Bridge

## Scope
CREATE: yt_sync/rag_bridge.py
MODIFY: []
BOUNDARY: yt_sync/models.py, yt_sync/user_model.py, rag/core/acl.py

## Requirements
- Create `build_acl_context(user: User) -> QueryACLContext` function
- Resolve user's group memberships from Django's auth groups
- Handle tenant_id if present on user model (getattr with None default)
- Create `get_system_context() -> QueryACLContext` function returning QueryACLContext.system_context()
- Add type hints for all functions
- Handle case where user is None or anonymous

## Checklist
- [ ] build_acl_context() extracts user.id as principal_id (convert UUID to str)
- [ ] build_acl_context() resolves groups via user.groups.all()
- [ ] build_acl_context() converts group IDs to strings
- [ ] build_acl_context() handles tenant_id via getattr(user, 'tenant_id', None)
- [ ] get_system_context() returns QueryACLContext with bypass_acl=True
- [ ] Anonymous user handling returns appropriate context or raises
- [ ] All functions have type hints and docstrings
- [ ] Imports from rag.core.acl work correctly
