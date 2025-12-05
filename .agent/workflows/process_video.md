---
description: Process a single video through the pipeline
---

# Process Video Agent

This workflow manually triggers the processing pipeline for a specific video.

1. **Get Video ID**
   - Find the video ID you want to process (from admin or API).

2. **Trigger Processing**
   ```bash
   .venv/bin/python manage.py shell -c "from core.tasks import process_video_pipeline_task; process_video_pipeline_task.delay('VIDEO_UUID_HERE')"
   ```

3. **Monitor Celery Logs**
   - Watch the Celery worker logs to see the processing progress.
   - You should see: transcript extraction → AI summary generation → results saved.
