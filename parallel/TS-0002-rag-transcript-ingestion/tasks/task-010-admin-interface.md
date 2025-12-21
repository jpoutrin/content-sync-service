---
id: task-010-admin-interface
component: RAGAdmin
wave: 4
deps: [task-004, task-005]
blocks: []
agent: python-experts:django-expert
skills: [python-experts:python-style, python-experts:django-dev]
tech_spec: TS-0002
contracts: [contracts/types.py, contracts/api-schema.yaml]
---
# task-010-admin-interface: Django Admin RAG Interface

## Scope
MODIFY:
- rag/admin.py

BOUNDARY:
- rag/api/* (do not modify)
- rag/core/* (do not modify)

## Requirements
- Add admin action "Ingest to RAG" for Document model
- Add admin action "Search RAG" with query input
- Restrict to staff users only
- Use bypass_acl=True for admin search
- Show ingestion results (success/failure count)
- Display search results in admin messages
- Include timestamp_url in search results
- Handle bulk ingestion (multiple documents)
- Provide clear feedback messages

## Checklist
- [ ] "Ingest to RAG" admin action works
- [ ] "Search RAG" admin action works
- [ ] Staff-only restriction enforced
- [ ] bypass_acl enabled for admin search
- [ ] Ingestion results displayed
- [ ] Search results formatted clearly
- [ ] timestamp_url included
- [ ] Bulk operations work
- [ ] Feedback messages clear
- [ ] Type hints complete
- [ ] Docstrings written
