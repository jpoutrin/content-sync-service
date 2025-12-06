---
description: Start the ContentSync development stack
---

# Start App Agent

This workflow starts the entire application stack.

1. **Ensure Infrastructure is Running**
   // turbo
   ```bash
   docker-compose up -d
   ```

2. **Start Celery Worker**
   - Starts the background worker in a detached process or separate terminal.
   ```bash
   # You should run this in a separate terminal
   # uv run celery -A config worker -l info
   echo "Please start the Celery worker in a new terminal: uv run celery -A config worker -B -l info"
   ```

3. **Start Django Server**
   ```bash
   uv run python manage.py runserver
   ```
