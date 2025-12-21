---
id: task-004-ingestion-service
component: IngestionService
wave: 2
deps: [task-001, task-002, task-003]
blocks: [task-008, task-009, task-010, task-011]
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev, python-experts:django-api, python-experts:documentation-research]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-004-ingestion-service: RAG Ingestion Service

## Scope
CREATE:
- rag/services/__init__.py
- rag/services/ingestion.py
- rag/services/tests/__init__.py
- rag/services/tests/test_ingestion.py

BOUNDARY:
- rag/core/* (do not modify)
- rag/stores/* (do not modify)
- yt_sync/models.py (read-only)

## Requirements
- Orchestrate chunker, embedder, and vector store
- Implement ingest_video(Video) -> int (returns chunk count)
- Build Document from Video metadata
- Set ACL from video.source.user (tenant, visibility)
- Use document ID format: video:{pk}
- Extract transcript from video.transcript_text
- Chunk transcript using TranscriptChunker
- Embed chunks using configured embedder
- Store chunks in VectorStore
- Handle videos without transcripts gracefully
- Support re-ingestion (clear existing chunks first)

## Checklist
- [ ] IngestionService class created
- [ ] ingest_video() method works end-to-end
- [ ] Document built correctly from Video
- [ ] ACL inherited from video.source.user
- [ ] Document ID format: video:{pk}
- [ ] Transcript chunking works
- [ ] Embedding works
- [ ] Vector storage works
- [ ] Re-ingestion clears old chunks
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Type hints complete
- [ ] Docstrings written
