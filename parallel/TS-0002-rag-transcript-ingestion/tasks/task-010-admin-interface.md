---
id: task-010
component: admin-interface
wave: 4
deps: [task-005]
agent: python-experts:django-expert
tech_spec: TS-0002
contracts: [rag/retrievers/default.py, rag/core/acl.py]
---
# task-010: Implement Admin Search Interface

## Scope
CREATE: none
MODIFY: rag/admin.py
BOUNDARY: rag/retrievers/*, rag/core/*, rag/services/*, yt_sync/*

## Requirements
- Add custom admin view for RAG search at /admin/rag/search/
- Create search form with query text input, top_k dropdown, min_score input
- Display results in table: chunk content, score, video title, timestamp link
- Use admin bypass ACL context for search (admin sees all content)
- Add link to search page in admin
- Style using Django admin CSS classes
- Handle empty results and errors gracefully

## Checklist
- [ ] Custom admin view function or class-based view
- [ ] URL registered at /admin/rag/search/
- [ ] Search form with query, top_k, min_score inputs
- [ ] Results table with columns: Content, Score, Video, Timestamp Link
- [ ] QueryACLContext.system_context() used for bypass
- [ ] Empty results show 'No results found' message
- [ ] Template extends admin/base_site.html
- [ ] Tests verify admin access required
- [ ] Uses DefaultRetriever contract from rag/retrievers/default.py
- [ ] Uses QueryACLContext from rag/core/acl.py
