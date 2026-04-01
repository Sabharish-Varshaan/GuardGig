ALTER TABLE IF EXISTS policies
  ADD COLUMN IF NOT EXISTS waiting_period_hours INT NOT NULL DEFAULT 24 CHECK (waiting_period_hours >= 0);

ALTER TABLE IF EXISTS claims
  ADD COLUMN IF NOT EXISTS activity_status TEXT,
  ADD COLUMN IF NOT EXISTS location_valid BOOLEAN,
  ADD COLUMN IF NOT EXISTS rule_decision_reason TEXT;

CREATE INDEX IF NOT EXISTS claims_user_created_at_idx ON claims (user_id, created_at);
