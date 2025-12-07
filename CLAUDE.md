# Project: Content Sync Service

## Overview
Django-based content synchronization service.

## Tech Stack
- **Framework**: Django
- **Database**: PostgreSQL (via Supabase)
- **Task Queue**: Django-Q (ORM backend)
- **Python Version**: 3.12

## Project Structure
```
content-sync-service/
├── config/              # Django project settings
│   ├── settings.py
│   └── urls.py
├── rag/                 # RAG module (new)
├── yt_sync/             # YouTube sync module (new)
├── manage.py
└── .claude/
    ├── tasks/           # Parallel task specifications
    ├── contracts/       # Shared type contracts
    ├── architecture.md  # System architecture
    └── readiness-report.md
```

## Development Commands
```bash
# Start development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Run tests
python manage.py test

# Start services (custom script)
./scripts/start-services.sh
```

## Coding Standards
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and small

## Parallel Development

This project uses parallel multi-agent development. Artifacts are in `parallel/`.

- Each Tech Spec decomposition creates `parallel/TS-XXXX-{slug}/`
- Task files use compact YAML format for token efficiency
- Contracts are shared via `contracts/` subdirectory
- Legacy artifacts remain in `.claude/` for reference

### Commands
- `/parallel-decompose <prd> --tech-spec <ts-file>` - Decompose PRD into tasks
- `/parallel-integrate --parallel-dir <dir>` - Verify integration
- `/parallel-ready-django` - Assess parallelization readiness

### References
- See `.claude/architecture.md` for system design
- See `.claude/contracts/` for shared interfaces
