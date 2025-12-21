---
id: task-002
component: embedder
wave: 1
deps: []
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [rag/core/interfaces.py, rag/core/schemas.py]
---
# task-002: Implement LiteLLMEmbedder

## Scope
CREATE: rag/embedders/__init__.py, rag/embedders/litellm.py, rag/embedders/tests/__init__.py, rag/embedders/tests/test_litellm.py
MODIFY: none
BOUNDARY: rag/core/interfaces.py, rag/core/schemas.py, rag/chunkers/*, rag/services/*, rag/stores/*

## Requirements
- Implement `LiteLLMEmbedder` class implementing `EmbedderInterface`
- Support 'local' provider using `sentence-transformers/all-MiniLM-L6-v2` (384 dims)
- Support 'openai' provider using `text-embedding-3-small` (1536 dims) via LiteLLM
- Implement `embed(text: str) -> list[float]` for single text
- Implement `embed_batch(texts: list[str]) -> list[list[float]]` for batch
- Respect `batch_size` from `settings.RAG_EMBEDDING_BATCH_SIZE` (default 50)
- Implement `model_name` and `dimensions` properties
- Handle API timeouts and rate limits with retry logic (exponential backoff)
- Raise `EmbeddingError` with descriptive messages on failures

## Checklist
- [ ] `LiteLLMEmbedder` implements `EmbedderInterface`
- [ ] Local provider uses `sentence-transformers` directly, returns 384-dim vectors
- [ ] OpenAI provider uses `litellm.embedding()`, returns 1536-dim vectors
- [ ] `embed_batch` splits input into batches of `batch_size`
- [ ] API timeout raises `EmbeddingError` with descriptive message
- [ ] Rate limit (429) triggers retry with exponential backoff
- [ ] `model_name` property returns configured model name
- [ ] `dimensions` property returns correct dimension count (384 or 1536)
- [ ] Tests mock external APIs (no real API calls)
- [ ] Test coverage >= 90%
