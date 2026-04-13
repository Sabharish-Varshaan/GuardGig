ALTER TABLE policies
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;

UPDATE policies
SET expires_at = activated_at + INTERVAL '7 days'
WHERE activated_at IS NOT NULL
  AND expires_at IS NULL;
