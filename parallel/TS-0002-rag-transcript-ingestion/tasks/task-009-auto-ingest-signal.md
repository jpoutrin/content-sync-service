---
id: task-009-auto-ingest-signal
component: AutoIngestSignal
wave: 4
deps: [task-003, task-004]
blocks: []
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-009-auto-ingest-signal: Automatic Ingestion Signal

## Scope
CREATE:
- yt_sync/signals.py
- yt_sync/tests/test_signals.py

MODIFY:
- yt_sync/apps.py (import signals in ready())

BOUNDARY:
- rag/api/* (do not modify)
- rag/core/* (do not modify)

## Requirements
- Implement post_save signal for Video model
- Trigger when transcript_status changes to COMPLETED
- Check RAG_AUTO_INGEST setting (skip if False)
- Queue Django-Q async task for ingestion
- Prevent duplicate tasks (check if already queued/processing)
- Handle signal errors gracefully (log, don't crash)
- Test with RAG_AUTO_INGEST enabled/disabled
- Verify signal registration in apps.py

## Checklist
- [ ] post_save signal created
- [ ] Triggers on transcript_status=COMPLETED
- [ ] RAG_AUTO_INGEST setting respected
- [ ] Django-Q task queued correctly
- [ ] Duplicate prevention works
- [ ] Error handling implemented
- [ ] Signal registered in apps.py
- [ ] Tests with setting enabled
- [ ] Tests with setting disabled
- [ ] Type hints complete
- [ ] Docstrings written
