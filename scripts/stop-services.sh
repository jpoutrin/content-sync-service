#!/bin/bash

# ContentSync Stop Services Script

echo "🛑 Stopping ContentSync Services"
echo "=================================="
echo ""

# Stop Django (if running)
if lsof -i :10039 >/dev/null 2>&1; then
    echo "Stopping Django server..."
    lsof -ti :10039 | xargs kill -9 2>/dev/null || true
    echo "✓ Django stopped"
fi

# Stop Celery workers (if running)
pkill -f "celery.*worker" 2>/dev/null && echo "✓ Celery workers stopped" || true

# Stop Redis
echo "Stopping Redis..."
docker-compose stop redis
echo "✓ Redis stopped"

# Stop Supabase
echo "Stopping Supabase..."
npx supabase stop
echo "✓ Supabase stopped"

echo ""
echo "✅ All services stopped"
