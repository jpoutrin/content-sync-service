---
id: task-009
component: auto-ingest-signal
wave: 4
deps: [task-004]
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [yt_sync/models.py, rag/services/ingestion.py]
---
# task-009: Implement Auto-Ingestion Django Signal

## Scope
CREATE: yt_sync/signals.py, yt_sync/tests/test_signals.py
MODIFY: yt_sync/apps.py
BOUNDARY: yt_sync/models.py, rag/services/*, rag/core/*, rag/retrievers/*

## Requirements
- Create transcript_saved signal receiver for Video post_save
- Trigger only when transcript_status changes to 'COMPLETED'
- Check settings.RAG_AUTO_INGEST - skip if False
- Queue Django-Q async task for ingestion (async_ingest_video)
- Define async_ingest_video(video_id) task function
- Task retrieves Video by ID and calls IngestionService.ingest_video()
- Import signal in apps.py ready() method
- Log when task is queued and when ingestion completes
- Handle race conditions gracefully (video deleted before task runs)

## Checklist
- [ ] transcript_saved signal receiver defined with @receiver(post_save, sender=Video)
- [ ] Signal checks if transcript_status == 'COMPLETED'
- [ ] Signal checks settings.RAG_AUTO_INGEST before queueing
- [ ] Django-Q async_task called with video_id
- [ ] async_ingest_video(video_id) fetches Video and calls IngestionService
- [ ] Video.DoesNotExist handled gracefully
- [ ] YtSyncConfig.ready() imports yt_sync.signals
- [ ] Tests verify signal triggers on COMPLETED status
- [ ] Tests verify signal respects RAG_AUTO_INGEST=False
- [ ] Uses Video model from yt_sync/models.py
- [ ] Uses IngestionService contract from rag/services/ingestion.py
