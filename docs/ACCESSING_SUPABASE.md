# Accessing Supabase UI

## Quick Access

Once Supabase is running, you can access the Studio UI at:

**🌐 Supabase Studio**: http://localhost:54323

This provides a web interface for:
- 📊 **Table Editor**: View and edit your database tables
- 🔍 **SQL Editor**: Run custom SQL queries
- 📈 **Database**: View schema, relationships, and indexes
- 🔐 **Authentication**: Manage users (when using Supabase Auth)
- 📁 **Storage**: File management (if enabled)
- ⚡ **API Docs**: Auto-generated API documentation

## Starting Supabase

```bash
# Start all Supabase services
npx supabase start

# Check status and get URLs
npx supabase status

# Stop services
npx supabase stop
```

## Key URLs from `npx supabase status`

When running, you'll see:

```
╭──────────────────────────────────╮
│ 🔧 Development Tools             │
├─────────┬────────────────────────┤
│ Studio  │ http://127.0.0.1:54323 │  ← Web UI
│ Mailpit │ http://127.0.0.1:54324 │  ← Email testing
╰─────────┴────────────────────────╯

╭───────────────────────────────────────────────────────────────╮
│ ⛁ Database                                                    │
├─────┬─────────────────────────────────────────────────────────┤
│ URL │ postgresql://postgres:postgres@127.0.0.1:54322/postgres │
╰─────┴─────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────╮
│ 🔑 Authentication Keys                                       │
├─────────────┬────────────────────────────────────────────────┤
│ Publishable │ sb_publishable_...                             │
│ Secret      │ sb_secret_...                                  │
╰─────────────┴────────────────────────────────────────────────╯
```

## Using Studio UI

### 1. **Table Editor**
- Navigate to "Table Editor" in the left sidebar
- You'll see your tables: `core_source`, `core_video`, `core_processedcontent`
- Click any table to view/edit data
- Use filters and search to find specific records

### 2. **SQL Editor**
- Click "SQL Editor" in the left sidebar
- Write and execute custom queries
- Example queries:

```sql
-- View all sources
SELECT * FROM core_source;

-- View videos with their processed content
SELECT 
    v.title,
    v.transcript_status,
    v.ai_analysis_status,
    pc.summary
FROM core_video v
LEFT JOIN core_processedcontent pc ON pc.video_id = v.id
LIMIT 10;

-- Count videos by status
SELECT 
    transcript_status,
    ai_analysis_status,
    COUNT(*) as count
FROM core_video
GROUP BY transcript_status, ai_analysis_status;
```

### 3. **Database Schema**
- Click "Database" → "Tables" to see schema
- View columns, types, constraints
- See relationships between tables

## Alternative: Direct Database Access

You can also connect directly using any PostgreSQL client:

```bash
# Using psql
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres

# Using DBeaver, pgAdmin, or any PostgreSQL client
Host: localhost
Port: 54322
Database: postgres
User: postgres
Password: postgres
```

## Django Admin Interface

For managing data through Django:

1. **Create a superuser** (if not done):
```bash
.venv/bin/python manage.py createsuperuser
```

2. **Access Django Admin**:
```
http://localhost:8000/admin/
```

This provides:
- Source management
- Video management
- ProcessedContent viewing
- User management
- Django's built-in admin features

## Troubleshooting

### Studio not loading?
```bash
# Restart Supabase
npx supabase stop
npx supabase start

# Check if port 54323 is in use
lsof -i :54323
```

### Database connection issues?
```bash
# Check if database is running
docker ps | grep supabase_db

# Check logs
docker logs supabase_db_content-sync-service
```

### Reset everything?
```bash
# Stop and remove all data
npx supabase stop --no-backup

# Start fresh
npx supabase start
.venv/bin/python manage.py migrate
```

## Pro Tips

1. **Bookmark Studio URL**: http://localhost:54323
2. **Use SQL Editor** for complex queries and data exploration
3. **Table Editor** is great for quick data viewing/editing
4. **Django Admin** is better for application-level data management
5. **Keep `npx supabase status` output** handy for credentials

## Current Project Tables

- **core_source**: YouTube channels/playlists being monitored
- **core_video**: Individual videos discovered
- **core_processedcontent**: AI-generated analysis results
- **django_***: Django system tables
- **celery_***: Celery task results

Happy exploring! 🚀
