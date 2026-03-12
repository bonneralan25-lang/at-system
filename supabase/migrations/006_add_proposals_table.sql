-- 006_add_proposals_table.sql
-- Stores customer proposal tokens generated when estimates are approved.
-- Each approved estimate gets one token; customer uses the link to book.

CREATE TABLE IF NOT EXISTS proposals (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token             TEXT UNIQUE NOT NULL,
    estimate_id       UUID REFERENCES estimates(id) ON DELETE CASCADE,
    lead_id           UUID REFERENCES leads(id) ON DELETE CASCADE,
    status            TEXT NOT NULL DEFAULT 'sent'
                          CHECK (status IN ('sent', 'viewed', 'booked')),
    selected_tier     TEXT,
    booked_at         TIMESTAMPTZ,
    calendar_event_id TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_proposals_token      ON proposals(token);
CREATE INDEX IF NOT EXISTS idx_proposals_estimate_id ON proposals(estimate_id);
CREATE INDEX IF NOT EXISTS idx_proposals_lead_id     ON proposals(lead_id);
