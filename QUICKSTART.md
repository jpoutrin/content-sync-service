# 🚀 ContentSync - Quick Start Guide

## ✅ Current Status

Your ContentSync application is now **running**!

**Services Status:**
- ✅ Django Server (Port 10039)
- ✅ PostgreSQL Database (Port 54322)
- ✅ Redis (Port 6380)
- ✅ Flower (Celery Monitor - Port 10040)

### 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Django Admin** | http://localhost:10039/admin/ | Username: `admin`<br>Password: `admin123` |
| **Flower (Celery)** | http://localhost:10040/ | No auth required |
| **API Endpoints** | http://localhost:10039/api/ | Requires Supabase JWT |
| **Supabase Studio** | http://localhost:54323 | (Web UI for database) |
| **PostgreSQL** | `postgresql://postgres:postgres@localhost:54322/postgres` | Direct DB access |

### 📡 API Endpoints

- **Sources**: http://localhost:10039/api/sources/
- **Videos**: http://localhost:10039/api/videos/

## 🔧 Environment Setup

### Option 1: Using direnv (Recommended)

If you have `direnv` installed:
```bash
direnv allow
```

This will automatically load all environment variables from `.envrc`.

### Option 2: Manual Setup

Source the environment file:
```bash
source .envrc
```

Or use the `.env` file (already configured).

## 🎯 Quick Actions

### 1. Access Django Admin
```bash
open http://localhost:10039/admin/
# Login: admin / admin123
```

### 2. Add a YouTube Source
```bash
# Playlist
.venv/bin/python manage.py add_source "https://www.youtube.com/playlist?list=PLxxx" "admin"

# Channel (with @ handle)
.venv/bin/python manage.py add_source "https://www.youtube.com/@channelname" "admin"

# Channel (with ID)
.venv/bin/python manage.py add_source "https://www.youtube.com/channel/UCxxx" "admin"
```

### 3. Test the Pipeline
```bash
.venv/bin/python manage.py test_pipeline dQw4w9WgXcQ --skip-llm
```

### 4. Start Celery Worker (for background tasks)
```bash
celery -A config worker -l info
```

## 📊 View Your Data

### Django Admin (Easiest)
1. Go to http://localhost:10039/admin/
2. Login with `admin` / `admin123`
3. Browse:
   - Sources
   - Videos
   - Processed content

### Supabase Studio (Advanced)
1. Start Supabase: `npx supabase start`
2. Open http://localhost:54323
3. Use the Table Editor or SQL Editor

## 🔑 API Keys Needed

To use the full pipeline, add these to `.env` or `.envrc`:

```bash
# YouTube Data API v3
export YOUTUBE_API_KEY=your_actual_key_here

# Anthropic (for Claude AI)
export ANTHROPIC_API_KEY=your_actual_key_here
```

Get your keys from:
- YouTube: https://console.cloud.google.com/apis/credentials
- Anthropic: https://console.anthropic.com/

## 🧪 Test the System

Run the test suite:
```bash
.venv/bin/python test_system.py
```

## 🛠️ Helper Scripts

We've created convenient scripts to manage services:

```bash
# Start all services (Redis, Supabase, Django setup)
./scripts/start-services.sh

# Stop all services
./scripts/stop-services.sh

# Access Supabase Studio
./scripts/access-supabase.sh
```

## 📝 Common Commands

```bash
# Start Django server on port 10039
.venv/bin/python manage.py runserver 10039

# Run migrations
.venv/bin/python manage.py migrate

# Create another superuser
.venv/bin/python manage.py createsuperuser

# Start Celery worker
celery -A config worker -l info

# Check Supabase status
npx supabase status

# Start Supabase
npx supabase start

# Stop Supabase
npx supabase stop
```

## 🎉 You're All Set!

Your ContentSync MVP is fully operational. Start by:
1. ✅ Accessing Django Admin at http://localhost:10039/admin/
2. ✅ Adding your API keys to `.envrc`
3. ✅ Creating your first YouTube source
4. ✅ Watching the magic happen!

---

**Need help?** Check the documentation:
- `README.md` - Full setup guide
- `IMPLEMENTATION_SUMMARY.md` - Technical overview
- `docs/ACCESSING_SUPABASE.md` - Database UI guide
