---
id: task-003
component: config
wave: 1
deps: []
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: []
---
# task-003: Add RAG Configuration Settings

## Scope
CREATE: none
MODIFY: config/settings.py
BOUNDARY: rag/*, yt_sync/*, manage.py

## Requirements
- Add `RAG_EMBEDDING_PROVIDER` setting (default: 'local')
- Add `RAG_EMBEDDING_MODEL` setting (default: 'sentence-transformers/all-MiniLM-L6-v2')
- Add `RAG_AUTO_INGEST` boolean (default: True)
- Add `RAG_CHUNK_GAP_THRESHOLD` float (default: 2.0)
- Add `RAG_CHUNK_MAX_CHARS` int (default: 1000)
- Add `RAG_CHUNK_MIN_CHARS` int (default: 100)
- Add `RAG_EMBEDDING_BATCH_SIZE` int (default: 50)
- Add `OPENAI_API_KEY` setting (from environment)
- Group all settings with comment header `# RAG Configuration`
- Use `environ.Env` with appropriate type casting for each setting

## Checklist
- [ ] `RAG_EMBEDDING_PROVIDER` setting added with default 'local'
- [ ] `RAG_EMBEDDING_MODEL` setting added with default 'sentence-transformers/all-MiniLM-L6-v2'
- [ ] `RAG_AUTO_INGEST` boolean setting added with default True
- [ ] `RAG_CHUNK_GAP_THRESHOLD` float setting added with default 2.0
- [ ] `RAG_CHUNK_MAX_CHARS` int setting added with default 1000
- [ ] `RAG_CHUNK_MIN_CHARS` int setting added with default 100
- [ ] `RAG_EMBEDDING_BATCH_SIZE` int setting added with default 50
- [ ] `OPENAI_API_KEY` setting added (reads from environment)
- [ ] All settings grouped under `# RAG Configuration` comment
- [ ] Django server starts without errors (`python manage.py runserver`)
