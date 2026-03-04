---
id: task-008-cli-ingest
component: RAGIngestCommand
wave: 3
deps: [task-004]
blocks: []
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-008-cli-ingest: RAG Ingest CLI Command

## Scope
CREATE:
- rag/management/commands/rag_ingest.py
- rag/management/commands/tests/test_rag_ingest.py

BOUNDARY:
- rag/api/* (do not modify)
- rag/retrievers/* (do not modify)

## Requirements
- Implement python manage.py rag_ingest
- Option: --video-id <id> (ingest single video)
- Option: --source <source_id> (ingest all videos from source)
- Option: --all (ingest all videos)
- Option: --reingest (re-ingest existing videos)
- Option: --dry-run (preview without ingesting)
- Show progress output (count, success/failure)
- Filter to videos with transcript_status=COMPLETED
- Handle errors gracefully (continue on failure)
- Report summary at end

## Checklist
- [ ] Command registered correctly
- [ ] --video-id option works
- [ ] --source option works
- [ ] --all option works
- [ ] --reingest option works
- [ ] --dry-run option works
- [ ] Progress output displayed
- [ ] Only COMPLETED transcripts processed
- [ ] Error handling works
- [ ] Summary report shown
- [ ] Command tests pass
- [ ] Type hints complete
- [ ] Docstrings written
