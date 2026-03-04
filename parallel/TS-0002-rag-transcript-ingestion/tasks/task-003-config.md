---
id: task-003-config
component: Settings
wave: 1
deps: []
blocks: [task-004, task-005, task-009]
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-003-config: RAG Configuration Settings

## Scope
MODIFY:
- config/settings.py

BOUNDARY:
- rag/* (do not create/modify)
- yt_sync/* (do not modify)

## Requirements
- Add RAG_EMBEDDING_PROVIDER setting (local or openai)
- Add RAG_EMBEDDING_MODEL setting (provider-specific model name)
- Add RAG_AUTO_INGEST setting (boolean, default False)
- Add RAG_CHUNK_GAP_THRESHOLD setting (float, default 2.0)
- Add RAG_CHUNK_MAX_CHARS setting (int, default 1000)
- Add RAG_CHUNK_MIN_CHARS setting (int, default 100)
- Add RAG_EMBEDDING_BATCH_SIZE setting (int, default 32)
- Use django-environ for environment variable loading
- Include sensible defaults
- Document each setting with comments

## Checklist
- [ ] RAG_EMBEDDING_PROVIDER setting added
- [ ] RAG_EMBEDDING_MODEL setting added
- [ ] RAG_AUTO_INGEST setting added
- [ ] RAG_CHUNK_GAP_THRESHOLD setting added
- [ ] RAG_CHUNK_MAX_CHARS setting added
- [ ] RAG_CHUNK_MIN_CHARS setting added
- [ ] RAG_EMBEDDING_BATCH_SIZE setting added
- [ ] All settings use django-environ
- [ ] Defaults documented
- [ ] Django app starts correctly with new settings
