-- Create system_metrics table for actuarial intelligence layer
-- Single-row design: tracks total premiums, payouts, and loss ratio system-wide

CREATE TABLE IF NOT EXISTS system_metrics (
  id SERIAL PRIMARY KEY,
  total_premium DECIMAL(15,2) NOT NULL DEFAULT 0,
  total_payout DECIMAL(15,2) NOT NULL DEFAULT 0,
  loss_ratio DECIMAL(5,4) NOT NULL DEFAULT 0,
  updated_by TEXT,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on last_updated for querying recent metrics
CREATE INDEX IF NOT EXISTS system_metrics_last_updated_idx ON system_metrics (last_updated);

-- Initialize single row if it doesn't exist
TRUNCATE TABLE system_metrics;
INSERT INTO system_metrics (id, total_premium, total_payout, loss_ratio, updated_by, last_updated)
VALUES (1, 0, 0, 0, 'initialization', NOW());
