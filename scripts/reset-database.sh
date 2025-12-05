#!/bin/bash

# Reset Database Script
# This will delete all migrations and recreate the database from scratch
# WARNING: This will delete all data!

echo "⚠️  WARNING: This will delete all database data!"
read -p "Are you sure you want to continue? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "🗑️  Removing old migrations..."
find ./core/migrations -name "*.py" -not -name "__init__.py" -delete
find ./core/migrations -name "*.pyc" -delete

echo "🔄 Stopping Supabase..."
npx supabase db reset --local

echo "📝 Creating new migrations..."
.venv/bin/python manage.py makemigrations

echo "🚀 Running migrations..."
.venv/bin/python manage.py migrate

echo "👤 Creating superuser..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | .venv/bin/python manage.py shell

echo "✅ Database reset complete!"
echo ""
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: admin123"
