---
id: task-007
component: cli-search
wave: 3
deps: [task-005]
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [rag/retrievers/default.py, rag/core/schemas.py, rag/core/acl.py]
---
# task-007: Implement rag_search Management Command

## Scope
CREATE: rag/management/__init__.py, rag/management/commands/__init__.py, rag/management/commands/rag_search.py, rag/management/commands/tests/__init__.py, rag/management/commands/tests/test_rag_search.py
MODIFY: none
BOUNDARY: rag/retrievers/*, rag/core/*, rag/services/*, yt_sync/*

## Requirements
- Create Django management command: `python manage.py rag_search`
- Accept positional argument: query text
- Accept `--top-k` option (default 5)
- Accept `--min-score` option (default 0.0)
- Accept `--user` option to search as specific user ID
- If `--user` not specified, use system context (bypass ACL)
- Output results in formatted table: content (truncated), score, timestamp_url
- Show 'No results found' message for empty results

## Checklist
- [ ] Command class extends BaseCommand
- [ ] add_arguments defines query (positional), --top-k, --min-score, --user
- [ ] System context used when --user not provided
- [ ] Results formatted as table with columns
- [ ] Content truncated to 80 chars with ellipsis
- [ ] 'No results found' message for empty results
- [ ] Tests cover: basic search, --user option, no results
- [ ] Uses DefaultRetriever contract from rag/retrievers/default.py
- [ ] Uses SearchQuery schema from rag/core/schemas.py
- [ ] Uses QueryACLContext from rag/core/acl.py
