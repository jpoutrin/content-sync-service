---
id: task-002-embedder
component: LiteLLMEmbedder
wave: 1
deps: []
blocks: [task-004, task-005]
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev, python-experts:django-api, python-experts:documentation-research]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-002-embedder: LiteLLM Embedder Implementation

## Scope
CREATE:
- rag/embedders/__init__.py
- rag/embedders/litellm.py
- rag/embedders/tests/__init__.py
- rag/embedders/tests/test_litellm.py

BOUNDARY:
- rag/core/* (do not modify)
- rag/stores/* (do not modify)
- rag/chunkers/* (do not modify)

## Requirements
- Implement EmbedderInterface from rag/core/interfaces.py
- Support local provider (sentence-transformers, 384 dimensions)
- Support openai provider (litellm, 1536 dimensions)
- Implement embed() method for single text
- Implement embed_batch() method with configurable batch_size
- Expose dimensions property
- Handle API errors gracefully
- Support provider/model configuration via constructor

## Checklist
- [ ] LiteLLMEmbedder implements EmbedderInterface correctly
- [ ] Local provider (sentence-transformers) works
- [ ] OpenAI provider (litellm) works
- [ ] embed() method returns correct dimension vectors
- [ ] embed_batch() handles batching correctly
- [ ] dimensions property accurate for each provider
- [ ] Error handling implemented
- [ ] Unit tests pass with mocked API calls
- [ ] Type hints complete
- [ ] Docstrings written
