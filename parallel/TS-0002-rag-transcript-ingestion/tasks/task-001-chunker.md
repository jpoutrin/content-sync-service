---
id: task-001
component: chunker
wave: 1
deps: []
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [rag/core/interfaces.py, rag/core/schemas.py]
---
# task-001: Implement TranscriptChunker

## Scope
CREATE: rag/chunkers/__init__.py, rag/chunkers/transcript.py, rag/chunkers/tests/__init__.py, rag/chunkers/tests/test_transcript.py
MODIFY: none
BOUNDARY: rag/core/interfaces.py, rag/core/schemas.py, rag/embedders/*, rag/services/*, rag/stores/*

## Requirements
- Implement `TranscriptChunker` class implementing `ChunkerInterface` from `rag.core.interfaces`
- Parse `transcript_data` from `Document.metadata` (list of `{'text': str, 'start': float, 'duration': float}`)
- Split transcripts by timestamp gaps (gap_threshold default 2.0s from `settings.RAG_CHUNK_GAP_THRESHOLD`)
- Respect `max_chars` (default 1000) - split long segments
- Merge short segments until `min_chars` (default 100)
- Use `Chunk.from_document()` to inherit ACL fields
- Include timestamp metadata: `start_time`, `end_time`, `segment_count`, `video_title`, `video_url`, `youtube_video_id`
- Use chunk ID format: `video:{document.source_id}:chunk:{index}`
- Handle empty `transcript_data` gracefully (return empty list)

## Checklist
- [ ] `TranscriptChunker` implements `ChunkerInterface.chunk(document) -> list[Chunk]`
- [ ] Constructor accepts `gap_threshold`, `max_chars`, `min_chars` with defaults from Django settings
- [ ] Chunks split when gap between segments > `gap_threshold`
- [ ] Chunks split when accumulated text > `max_chars`
- [ ] Short segments merged until reaching `min_chars`
- [ ] Chunks created using `Chunk.from_document()` to copy ACL fields
- [ ] `Chunk.metadata` contains: `start_time`, `end_time`, `segment_count`, `video_title`, `video_url`, `youtube_video_id`
- [ ] Empty `transcript_data` returns empty list (no error)
- [ ] Tests cover: gap splitting, max_chars splitting, min_chars merging, ACL inheritance
- [ ] Test coverage >= 90%
