-- Migration 005: Add messages table for webhook-stored GHL conversation threads
-- Messages are written by the GHL webhook and read by the dashboard.
-- This eliminates repeated GHL API calls for message display.
CREATE TABLE IF NOT EXISTS messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ghl_message_id  TEXT UNIQUE,               -- GHL's own message ID (used for upsert dedup)
    ghl_contact_id  TEXT NOT NULL,
    lead_id         UUID REFERENCES leads(id) ON DELETE CASCADE,
    direction       TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    body            TEXT NOT NULL DEFAULT '',
    message_type    TEXT DEFAULT 'SMS',
    date_added      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_lead_id       ON messages(lead_id);
CREATE INDEX IF NOT EXISTS idx_messages_ghl_contact_id ON messages(ghl_contact_id);
CREATE INDEX IF NOT EXISTS idx_messages_date_added     ON messages(date_added);
