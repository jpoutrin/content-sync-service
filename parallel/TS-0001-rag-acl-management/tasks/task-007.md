---
id: task-007
component: django-bridge
wave: 3
deps: [task-005]
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-007: Create Django Bridge for ACL Context Building

## Scope
CREATE: yt_sync/rag_bridge.py
MODIFY: (none)
BOUNDARY: rag/core/*, rag/stores/*, yt_sync/models.py, yt_sync/views.py

## Requirements
- Create `build_acl_context(user: User) -> QueryACLContext` function
  - Accept Django User instance
  - Extract principal_id from user.id or user.username
  - Resolve group memberships via `user.groups.all()`
  - Extract tenant_id if present on user model (check hasattr, return None if not present)
  - Return fully populated QueryACLContext
- Create `system_acl_context() -> QueryACLContext` function for admin/system operations
  - Return QueryACLContext.system_context() with bypass_acl=True
- Create `get_vector_store() -> PgVectorStore` factory function
  - Read database connection from Django settings (settings.DATABASES['default'])
  - Construct connection string from settings components
  - Return configured PgVectorStore instance
  - Handle connection pooling if applicable
- Include comprehensive docstrings explaining integration patterns for Django views
- Document example usage in module docstring
- Use type hints for all function signatures
- Import Django User model: `from django.contrib.auth.models import User`
- Import settings: `from django.conf import settings`

## Checklist
- [ ] build_acl_context() accepts Django User instance
- [ ] Groups resolved from user.groups.all()
- [ ] Groups converted to list of group names or IDs
- [ ] tenant_id extracted with hasattr check (returns None if not present)
- [ ] Returns fully populated QueryACLContext
- [ ] system_acl_context() returns bypass_acl=True context
- [ ] get_vector_store() reads connection from Django settings
- [ ] get_vector_store() returns PgVectorStore instance
- [ ] All functions include type hints
- [ ] Docstrings explain integration usage with examples
- [ ] Module docstring includes usage examples
- [ ] No files modified outside scope
