# ATSystem — A&T's Fence Restoration Operations Dashboard

## Project Overview

Operations dashboard for A&T's Pressure Washing Fence Restoration Division. Automates lead capture from GoHighLevel (GHL), generates intelligent fence staining estimates, and provides a VA-operated dashboard for estimate review, categorization, and delivery to clients. Includes a customer-facing self-serve proposal/booking website.

**Business Goal:** Deliver estimates to clients faster. Minimize VA manual work by auto-categorizing leads, auto-calculating estimates, and guiding the VA through a streamlined approval flow. Let customers self-book via a branded proposal link.

> Previous CLAUDE.md (original spec) is preserved as `CLAUDE2.md`.

---

## Tech Stack

- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI (Python 3.9+), Pydantic v2, uvicorn
- **Database:** PostgreSQL via custom db.py query builder (`backend/db.py`) — NOT Supabase client
- **Integrations:** GoHighLevel API v2 (contacts, SMS, pipeline), Google Calendar API (service account), Resend (Email)
- **Package Manager:** npm (frontend), pip + venv (backend)

---

## Core Business Flow

```
1. Lead submits form in GHL → webhook or 5-min poller syncs to dashboard
2. Auto-categorized by color on Kanban board (GRAY/PURPLE/ORANGE/GREEN/YELLOW/RED/SKY BLUE)
3. VA opens Lead Detail page → fills Estimate Inputs → Save & Recalculate
4. VA reviews Estimate → Approve & Send All Packages (sends SMS with proposal link)
5. Customer opens proposal link → picks package → books date → Google Calendar event created
6. Alan notified via GHL SMS
```

---

## Project Structure

```
ATSystem/
├── backend/
│   ├── main.py                  # FastAPI entry, CORS, route registration
│   ├── config.py                # Pydantic Settings (env vars)
│   ├── db.py                    # Custom PostgreSQL query builder
│   ├── api/
│   │   ├── webhooks.py          # POST /webhook/ghl, POST /webhook/ghl/message
│   │   ├── leads.py             # GET/PUT leads endpoints
│   │   ├── estimates.py         # CRUD + approve/reject/adjust estimates
│   │   ├── proposals.py         # GET /api/proposal/{token}, POST /api/proposal/{token}/book
│   │   ├── settings.py          # Pricing config + stats
│   │   └── sync.py              # GHL bulk import + pipeline sync
│   ├── models/
│   │   ├── lead.py              # Lead, LeadDetail, ServiceType, LeadStatus
│   │   └── estimate.py          # Estimate, EstimateDetail, EstimateApprove
│   └── services/
│       ├── ghl.py               # GHL API client (contacts, SMS, webhook parsing)
│       ├── estimator.py         # Pricing engine — zone/tier/age/size logic
│       ├── google_calendar.py   # Google Calendar service account integration
│       ├── poller.py            # Background poller (runs every 5 min)
│       └── notify.py            # Email notifications to owner
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root layout (no sidebar — used by proposal page)
│   │   ├── proposal/
│   │   │   └── [token]/
│   │   │       └── page.tsx     # PUBLIC customer proposal + booking page
│   │   └── (dashboard)/
│   │       ├── layout.tsx       # Dashboard layout (sidebar)
│   │       ├── page.tsx         # Dashboard home — KPI cards + pending queue
│   │       ├── leads/
│   │       │   ├── page.tsx     # Kanban board (7 columns) + Queue tab
│   │       │   └── [id]/page.tsx # Lead detail + VA input form + estimate result
│   │       ├── estimates/
│   │       │   ├── page.tsx     # Estimate list with tier prices
│   │       │   └── [id]/page.tsx # Estimate detail — approve/reject/adjust
│   │       └── settings/        # Pricing config + GHL sync
│   ├── components/
│   │   ├── ui/                  # Shadcn primitives
│   │   └── dashboard/sidebar.tsx
│   └── lib/
│       ├── api.ts               # HTTP client + all TypeScript types (incl. ProposalData)
│       └── utils.ts             # Formatting helpers
├── supabase/
│   └── migrations/              # SQL migration files (run manually via psql)
│       ├── 001_initial_schema.sql
│       ├── 002_ghl_enrichment.sql
│       ├── 003_add_archived.sql
│       ├── 004_add_kanban_column.sql
│       ├── 005_add_messages_table.sql
│       └── 006_add_proposals_table.sql
├── TODO.md                      # Deferred features + future roadmap
├── CLAUDE.md                    # ← You are here
└── CLAUDE2.md                   # Original spec (preserved for reference)
```

