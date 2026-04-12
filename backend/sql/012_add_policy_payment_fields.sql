ALTER TABLE IF EXISTS policies
  ADD COLUMN IF NOT EXISTS payment_status TEXT NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS payment_id TEXT,
  ADD COLUMN IF NOT EXISTS activated_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS policies_payment_status_idx ON policies (payment_status);