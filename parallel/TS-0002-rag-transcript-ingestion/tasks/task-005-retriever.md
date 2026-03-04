---
id: task-005-retriever
component: DefaultRetriever
wave: 2
deps: [task-002, task-003]
blocks: [task-006, task-007, task-010, task-011]
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev, python-experts:django-api, python-experts:documentation-research]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-005-retriever: Default Retriever Implementation

## Scope
CREATE:
- rag/retrievers/__init__.py
- rag/retrievers/default.py
- rag/retrievers/tests/__init__.py
- rag/retrievers/tests/test_default.py

BOUNDARY:
- rag/core/* (do not modify)
- rag/stores/* (do not modify)
- rag/chunkers/* (do not modify)

## Requirements
- Implement RetrieverInterface from rag/core/interfaces.py
- Implement retrieve(SearchQuery) -> list[SearchResult]
- Embed query text using configured embedder
- Search vector store with ACL context
- Enrich results with timestamp_url metadata
- Format timestamp_url as: {video_url}&t={start_time}s
- Support top_k and min_score filtering
- Handle bypass_acl for admin queries
- Return results sorted by score (descending)

## Checklist
- [ ] DefaultRetriever implements RetrieverInterface
- [ ] retrieve() method works correctly
- [ ] Query embedding works
- [ ] Vector search respects ACL
- [ ] timestamp_url format correct
- [ ] top_k filtering works
- [ ] min_score filtering works
- [ ] bypass_acl supported
- [ ] Results sorted by score
- [ ] Unit tests pass
- [ ] Type hints complete
- [ ] Docstrings written
