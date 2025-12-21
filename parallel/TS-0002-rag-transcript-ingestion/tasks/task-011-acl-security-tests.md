---
id: task-011
component: acl-security-tests
wave: 5
deps: [task-004, task-005, task-006]
agent: python-experts:python-testing-expert
tech_spec: TS-0002
contracts: [rag/services/ingestion.py, rag/retrievers/default.py, rag/api/views.py, rag/core/acl.py, yt_sync/models.py]
---
# task-011: Implement ACL Security Integration Tests

## Scope
CREATE: rag/tests/__init__.py, rag/tests/test_acl_security.py, rag/tests/conftest.py
MODIFY: none
BOUNDARY: rag/services/*, rag/retrievers/*, rag/api/*, rag/core/*, yt_sync/models.py

## Requirements
- Create comprehensive ACL security test suite
- Test PRIVATE visibility: only owner can search/retrieve
- Test SHARED visibility: owner and shared_with_users/groups can access
- Test INTERNAL visibility: all authenticated users in same tenant
- Test PUBLIC visibility: anyone including anonymous can access
- Test tenant isolation: different tenants cannot access each other
- Test admin bypass: staff users with bypass_acl=True see everything
- Create multi-user test fixtures (owner, shared_user, other_user, admin)
- Create multi-tenant test fixtures
- Test via API endpoint to verify full stack ACL enforcement

## Checklist
- [ ] conftest.py with pytest fixtures for users, videos, indexed content
- [ ] sample_transcript_data fixture with realistic timed segments
- [ ] video_with_transcript factory fixture
- [ ] indexed_video fixture that runs full ingestion
- [ ] multi_user_scenario fixture with owner, shared_user, other_user
- [ ] PRIVATE visibility tests: owner sees, others don't
- [ ] SHARED visibility tests: owner and shared users/groups see
- [ ] INTERNAL visibility tests: same tenant authenticated users see
- [ ] PUBLIC visibility tests: everyone sees including anonymous
- [ ] Tenant isolation tests: cross-tenant access blocked
- [ ] Admin bypass tests: staff with bypass_acl sees all
- [ ] API tests using DRF test client with authentication
- [ ] All tests marked with @pytest.mark.integration
- [ ] Uses IngestionService contract from rag/services/ingestion.py
- [ ] Uses DefaultRetriever contract from rag/retrievers/default.py
- [ ] Uses SearchView contract from rag/api/views.py
- [ ] Uses Visibility and QueryACLContext from rag/core/acl.py
- [ ] Uses Video, Source, User models from yt_sync/models.py
