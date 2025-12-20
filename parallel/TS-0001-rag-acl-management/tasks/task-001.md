---
id: task-001
component: acl-core
wave: 1
deps: []
agent: python-experts:django-expert
tech_spec: TS-0001
contracts: [contracts/types.py]
---
# task-001: Create ACL Core Module

## Scope
CREATE: rag/core/acl.py
MODIFY: (none)
BOUNDARY: rag/core/schemas.py, rag/core/interfaces.py, rag/stores/*, rag/migrations/*

## Requirements
- Create `Visibility` enum with values: PRIVATE, SHARED, INTERNAL, PUBLIC (inherit from str, Enum)
- Create `QueryACLContext` Pydantic model with fields:
  - `principal_id` (required str): User/service identifier
  - `member_of_groups` (list[str], default []): Group memberships
  - `tenant_id` (Optional[str], default None): Multi-tenant isolation
  - `bypass_acl` (bool, default False): System context flag
- Implement `QueryACLContext.system_context()` class method that returns instance with bypass_acl=True
- Create `ACLFilterSpec` Pydantic model with `to_sql_conditions()` method
- `to_sql_conditions()` must return tuple[str, list] containing SQL WHERE clause and parameters
- SQL generation must use parameterized queries ($1, $2, etc.) to prevent SQL injection
- Support OR conditions for: owner match, visibility check, user sharing, group sharing
- Include tenant filtering with NULL handling (tenant_id IS NULL OR tenant_id = $N)
- Comprehensive docstrings for all classes and methods

## Checklist
- [ ] Visibility enum inherits from str, Enum with all 4 values
- [ ] QueryACLContext validates required principal_id field
- [ ] QueryACLContext.system_context() returns bypass_acl=True
- [ ] ACLFilterSpec.to_sql_conditions() returns tuple[str, list]
- [ ] SQL uses positional parameters ($1, $2, etc.)
- [ ] All models use Pydantic BaseModel
- [ ] Module includes comprehensive docstrings
- [ ] No files modified outside scope
