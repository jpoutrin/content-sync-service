#!/bin/bash

# Quick Supabase Studio Access Script

echo "🚀 ContentSync - Supabase Studio Access"
echo "========================================"
echo ""

# Check if Supabase is running
if ! command -v npx &> /dev/null; then
    echo "❌ npx not found. Please install Node.js first."
    exit 1
fi

echo "📊 Checking Supabase status..."
echo ""

# Get status
npx supabase status 2>&1 | grep -E "(Studio|Database|API URL)" || {
    echo "⚠️  Supabase doesn't seem to be running."
    echo ""
    read -p "Would you like to start it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Starting Supabase..."
        npx supabase start
    else
        echo "ℹ️  Run 'npx supabase start' to start Supabase"
        exit 0
    fi
}

echo ""
echo "✅ Supabase is running!"
echo ""
echo "📍 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎨 Supabase Studio (Web UI):"
echo "   → http://localhost:54323"
echo ""
echo "🗄️  PostgreSQL Database:"
echo "   → postgresql://postgres:postgres@localhost:54322/postgres"
echo ""
echo "🔐 Django Admin:"
echo "   → http://localhost:8000/admin/"
echo ""
echo "📡 API Endpoints:"
echo "   → http://localhost:8000/api/sources/"
echo "   → http://localhost:8000/api/videos/"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tip: Open http://localhost:54323 in your browser to access Studio"
echo ""

# Offer to open in browser
if command -v open &> /dev/null; then
    read -p "Open Supabase Studio in browser? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:54323
        echo "✅ Opening Studio in your default browser..."
    fi
fi
