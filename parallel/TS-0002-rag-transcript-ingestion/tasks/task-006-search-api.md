---
id: task-006-search-api
component: SearchAPI
wave: 3
deps: [task-005]
blocks: [task-011]
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev, python-experts:django-api, python-experts:documentation-research]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-006-search-api: RAG Search API Endpoint

## Scope
CREATE:
- rag/api/__init__.py
- rag/api/views.py
- rag/api/serializers.py
- rag/api/urls.py
- rag/api/tests/__init__.py
- rag/api/tests/test_search.py

MODIFY:
- config/urls.py (register rag.api.urls)

BOUNDARY:
- rag/core/* (do not modify)
- rag/stores/* (do not modify)
- rag/services/* (do not modify)

## Requirements
- Implement GET /api/rag/search endpoint
- Query parameters: q (required), top_k (default 10), min_score (default 0.7)
- Use DRF for serializers and views
- Require authentication (IsAuthenticated)
- Build QueryACLContext from request.user
- Return SearchResult list as JSON
- Validate query parameters
- Handle empty results gracefully
- Include proper error responses

## Checklist
- [ ] SearchView implemented with DRF
- [ ] Query parameter validation works
- [ ] Authentication required
- [ ] ACL context built from request.user
- [ ] Retriever integration works
- [ ] Serializers correctly format results
- [ ] URL registered in config/urls.py
- [ ] API tests pass
- [ ] Error handling works
- [ ] Type hints complete
- [ ] Docstrings written
