UPDATE public.claims
SET fraud_score = ROUND((fraud_score / 100.0)::NUMERIC, 4)
WHERE fraud_score IS NOT NULL
  AND fraud_score > 1
  AND fraud_score <= 100;

ALTER TABLE IF EXISTS public.claims
  DROP CONSTRAINT IF EXISTS claims_fraud_score_check;

ALTER TABLE IF EXISTS public.claims
  ADD CONSTRAINT claims_fraud_score_check
  CHECK (fraud_score IS NULL OR (fraud_score >= 0 AND fraud_score <= 1));
