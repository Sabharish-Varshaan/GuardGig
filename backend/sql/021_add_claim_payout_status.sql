ALTER TABLE IF EXISTS public.claims
  ADD COLUMN IF NOT EXISTS payout_status TEXT DEFAULT 'pending';

UPDATE public.claims
SET payout_status = 'pending'
WHERE payout_status IS NULL;

ALTER TABLE IF EXISTS public.claims
  DROP CONSTRAINT IF EXISTS claims_payout_status_check;

ALTER TABLE IF EXISTS public.claims
  ADD CONSTRAINT claims_payout_status_check
  CHECK (payout_status IN ('pending', 'processing', 'credited', 'failed'));

CREATE INDEX IF NOT EXISTS claims_payout_status_idx ON public.claims (payout_status);
