# ATSystem — Developer Setup Guide

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Git**

---

## 1. Clone the Repo

```bash
git clone https://github.com/bonneralan25-lang/at-system.git
cd at-system
```

---

## 2. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
```

Open `backend/.env` and fill in the real values (ask Alan for the keys):

- `GHL_API_KEY` — GoHighLevel Private Integration Token
- `GHL_LOCATION_ID` — GHL Location ID
- `DATABASE_URL` — your local Postgres connection string (default works if using `atsystem` db name)

---

## 3. Database Setup

Install PostgreSQL if you don't have it:

```bash
# macOS
brew install postgresql@17
brew services start postgresql@17

# Ubuntu/Debian
sudo apt install postgresql
sudo systemctl start postgresql
```

Create the database and run migrations:

```bash
createdb atsystem
psql atsystem < supabase/migrations/001_initial_schema.sql
psql atsystem < supabase/migrations/002_ghl_enrichment.sql
```

---

## 4. Frontend Setup

```bash
cd frontend
npm install
```

### Configure Environment

```bash
cp .env.example .env.local
```

Open `frontend/.env.local` and fill in:

- `NEXT_PUBLIC_API_URL` — backend URL (default `http://localhost:8000` works for local dev)
- `NEXT_PUBLIC_GOOGLE_MAPS_KEY` — Google Maps API key (ask Alan)

---

## 5. Start the Servers

### Backend (runs on port 8000)

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

### Frontend (runs on port 3000)

```bash
cd frontend
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## 6. Import GHL Data (First Time)

Once both servers are running:

1. Go to **Settings** in the dashboard
2. Click **Discover GHL Fields** — maps GHL custom field IDs to our field names
3. Click **Sync from GHL** — imports existing contacts as leads

---

## Project Structure

```
at-system/
├── backend/
│   ├── api/            # FastAPI route handlers
│   ├── models/         # Pydantic models
│   ├── services/       # GHL client, estimator, poller
│   ├── db.py           # PostgreSQL abstraction layer
│   ├── config.py       # Settings from .env
│   ├── main.py         # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── app/            # Next.js pages (App Router)
│   ├── components/     # Shared UI components (shadcn)
│   └── lib/            # API client, utilities
├── supabase/
│   └── migrations/     # SQL migration files
├── CLAUDE.md           # AI assistant project context
└── instructions.md     # This file
```

---

## Questions?

Reach out to Alan for API keys, access, or architecture questions.
