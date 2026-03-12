-- Allow 'preview' status for internal VA previews (not sent to customer)
ALTER TABLE proposals
  DROP CONSTRAINT IF EXISTS proposals_status_check;

ALTER TABLE proposals
  ADD CONSTRAINT proposals_status_check
    CHECK (status IN ('sent', 'viewed', 'booked', 'preview'));
