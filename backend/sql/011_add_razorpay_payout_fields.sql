ALTER TABLE IF EXISTS claims
  ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS transaction_id TEXT,
  ADD COLUMN IF NOT EXISTS paid_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS payout_method TEXT DEFAULT 'Razorpay',
  ADD COLUMN IF NOT EXISTS trigger_snapshot JSONB;

CREATE INDEX IF NOT EXISTS claims_payment_status_idx ON claims (payment_status);