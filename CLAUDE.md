# Project: Content Sync Service

## Overview
Django-based content synchronization service.

## Tech Stack
- **Framework**: Django
- **Database**: PostgreSQL (via Supabase)
- **Task Queue**: Celery / Django-Q
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
This project is set up for parallel multi-agent development.
- See `.claude/architecture.md` for system design
- See `.claude/contracts/` for shared interfaces
- Run `/parallel-ready-django` to assess parallelization readiness
