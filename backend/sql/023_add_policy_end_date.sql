ALTER TABLE IF EXISTS public.policies
  ADD COLUMN IF NOT EXISTS end_date TIMESTAMPTZ;

UPDATE public.policies
SET end_date = COALESCE(expires_at, activated_at + INTERVAL '7 days')
WHERE end_date IS NULL;
