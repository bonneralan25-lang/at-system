#!/bin/bash
# Dashboard Setup Script
# Run this once to install all dependencies

set -e

echo "=== Operations Dashboard Setup ==="
echo ""

# Detect node
NODE_BIN=""
if [ -d "$HOME/.nvm/versions/node" ]; then
  LATEST=$(ls "$HOME/.nvm/versions/node" | sort -V | tail -1)
  NODE_BIN="$HOME/.nvm/versions/node/$LATEST/bin"
fi

if [ -z "$NODE_BIN" ]; then
  echo "ERROR: Node.js not found. Install via: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && nvm install --lts"
  exit 1
fi

echo "Using Node: $NODE_BIN/node ($(${NODE_BIN}/node --version))"
echo ""

# Install frontend deps
echo "--- Installing frontend dependencies ---"
cd "$(dirname "$0")/frontend"
if [ ! -f ".env.local" ]; then
  cp .env.local.example .env.local
  echo "Created .env.local — add your API keys"
fi
PATH="$NODE_BIN:$PATH" "$NODE_BIN/npm" install
echo "Frontend deps installed."
echo ""

# Setup backend
echo "--- Setting up Python backend ---"
cd "$(dirname "$0")/backend"
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env — add your API keys"
fi

# Create virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "Backend deps installed."
echo ""

echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "1. Fill in your API keys in:"
echo "   - backend/.env"
echo "   - frontend/.env.local"
echo ""
echo "2. Run the Supabase migration:"
echo "   - Go to https://app.supabase.com → your project → SQL Editor"
echo "   - Paste and run: supabase/migrations/001_initial_schema.sql"
echo ""
echo "3. Set up GHL webhook:"
echo "   - GHL → Automations → Webhooks → New → URL: http://localhost:8000/webhook/ghl"
echo "   - Trigger: Form Submitted (on your fence/pressure wash forms)"
echo ""
echo "4. Start the backend:"
echo "   cd backend && source .venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "5. Start the frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "Dashboard: http://localhost:3000"
echo "API docs:  http://localhost:8000/docs"
