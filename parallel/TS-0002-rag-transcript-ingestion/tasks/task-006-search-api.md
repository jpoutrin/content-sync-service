---
id: task-006
component: search-api
wave: 3
deps: [task-005]
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [rag/retrievers/default.py, rag/core/schemas.py, rag/core/acl.py]
---
# task-006: Implement Search API Endpoint

## Scope
CREATE: rag/api/__init__.py, rag/api/views.py, rag/api/serializers.py, rag/api/urls.py, rag/api/tests/__init__.py, rag/api/tests/test_search.py
MODIFY: config/urls.py
BOUNDARY: rag/retrievers/*, rag/core/*, rag/embedders/*, rag/stores/*

## Requirements
- Create `SearchView` as DRF `APIView` at `/api/rag/search`
- GET method accepting `q`, `top_k`, `min_score` query parameters
- Validate `q` is required, 1-500 chars
- Validate `top_k` is 1-100, default 5
- Validate `min_score` is 0.0-1.0, default 0.0
- Build `QueryACLContext` from authenticated user (`request.user`)
- Response format: `{query, results[], total}`
- Return 400 for validation errors
- Return 401 for unauthenticated requests
- Return 500 for internal errors
- Wire up URL in `config/urls.py` at `/api/rag/`

## Checklist
- [ ] `SearchQuerySerializer` validates all parameters (`q`, `top_k`, `min_score`)
- [ ] `q` parameter: required, 1-500 chars
- [ ] `top_k` parameter: optional, 1-100, default 5
- [ ] `min_score` parameter: optional, 0.0-1.0, default 0.0
- [ ] `SearchResultSerializer` with all required fields
- [ ] `SearchView` requires authentication (`IsAuthenticated` permission)
- [ ] `QueryACLContext` built from `request.user.id`
- [ ] `DefaultRetriever` instantiated with configured embedder and store
- [ ] Response format: `{query: str, results: list, total: int}`
- [ ] 400 returned for validation errors with error details
- [ ] 401 returned for unauthenticated requests
- [ ] 500 returned for internal errors with appropriate message
- [ ] URL wired up at `/api/rag/search` in `config/urls.py`
- [ ] Tests cover: authentication, validation, success, errors
- [ ] Test coverage >= 90%
