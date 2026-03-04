# TS-0003: Separate LLM Processing from Transcript Fetching

## Overview

Currently, the video processing pipeline couples transcript fetching with LLM analysis in a single `process_video_pipeline_task`. This prevents efficient reprocessing of LLM analysis without re-fetching transcripts from YouTube.

This spec introduces a new task and management command to decouple LLM processing, enabling independent reprocessing of AI analysis while reusing cached transcripts.

## Problem Statement

**Current Flow:**
```
process_video_pipeline_task
├── extract_transcript_task (fetch from YouTube)
├── generate_summary_task (call LLM)
└── save_results_task (persist to DB)
```

**Issues:**
1. To reprocess LLM analysis, the entire pipeline re-runs, including YouTube API calls
2. YouTube API has rate limits and costs
3. Transcripts are already stored in `Video.transcript_text` but not reused
4. No way to quickly iterate on LLM prompts or model changes without re-fetching

## Solution

Introduce a new task `reprocess_llm_task` that:
- Reads `transcript_text` directly from the database
- Skips YouTube API calls entirely
- Resets `ai_analysis_status` to `PENDING`
- Runs `generate_summary_task` → `save_results_task`
- Provides a new management command `reprocess_llm` for easy invocation

## Architecture

### New Task: `reprocess_llm_task(video_id)`

**Location:** `yt_sync/tasks.py`

**Behavior:**
1. Fetch video from DB by `video_id`
2. If `transcript_text` is empty, log warning and return (no-op)
3. Reset `ai_analysis_status` to `PENDING`
4. Create transcript result dict from stored `transcript_text`
5. Call `generate_summary_task(transcript_result)`
6. If successful, call `save_results_task(summary_result, video_id)`
7. Log completion or failure

**Error Handling:**
- Video not found → log error, return
- No transcript → log warning, return
- LLM failure → status set to FAILED, error logged

### New Management Command: `reprocess_llm`

**Location:** `yt_sync/management/commands/reprocess_llm.py`

**Interface:**
```bash
python manage.py reprocess_llm --video-id <uuid>
python manage.py reprocess_llm --source-id <uuid>
python manage.py reprocess_llm --all
```

**Behavior:**
1. Accept mutually exclusive arguments: `--video-id`, `--source-id`, or `--all`
2. Query videos with non-null `transcript_text` (only reprocess if transcript exists)
3. For each video, dispatch `reprocess_llm_task` via `async_task`
4. Output task IDs and count to stdout
5. Handle edge cases (no videos found, invalid UUIDs)

**Filtering:**
- Always filter to videos where `transcript_text IS NOT NULL`
- This prevents attempting LLM processing on videos without transcripts

## Data Model

No model changes required. Existing fields used:
- `Video.transcript_text` — source for LLM input
- `Video.ai_analysis_status` — tracks LLM processing state
- `Video.processing_error` — stores error messages
- `ProcessedContent` — stores LLM output (summary, tags, categories, etc.)

## Testing Strategy

### Unit Tests: `yt_sync/tests/test_tasks.py`

**Test Class: `TestReprocessLlmTask`**

1. **`test_reprocess_llm_task_success`**
   - Setup: Video with `transcript_text` populated
   - Mock: `LLMService.generate_summary()` returns valid summary data
   - Assert: `ProcessedContent` created, `ai_analysis_status` = COMPLETED

2. **`test_reprocess_llm_task_no_transcript`**
   - Setup: Video with `transcript_text = None`
   - Assert: LLM NOT called, status unchanged, warning logged

3. **`test_reprocess_llm_task_video_not_found`**
   - Setup: Invalid video UUID
   - Assert: No crash, error logged

4. **`test_reprocess_llm_task_llm_failure`**
   - Setup: Video with transcript, LLM returns `None`
   - Assert: `ai_analysis_status` = FAILED, no `ProcessedContent` created

5. **`test_reprocess_llm_task_resets_status`**
   - Setup: Video with `ai_analysis_status` = COMPLETED
   - Assert: Status reset to PENDING before LLM call

6. **`test_reprocess_llm_task_overwrites_existing_content`**
   - Setup: Video with existing `ProcessedContent`
   - Mock: LLM returns new summary data
   - Assert: `ProcessedContent` updated with new data

### Integration Tests: `yt_sync/tests/test_tasks.py`

**Test Class: `TestReprocessLlmCommand`**

1. **`test_command_dispatches_task_for_video_id`**
   - Setup: Create video with transcript
   - Execute: `reprocess_llm --video-id <uuid>`
   - Assert: Exactly 1 async task dispatched

2. **`test_command_skips_videos_without_transcript`**
   - Setup: Create 2 videos (1 with transcript, 1 without)
   - Execute: `reprocess_llm --all`
   - Assert: Only 1 task dispatched (the one with transcript)

3. **`test_command_all_flag`**
   - Setup: Create 3 videos with transcripts
   - Execute: `reprocess_llm --all`
   - Assert: 3 tasks dispatched

4. **`test_command_source_id_flag`**
   - Setup: Create 2 sources, 2 videos each (all with transcripts)
   - Execute: `reprocess_llm --source-id <source1_uuid>`
   - Assert: 2 tasks dispatched (only for source1)

5. **`test_command_no_videos_found`**
   - Setup: No videos with transcripts
   - Execute: `reprocess_llm --all`
   - Assert: Warning message, 0 tasks dispatched

6. **`test_command_invalid_video_id`**
   - Execute: `reprocess_llm --video-id invalid-uuid`
   - Assert: Warning message, 0 tasks dispatched

### Mocking Strategy

- Mock `LLMService.generate_summary()` to return controlled test data
- Mock `async_task()` to verify task dispatch without running queue
- Use `VideoFactory` and `SourceFactory` for test data

## Implementation Files

| File | Action |
|---|---|
| `yt_sync/tasks.py` | Add `reprocess_llm_task()` function |
| `yt_sync/management/commands/reprocess_llm.py` | New management command |
| `yt_sync/tests/test_tasks.py` | New test file with unit + integration tests |

## Backward Compatibility

- Existing `process_video_pipeline_task` unchanged
- Existing `reprocess_transcripts` command unchanged
- No database migrations required
- No API changes

## Performance Considerations

- **Transcript Fetching Eliminated:** Saves YouTube API calls and network latency
- **Async Dispatch:** Tasks queued via django-q, non-blocking
- **Database Queries:** Minimal (1 query per video to fetch transcript)
- **LLM Cost:** Same as before (1 LLM call per video)

## Future Enhancements

1. Add `--batch-size` flag to limit concurrent LLM calls
2. Add `--dry-run` flag to preview which videos would be reprocessed
3. Add `--force` flag to reprocess even videos without transcripts (re-fetch)
4. Add progress bar for large batch operations
5. Add webhook/signal to trigger reprocessing on LLM model updates

## Success Criteria

✅ `reprocess_llm_task` successfully processes videos using cached transcripts  
✅ `reprocess_llm` command dispatches tasks correctly  
✅ No YouTube API calls made during LLM reprocessing  
✅ All tests pass (unit + integration)  
✅ Error handling covers edge cases  
✅ Backward compatible with existing pipeline  
