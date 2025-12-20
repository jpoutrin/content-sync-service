---
id: task-007
component: rag-acl-tests
wave: 4
deps: [task-004, task-006]
blocks: []
agent: python-experts:python-testing-expert
tech_spec: TS-0001
contracts: [contracts/acl-types.py, contracts/vector-store.py, contracts/test-fixtures.py]
---
# task-007: RAG ACL Tests

## Scope
CREATE: rag/tests/__init__.py, rag/tests/test_acl.py, rag/tests/test_schemas.py, rag/tests/test_pgvector.py, yt_sync/tests/test_rag_bridge.py
MODIFY: []
BOUNDARY: rag/core/acl.py, rag/core/schemas.py, rag/core/interfaces.py, rag/stores/pgvector.py, yt_sync/rag_bridge.py

## Requirements
- Create test_acl.py: test Visibility enum values, QueryACLContext validation, system_context(), ACLFilterSpec.to_sql_conditions()
- Create test_schemas.py: test Document ACL defaults, Chunk ACL inheritance via from_document(), SearchQuery acl_context
- Create test_pgvector.py: integration tests for search with ACL filtering, delete_by_owner, update_document_acl
- Create test_rag_bridge.py: test build_acl_context() with mock user
- Use pytest fixtures for test data (users, documents per Tech Spec fixtures)
- Mark integration tests with @pytest.mark.integration

## Checklist
- [ ] test_visibility_enum: verify 4 values and string conversion
- [ ] test_query_acl_context_validation: required principal_id, defaults for other fields
- [ ] test_system_context_bypass: verify bypass_acl=True
- [ ] test_acl_filter_to_sql: verify SQL generation with various inputs
- [ ] test_document_acl_defaults: visibility=PRIVATE, empty share lists
- [ ] test_chunk_from_document_inherits_acl: all 5 ACL fields copied
- [ ] test_search_owner_access: owner retrieves own docs
- [ ] test_search_no_cross_user: user A cannot see user B private docs
- [ ] test_search_shared_user_access: shared docs visible to granted users
- [ ] test_search_shared_group_access: group members can access
- [ ] test_delete_by_owner: all owner chunks deleted
- [ ] test_build_acl_context: correct QueryACLContext from Django user
- [ ] All tests pass with pytest-django
- [ ] Integration tests skip if DATABASE_URL not configured
