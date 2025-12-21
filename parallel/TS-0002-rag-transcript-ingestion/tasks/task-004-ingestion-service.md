---
id: task-004
component: ingestion-service
wave: 2
deps: [task-001, task-002, task-003]
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [rag/chunkers/transcript.py, rag/embedders/litellm.py, rag/stores/pgvector.py, yt_sync/models.py]
---
# task-004: Implement IngestionService

## Scope
CREATE: rag/services/__init__.py, rag/services/ingestion.py, rag/services/tests/__init__.py, rag/services/tests/test_ingestion.py
MODIFY: none
BOUNDARY: rag/chunkers/*, rag/embedders/*, rag/stores/*, yt_sync/models.py, rag/core/*

## Requirements
- Implement `IngestionService` class orchestrating chunking, embedding, storage
- Constructor accepts `chunker`, `embedder`, `store` (dependency injection)
- Implement `ingest_video(video: Video) -> int` returning chunk count
- Build `Document` from `Video` with `owner_id` from `video.source.user.id`
- Set `Document.visibility` to `PRIVATE` by default
- Include video metadata in `Document.metadata`: `youtube_video_id`, `title`, `url`
- Handle `ValueError` if `video.transcript_data` is None
- Log ingestion progress and chunk count using Django logging
- Create `Embedding` objects with correct `chunk_id`, `vector`, `model`, `dimensions`
- Call `store.upsert_batch` to persist embeddings

## Checklist
- [ ] `IngestionService` constructor with `chunker`, `embedder`, `store` parameters
- [ ] `ingest_video(video: Video) -> int` implemented
- [ ] `Document.id` follows convention `video:{video.pk}`
- [ ] `Document.owner_id = str(video.source.user.id)`
- [ ] `Document.visibility` set to `PRIVATE`
- [ ] `Document.metadata` includes `youtube_video_id`, `title`, `url`
- [ ] `Embedding` objects created with correct `chunk_id`, `vector`, `model`, `dimensions`
- [ ] `store.upsert_batch` called to persist embeddings
- [ ] `ValueError` raised if `video.transcript_data` is None with clear message
- [ ] Ingestion progress logged (start, chunk count, completion)
- [ ] Tests mock `chunker`, `embedder`, `store`
- [ ] Test coverage >= 90%
