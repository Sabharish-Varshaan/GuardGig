ALTER TABLE IF EXISTS public.policies
  ADD COLUMN IF NOT EXISTS risk_score DECIMAL(5,4);

ALTER TABLE IF EXISTS public.policies
  DROP CONSTRAINT IF EXISTS policies_risk_score_check;

ALTER TABLE IF EXISTS public.policies
  ADD CONSTRAINT policies_risk_score_check
  CHECK (risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1));

ALTER TABLE IF EXISTS public.claims
  ADD COLUMN IF NOT EXISTS risk_score DECIMAL(5,4);

ALTER TABLE IF EXISTS public.claims
  DROP CONSTRAINT IF EXISTS claims_risk_score_check;

ALTER TABLE IF EXISTS public.claims
  ADD CONSTRAINT claims_risk_score_check
  CHECK (risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1));

CREATE INDEX IF NOT EXISTS claims_risk_score_idx ON public.claims (risk_score);
