-- Add color selection fields to proposals table
ALTER TABLE proposals
  ADD COLUMN IF NOT EXISTS selected_color TEXT,
  ADD COLUMN IF NOT EXISTS color_mode     TEXT DEFAULT 'gallery',
  ADD COLUMN IF NOT EXISTS hoa_colors     JSONB,
  ADD COLUMN IF NOT EXISTS custom_color   TEXT;
