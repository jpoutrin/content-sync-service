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

## Claude Skills

### Supabase Management
Use the `/supabase` skill for all Supabase operations:

```bash
# Local development
/supabase start              # Start local Supabase stack
/supabase stop               # Stop local stack
/supabase status             # Check running services

# Database operations
/supabase db reset           # Reset local database
/supabase db pull            # Pull schema from remote
/supabase db push            # Push migrations to remote

# Migrations
/supabase migration new <name>    # Create new migration
/supabase migration up            # Apply pending migrations

# Type generation
/supabase gen types          # Generate TypeScript types

# Edge Functions
/supabase functions new      # Create new function
/supabase functions serve    # Serve functions locally
/supabase functions deploy   # Deploy to remote
```

See `~/.claude/skills/supabase/skill.md` for complete command reference.

## Coding Standards
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and small

## Code Quality Checks

Use the Makefile for systematic code quality checks:

```bash
# Type checking
make typecheck          # Run mypy on all modules
make typecheck-rag      # Run mypy on rag module only
make typecheck-yt-sync  # Run mypy on yt_sync module only

# Testing
make test               # Run all tests
make test-rag           # Run RAG tests only
make test-yt-sync       # Run yt_sync tests only

# Linting and formatting
make lint               # Run ruff linting
make format             # Format code with ruff

# Run all checks
make check              # Run typecheck + lint + test

# Clean cache files
make clean              # Remove __pycache__, .mypy_cache, etc.
```

**Type Checking Notes:**
- Mypy is configured in `pyproject.toml` with Django plugins
- Run type checks before committing code
- Use `# type: ignore[error-code]` for intentional violations (e.g., testing invalid inputs)

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
