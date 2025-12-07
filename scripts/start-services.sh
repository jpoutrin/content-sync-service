#!/bin/bash

# ContentSync Startup Script
# This script starts all required services

set -e

echo "🚀 Starting ContentSync Services"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :"$1" >/dev/null 2>&1
}

# 1. Start Supabase Database
echo "🗄️  Starting Supabase Database..."
if port_in_use 54322; then
    echo -e "${GREEN}✓${NC} Database is already running on port 54322"
else
    npx supabase db start
    echo -e "${GREEN}✓${NC} Database started on port 54322"
fi
echo ""

# 2. Get available port for Django
echo "🔍 Finding available port for Django..."
if command_exists portman; then
    DJANGO_PORT=$(portman get content-sync-service | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Reserved port: $DJANGO_PORT"
else
    DJANGO_PORT=10039
    echo -e "${YELLOW}⚠${NC}  portman not found, using default port: $DJANGO_PORT"
fi
echo ""

# 3. Check if Django is already running
if port_in_use $DJANGO_PORT; then
    echo -e "${YELLOW}⚠${NC}  Django server is already running on port $DJANGO_PORT"
    echo ""
else
    # 4. Run migrations
    echo "🔄 Running database migrations..."
    .venv/bin/python manage.py migrate --noinput
    echo -e "${GREEN}✓${NC} Migrations complete"
    echo ""

    # 5. Create superuser if needed
    echo "👤 Checking for superuser..."
    if .venv/bin/python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0 if User.objects.filter(username='admin').exists() else 1)" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Superuser 'admin' already exists"
    else
        echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | .venv/bin/python manage.py shell
        echo -e "${GREEN}✓${NC} Created superuser 'admin' with password 'admin123'"
    fi
    echo ""
fi

# 6. Display status
echo "=================================="
echo "✅ All Services Running!"
echo "=================================="
echo ""
echo "📍 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎨 Django Admin:"
echo "   → http://localhost:$DJANGO_PORT/admin/"
echo "   Login: admin / admin123"
echo ""

echo "📡 API Endpoints:"
echo "   → http://localhost:$DJANGO_PORT/api/sources/"
echo "   → http://localhost:$DJANGO_PORT/api/videos/"
echo ""
echo "🗄️  PostgreSQL Database:"
echo "   → postgresql://postgres:postgres@localhost:54322/postgres"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start Django server (if not running):"
echo "   .venv/bin/python manage.py runserver $DJANGO_PORT"
echo ""


echo "2. Start Django Q Cluster (for background tasks & daily sync):"
echo "   .venv/bin/python manage.py qcluster"
echo ""
echo "3. Access Django Admin:"
echo "   open http://localhost:$DJANGO_PORT/admin/"
echo ""
echo "💡 Tip: Run './scripts/stop-services.sh' to stop all services"
echo ""
