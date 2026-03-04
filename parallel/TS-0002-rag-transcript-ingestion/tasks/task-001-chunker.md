---
id: task-001-chunker
component: TranscriptChunker
wave: 1
deps: []
blocks: [task-004]
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev, python-experts:django-api, python-experts:documentation-research]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-001-chunker: Transcript Chunker Implementation

## Scope
CREATE:
- rag/chunkers/__init__.py
- rag/chunkers/transcript.py
- rag/chunkers/tests/__init__.py
- rag/chunkers/tests/test_transcript.py

BOUNDARY:
- rag/core/* (do not modify)
- rag/stores/* (do not modify)
- rag/embedders/* (do not modify)

## Requirements
- Implement ChunkerInterface from rag/core/interfaces.py
- Chunk transcripts by timestamp gaps (2.0s default threshold)
- Enforce max_chars (1000) and min_chars (100) constraints
- Use Chunk.from_document() for ACL inheritance from Document
- Include timestamp metadata in each chunk
- Support configurable gap threshold, max_chars, and min_chars
- Handle edge cases (empty transcripts, single-word chunks, etc.)

## Checklist
- [ ] TranscriptChunker implements ChunkerInterface correctly
- [ ] Chunking respects timestamp gaps (configurable threshold)
- [ ] max_chars and min_chars constraints enforced
- [ ] ACL inheritance works via Chunk.from_document()
- [ ] Timestamp metadata included in chunk metadata
- [ ] Unit tests pass for all scenarios
- [ ] Edge cases handled (empty input, boundary conditions)
- [ ] Type hints complete
- [ ] Docstrings written
