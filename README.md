# ContentSync Service

A Django-based service for synchronizing and analyzing YouTube content using AI.

## Features

- **Source Management**: Subscribe to YouTube channels and playlists
- **Automatic Sync**: Periodically fetch new videos from monitored sources
- **Transcript Extraction**: Automatically extract transcripts from videos
- **AI Analysis**: Generate summaries, tags, categories, and key moments using Claude AI
- **REST API**: Secure API endpoints for managing sources and accessing processed content
- **Background Processing**: Celery-based task queue for long-running operations

## Tech Stack

- **Backend**: Django 5.0 + Django REST Framework
- **Database**: PostgreSQL (via Supabase)
- **Task Queue**: Celery + Redis
- **Authentication**: Supabase Auth (JWT)
- **AI**: Claude 3 Haiku (via LiteLLM)
- **External APIs**: YouTube Data API v3

## Setup

### Prerequisites

- Python 3.12+
- Docker (for Redis and Supabase)
- YouTube API Key
- Anthropic API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd content-sync-service
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt  # Or use pip
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Start infrastructure**
   ```bash
   # Start Supabase (includes PostgreSQL)
   npx supabase start
   
   # Start Redis
   docker-compose up -d redis
   ```

6. **Run migrations**
   ```bash
   .venv/bin/python manage.py migrate
   ```

7. **Create superuser (optional)**
   ```bash
   .venv/bin/python manage.py createsuperuser
   ```

### Running the Application

You need to run three processes:

1. **Django API Server**
   ```bash
   .venv/bin/python manage.py runserver
   ```

2. **Celery Worker**
   ```bash
   celery -A config worker -l info
   ```

3. **Celery Beat (for periodic tasks - optional)**
   ```bash
   celery -A config beat -l info
   ```

## Usage

### Management Commands

**Add a new source:**
```bash
.venv/bin/python manage.py add_source <channel_id_or_username> <user_uuid>
```

**Manually sync a source:**
```bash
.venv/bin/python manage.py sync_source <source_uuid>
```

### API Endpoints

All endpoints require authentication via Supabase JWT in the `Authorization: Bearer <token>` header.

**Sources:**
- `POST /api/sources/` - Create a new source
- `GET /api/sources/` - List all sources
- `DELETE /api/sources/{id}/` - Remove a source

**Videos:**
- `GET /api/videos/` - List videos (supports filtering)
- `GET /api/videos/{id}/` - Get video details with AI analysis

**Query Parameters for Videos:**
- `source_id` - Filter by source
- `transcript_status` - Filter by transcript status
- `ai_analysis_status` - Filter by AI analysis status
- `search` - Search in video titles

## Architecture

```
User → Django API → PostgreSQL (Supabase)
         ↓
      Redis (Broker)
         ↓
    Celery Workers → YouTube API
                  → Transcript Extraction
                  → Claude AI (via LiteLLM)
                  → PostgreSQL
```

## Development

### Project Structure

```
content-sync-service/
├── config/              # Django settings and configuration
├── core/                # Main application
│   ├── models.py        # Database models
│   ├── views.py         # API views
│   ├── serializers.py   # DRF serializers
│   ├── tasks.py         # Celery tasks
│   ├── services/        # External service integrations
│   │   ├── youtube.py   # YouTube API client
│   │   ├── transcript.py # Transcript extraction
│   │   └── llm.py       # LLM integration
│   └── management/      # Django management commands
├── .agent/              # Agent workflows
└── technical-specs/     # Technical documentation
```

### Testing

```bash
.venv/bin/python manage.py test
```

## License

[Your License Here]
