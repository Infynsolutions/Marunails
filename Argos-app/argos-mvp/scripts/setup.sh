#!/bin/bash
# ══════════════════════════════════════════
# Argos MVP — Quick Setup Script
# ══════════════════════════════════════════
# Run from the project root: bash scripts/setup.sh

set -e

echo ""
echo "👁  ARGOS MVP — Setup"
echo "══════════════════════════════════════"
echo ""

# ── Check prerequisites ──
echo "🔍 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install Python 3.11+"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install Node.js 20+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
echo "  ✅ Python $PYTHON_VERSION"
echo "  ✅ Node.js v$NODE_VERSION"

# ── Backend setup ──
echo ""
echo "🐍 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✅ Virtual environment created"
fi

source venv/bin/activate
pip install -r requirements.txt -q
echo "  ✅ Dependencies installed"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "  ⚠️  Created backend/.env — YOU NEED TO FILL IN YOUR KEYS:"
    echo "     - ANTHROPIC_API_KEY"
    echo "     - SUPABASE_URL"
    echo "     - SUPABASE_SERVICE_KEY"
    echo "     - GOOGLE_SERVICE_ACCOUNT_JSON (path to your service account JSON)"
fi

cd ..

# ── Frontend setup ──
echo ""
echo "⚛️  Setting up frontend..."
cd frontend
npm install --silent
echo "  ✅ Dependencies installed"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✅ Created frontend/.env"
fi

cd ..

# ── Done ──
echo ""
echo "══════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Fill in your API keys in backend/.env"
echo ""
echo "2. Run the SQL schema in Supabase:"
echo "   → Open Supabase Dashboard → SQL Editor"
echo "   → Paste the contents of scripts/supabase_schema.sql"
echo "   → Click 'Run'"
echo ""
echo "3. Seed demo data:"
echo "   cd backend && source venv/bin/activate"
echo "   PYTHONPATH=. python ../scripts/seed_demo_data.py"
echo ""
echo "4. Start the backend:"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "5. Start the frontend (new terminal):"
echo "   cd frontend && npm run dev"
echo ""
echo "6. Open http://localhost:5173"
echo ""
echo "══════════════════════════════════════"
