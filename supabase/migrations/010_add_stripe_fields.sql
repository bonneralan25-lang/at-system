ALTER TABLE proposals
  ADD COLUMN IF NOT EXISTS pending_booking   JSONB,
  ADD COLUMN IF NOT EXISTS stripe_session_id TEXT,
  ADD COLUMN IF NOT EXISTS deposit_paid      BOOLEAN NOT NULL DEFAULT false;
