---
id: task-007-cli-search
component: RAGSearchCommand
wave: 3
deps: [task-005]
blocks: []
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-007-cli-search: RAG Search CLI Command

## Scope
CREATE:
- rag/management/__init__.py
- rag/management/commands/__init__.py
- rag/management/commands/rag_search.py
- rag/management/commands/tests/__init__.py
- rag/management/commands/tests/test_rag_search.py

BOUNDARY:
- rag/api/* (do not modify)
- rag/services/* (do not modify)

## Requirements
- Implement python manage.py rag_search <query>
- Required argument: query text
- Option: --top-k (default 10)
- Option: --min-score (default 0.7)
- Option: --user <user_id> (for ACL context)
- Option: --bypass-acl (admin/testing)
- Format output: score, document_id, text preview, timestamp_url
- Handle no results gracefully
- Validate inputs

## Checklist
- [ ] Command registered correctly
- [ ] Query argument required
- [ ] --top-k option works
- [ ] --min-score option works
- [ ] --user option works
- [ ] --bypass-acl option works
- [ ] Output formatted clearly
- [ ] No results handled
- [ ] Input validation works
- [ ] Command tests pass
- [ ] Type hints complete
- [ ] Docstrings written
