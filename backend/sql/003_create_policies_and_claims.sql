-- Create policies table
CREATE TABLE IF NOT EXISTS policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  weekly_income INT NOT NULL CHECK (weekly_income > 0),
  premium DECIMAL(10,2) NOT NULL CHECK (premium > 0),
  coverage_amount DECIMAL(10,2) NOT NULL DEFAULT 700.00,
  policy_start_date DATE NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'inactive')),
  eligibility_status TEXT NOT NULL DEFAULT 'eligible',
  worker_tier TEXT NOT NULL DEFAULT 'medium',
  active_days INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on user_id for policies
CREATE INDEX IF NOT EXISTS policies_user_id_idx ON policies (user_id);

ALTER TABLE IF EXISTS policies
  ADD COLUMN IF NOT EXISTS eligibility_status TEXT NOT NULL DEFAULT 'eligible',
  ADD COLUMN IF NOT EXISTS worker_tier TEXT NOT NULL DEFAULT 'medium',
  ADD COLUMN IF NOT EXISTS active_days INT NOT NULL DEFAULT 0;

-- Create claims table
CREATE TABLE IF NOT EXISTS claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  policy_id UUID NOT NULL REFERENCES policies(id),
  trigger_type TEXT NOT NULL CHECK (trigger_type IN ('rain', 'aqi', 'orders')),
  trigger_value DECIMAL(10,2),
  payout_amount DECIMAL(10,2) NOT NULL CHECK (payout_amount >= 0),
  status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
  fraud_score DECIMAL(5,4) CHECK (fraud_score >= 0 AND fraud_score <= 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for claims
CREATE INDEX IF NOT EXISTS claims_user_id_idx ON claims (user_id);
CREATE INDEX IF NOT EXISTS claims_policy_id_idx ON claims (policy_id);
CREATE INDEX IF NOT EXISTS claims_status_idx ON claims (status);