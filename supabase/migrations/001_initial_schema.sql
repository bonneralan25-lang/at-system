-- Operations Dashboard — Initial Schema
-- Run this in the Supabase SQL editor at: https://app.supabase.com

-- Leads table: incoming GHL contacts
CREATE TABLE IF NOT EXISTS leads (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ghl_contact_id  TEXT NOT NULL,
  service_type    TEXT NOT NULL CHECK (service_type IN ('fence_staining', 'pressure_washing')),
  status          TEXT NOT NULL DEFAULT 'new'
                  CHECK (status IN ('new', 'estimated', 'approved', 'rejected', 'sent')),
  address         TEXT NOT NULL DEFAULT '',
  form_data       JSONB NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_service_type ON leads(service_type);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_ghl_contact_id ON leads(ghl_contact_id);

-- Estimates table: generated estimates with breakdown
CREATE TABLE IF NOT EXISTS estimates (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id         UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  service_type    TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'approved', 'rejected', 'adjusted')),
  inputs          JSONB NOT NULL DEFAULT '{}',
  breakdown       JSONB NOT NULL DEFAULT '[]',
  estimate_low    NUMERIC(10, 2) NOT NULL,
  estimate_high   NUMERIC(10, 2) NOT NULL,
  owner_notes     TEXT,
  approved_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_estimates_status ON estimates(status);
CREATE INDEX idx_estimates_lead_id ON estimates(lead_id);
CREATE INDEX idx_estimates_approved_at ON estimates(approved_at DESC);

-- Pricing config: configurable per-service pricing rules
CREATE TABLE IF NOT EXISTS pricing_config (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  service_type    TEXT NOT NULL UNIQUE,
  config          JSONB NOT NULL DEFAULT '{}',
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Notification log (for auditing)
CREATE TABLE IF NOT EXISTS notification_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  estimate_id     UUID REFERENCES estimates(id) ON DELETE CASCADE,
  channel         TEXT NOT NULL CHECK (channel IN ('sms', 'email', 'push')),
  status          TEXT NOT NULL DEFAULT 'sent',
  sent_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed default pricing configs
INSERT INTO pricing_config (service_type, config) VALUES
(
  'fence_staining',
  '{
    "base_rate_per_sqft": 1.50,
    "age_factors": {"lt5": 1.0, "yr5_10": 1.1, "gt10": 1.25},
    "prep_factor_new": 1.15,
    "urgency_factors": {"flexible": 1.0, "within_month": 1.05, "rush": 1.25},
    "estimate_margin": 0.10
  }'::jsonb
),
(
  'pressure_washing',
  '{
    "base_rate_per_sqft": 0.25,
    "surface_factors": {"concrete": 1.0, "deck": 1.2, "siding": 1.3, "other": 1.0},
    "condition_factors": {"good": 1.0, "fair": 1.15, "poor": 1.35},
    "estimate_margin": 0.10
  }'::jsonb
)
ON CONFLICT (service_type) DO NOTHING;
