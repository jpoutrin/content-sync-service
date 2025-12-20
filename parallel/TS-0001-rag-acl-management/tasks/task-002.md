---
id: task-002
component: acl-core-tests
wave: 1
deps: []
blocks: [task-003, task-004, task-005]
agent: python-experts:python-testing-expert
tech_spec: TS-0001
contracts: [contracts/types.py]
---
# task-002: Unit Tests for ACL Core Module

## Scope
CREATE: rag/core/tests/__init__.py, rag/core/tests/test_acl.py
MODIFY: (none)
BOUNDARY: rag/core/acl.py (owned by task-001), rag/core/schemas.py, rag/stores/*

## Requirements
- Test `Visibility` enum values and string conversion
- Test `QueryACLContext` required fields validation (missing principal_id raises error)
- Test `QueryACLContext` default values for optional fields
- Test `QueryACLContext.system_context()` factory method returns bypass_acl=True
- Test `ACLFilterSpec.to_sql_conditions()` output format is tuple[str, list]
- Test SQL generation for various ACL scenarios:
  - Owner only (no groups, no sharing)
  - With group memberships
  - With tenant isolation
  - System context (bypass)
- Test parameter ordering and count matches SQL placeholders
- Verify SQL injection protection with malicious inputs (e.g., "'; DROP TABLE--")
- Use pytest fixtures for reusable test data
- Minimum 90% code coverage for rag/core/acl.py

## Checklist
- [ ] test_visibility_enum_values() passes
- [ ] test_visibility_enum_string_conversion() passes
- [ ] test_query_acl_context_required_fields() passes
- [ ] test_query_acl_context_defaults() passes
- [ ] test_system_context_bypass() passes
- [ ] test_acl_filter_spec_basic_sql() passes
- [ ] test_acl_filter_spec_with_groups() passes
- [ ] test_acl_filter_spec_with_tenant() passes
- [ ] test_sql_injection_protection() passes
- [ ] pytest rag/core/tests/test_acl.py passes
- [ ] Coverage >= 90% for rag/core/acl.py
- [ ] No files modified outside scope
