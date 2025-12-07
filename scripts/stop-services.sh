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

# Stop Django Q workers (if running)
pkill -f "python.*qcluster" 2>/dev/null && echo "✓ Django Q workers stopped" || true

# Stop Supabase
echo "Stopping Supabase..."
npx supabase stop
echo "✓ Supabase stopped"

echo ""
echo "✅ All services stopped"
