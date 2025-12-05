---
description: Bootstrap the ContentSync development environment
---

# Setup Workspace Agent

This workflow will set up your development environment from scratch.

1. **Initialize Python Environment**
   - Checks if `uv` is installed.
   - Initializes the project and installs dependencies.
   ```bash
   uv venv
   uv pip install django celery redis flower django-environ djangorestframework google-api-python-client litellm supabase
   ```

2. **Configure Environment Variables**
   - Creates a `.env` file if it doesn't exist.
   ```bash
   if [ ! -f .env ]; then
       echo "DEBUG=True" >> .env
       echo "SECRET_KEY=insecure-dev-key" >> .env
       echo "DATABASE_URL=postgres://postgres:postgres@localhost:5432/contentsync" >> .env
       echo "CELERY_BROKER_URL=redis://localhost:6379/0" >> .env
       echo "Creating .env file..."
   fi
   ```

3. **Start Infrastructure**
   - Starts Redis and Postgres (via Supabase or local Docker) using Docker Compose.
   // turbo
   ```bash
   docker-compose up -d
   ```

4. **Apply Database Migrations**
   ```bash
   uv run python manage.py migrate
   ```

5. **Create Superuser**
   - Prompts to create a superuser if needed.
   ```bash
   echo "To create a superuser, run: uv run python manage.py createsuperuser"
   ```
