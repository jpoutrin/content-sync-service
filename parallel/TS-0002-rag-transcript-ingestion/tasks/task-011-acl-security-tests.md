---
id: task-011-acl-security-tests
component: ACLSecurityTests
wave: 5
deps: [task-004, task-005, task-006]
blocks: []
agent: python-experts:python-testing-expert
skills: [python-experts:python-style]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-011-acl-security-tests: ACL Security Integration Tests

## Scope
CREATE:
- rag/tests/test_acl_security.py

BOUNDARY:
- all implementation files (read-only for tests)

## Requirements
- Test all 4 visibility levels: PRIVATE, SHARED, INTERNAL, PUBLIC
- Test tenant isolation (users can't see other tenants' content)
- Test admin bypass_acl functionality
- Use real pgvector extension (not mocked)
- Create test fixtures for multiple users, tenants, videos
- Test ingestion preserves ACL correctly
- Test retrieval respects ACL correctly
- Test API endpoint respects ACL
- Verify cross-tenant queries return nothing
- Verify PUBLIC content visible to all in tenant

## Checklist
- [ ] PRIVATE visibility test passes
- [ ] SHARED visibility test passes
- [ ] INTERNAL visibility test passes
- [ ] PUBLIC visibility test passes
- [ ] Tenant isolation verified
- [ ] Cross-tenant queries blocked
- [ ] Admin bypass_acl works
- [ ] Ingestion ACL inheritance correct
- [ ] Retrieval ACL filtering correct
- [ ] API endpoint ACL enforced
- [ ] Integration tests use real pgvector
- [ ] Test fixtures complete
- [ ] Type hints complete
- [ ] Docstrings written
