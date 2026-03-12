-- Admin-managed booking availability calendar
CREATE TABLE IF NOT EXISTS schedule_slots (
  date          DATE        PRIMARY KEY,
  is_available  BOOLEAN     NOT NULL DEFAULT true,
  label         TEXT,
  max_bookings  INTEGER     NOT NULL DEFAULT 1,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schedule_slots_date ON schedule_slots(date);