---

## Estimate Tier Pricing (3 packages sent together)

Every fence staining estimate produces 3 prices:
- **Essential** — base tier
- **Signature** — recommended (middle)
- **Legacy** — premium

All 3 are displayed on the proposal page. Customer picks one when booking.
Monthly financing shown as `price / 21` (21-month plan).

---

## Kanban Column Colors

| Color     | Meaning |
|-----------|---------|
| GRAY      | No estimate activity yet |
| PURPLE    | No address/zip — VA must enter zip |
| ORANGE    | Needs more info (height, age) |
| GREEN     | Ready to send — all criteria met |
| YELLOW    | Ready but has add-on services |
| RED       | Owner review required |
| SKY BLUE  | Follow-up quote sent |

---

## Proposal Website Flow

```
Approve estimate → generate token → append link to SMS
Customer: /proposal/{token}
  Step 1: Choose package (Essential / Signature / Legacy)
  Step 2: Pick a date (Mon–Sat, next 4 weeks)
  Step 3: Confirm name + address
  Step 4: Done — Google Calendar event created, Alan notified via GHL SMS
```

---

## Key Architecture Decisions

1. **Zone-based pricing** — TX zip codes mapped to Base/Blue/Purple/Outside zones
2. **3-tier pricing** — Essential / Signature / Legacy — all sent together, customer picks
3. **VA measurement flow** — `PUT /api/leads/{id}/form-data` merges + recalculates synchronously
4. **Proposal tokens** — UUID-based, stored in `proposals` table, appended to approval SMS
5. **GHL is bidirectional** — receives webhooks IN, sends SMS + updates contact notes OUT
6. **GHL for owner notifications** — Alan notified via GHL SMS (uses `OWNER_GHL_CONTACT_ID`), not Twilio
7. **Google Calendar** — Service account credentials stored as JSON env var; events created on booking
8. **DB-first messages** — Webhook stores messages in DB; API reads DB first, falls back to GHL API on first load
9. **No auth currently** — Dashboard assumed behind proxy auth or internal-only access
10. **Public proposal page** — Lives at `app/proposal/[token]/page.tsx` (outside dashboard route group = no sidebar)

---

## Environment Variables

### Backend (`backend/.env`)
```
DATABASE_URL=postgresql://...
GHL_API_KEY=...
GHL_LOCATION_ID=...
OWNER_GHL_CONTACT_ID=...          # Alan's GHL contact ID for booking notifications
RESEND_API_KEY=...
OWNER_EMAIL=...
FRONTEND_URL=http://localhost:3000
PROPOSAL_BASE_URL=http://localhost:3000   # → https://proposal.atpressurewash.com in prod
GOOGLE_CALENDAR_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_CALENDAR_ID=primary
GOOGLE_MAPS_API_KEY=...
```

### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_MAPS_KEY=...
```

---

## Running Locally

```bash
# Backend (port 8000)
cd backend && source .venv/bin/activate && uvicorn main:app --reload

# Frontend (port 3000)
cd frontend && npm run dev
```

---

## GHL Integration Details

- **API Base:** `https://services.leadconnectorhq.com`
- **Webhook endpoint:** `POST /webhook/ghl` + `POST /webhook/ghl/message`
- **Outbound SMS:** `send_message_to_contact(contact_id, message)` in `ghl.py`
- **Owner notifications:** `send_message_to_contact(OWNER_GHL_CONTACT_ID, message)` — no Twilio needed

---

## Coding Conventions

- **Backend:** Python 3.9+, FastAPI with Pydantic models, async where possible, db.py for all DB queries
- **Frontend:** TypeScript strict, functional React components, Tailwind for styling, Shadcn UI primitives
- **API pattern:** Backend returns JSON, frontend fetches via `lib/api.ts` client
- **File naming:** snake_case (Python), kebab-case (TS/TSX files), PascalCase (React components)
- **No over-engineering:** Keep solutions minimal. Don't add abstractions until needed twice.
