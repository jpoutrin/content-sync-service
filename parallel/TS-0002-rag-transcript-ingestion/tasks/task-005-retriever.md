---
id: task-005
component: retriever
wave: 2
deps: [task-002]
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [rag/core/interfaces.py, rag/core/schemas.py, rag/embedders/litellm.py, rag/stores/pgvector.py]
---
# task-005: Implement DefaultRetriever

## Scope
CREATE: rag/retrievers/__init__.py, rag/retrievers/default.py, rag/retrievers/tests/__init__.py, rag/retrievers/tests/test_default.py
MODIFY: none
BOUNDARY: rag/core/interfaces.py, rag/core/schemas.py, rag/embedders/*, rag/stores/*, rag/chunkers/*

## Requirements
- Implement `DefaultRetriever` implementing `RetrieverInterface`
- Constructor accepts `embedder`, `store`
- Implement `retrieve(query: SearchQuery) -> list[SearchResult]`
- Generate query embedding using `embedder.embed(query.text)`
- Call `store.search` with ACL context from query
- Enrich results with `timestamp_url`: `https://youtube.com/watch?v={youtube_video_id}&t={start_time}`
- Respect `query.min_score` and `query.top_k` when calling store
- Gracefully handle missing `youtube_video_id` in chunk metadata (skip timestamp_url)
- Return empty list if no results found

## Checklist
- [ ] `DefaultRetriever` implements `RetrieverInterface.retrieve(query)`
- [ ] Constructor accepts `embedder`, `store` parameters
- [ ] Query embedding generated via `embedder.embed(query.text)`
- [ ] `store.search` called with correct parameters including `acl_context`
- [ ] `_enrich_results` helper adds `timestamp_url` when `youtube_video_id` exists
- [ ] `timestamp_url` format: `https://youtube.com/watch?v={id}&t={seconds}`
- [ ] Missing `youtube_video_id` handled gracefully (no `timestamp_url` field)
- [ ] Empty results return empty list (no errors)
- [ ] `query.min_score` and `query.top_k` passed to store.search
- [ ] Tests mock `embedder` and `store`
- [ ] Test coverage >= 90%
