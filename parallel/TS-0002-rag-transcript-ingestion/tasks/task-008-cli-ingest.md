---
id: task-008
component: cli-ingest
wave: 3
deps: [task-004]
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [rag/services/ingestion.py, yt_sync/models.py]
---
# task-008: Implement rag_ingest Management Command

## Scope
CREATE: rag/management/commands/rag_ingest.py, rag/management/commands/tests/test_rag_ingest.py
MODIFY: none
BOUNDARY: rag/services/*, rag/core/*, yt_sync/models.py, rag/retrievers/*

## Requirements
- Create Django management command: `python manage.py rag_ingest`
- Accept `--video-id` option to ingest single video by primary key
- Accept `--all` flag to ingest all videos with COMPLETED transcript_status
- Accept `--source` option to ingest all videos from specific source ID
- Accept `--reingest` flag to force re-indexing
- Accept `--dry-run` flag to show what would be ingested
- Output progress: 'Ingesting video: {title}...'
- Output summary: 'Ingested N videos, M total chunks'
- Handle errors per-video (log and continue)
- Require at least one of: --video-id, --all, --source

## Checklist
- [ ] add_arguments defines --video-id, --all, --source, --reingest, --dry-run
- [ ] Validation requires at least one of video-id/all/source
- [ ] --video-id fetches single Video by pk
- [ ] --all fetches Video.objects.filter(transcript_status='COMPLETED')
- [ ] --dry-run lists videos without calling ingest_video()
- [ ] Progress output shows video title
- [ ] Summary output shows total videos and chunks
- [ ] Per-video errors logged but don't stop other videos
- [ ] Tests cover: single video, --all, --source, --dry-run
- [ ] Uses IngestionService contract from rag/services/ingestion.py
- [ ] Uses Video and Source models from yt_sync/models.py
