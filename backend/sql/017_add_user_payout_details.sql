-- Add per-user payout recipient details and masked payout destination support

CREATE TABLE IF NOT EXISTS public.user_payout_details (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES public.app_users(id) ON DELETE CASCADE,
  account_holder_name TEXT NOT NULL,
  bank_account_number TEXT,
  ifsc_code TEXT,
  upi_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (
    ((bank_account_number IS NOT NULL AND ifsc_code IS NOT NULL) OR upi_id IS NOT NULL)
    AND NOT (bank_account_number IS NULL AND ifsc_code IS NOT NULL)
    AND NOT (bank_account_number IS NOT NULL AND ifsc_code IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS user_payout_details_user_id_idx
  ON public.user_payout_details (user_id);

ALTER TABLE IF EXISTS public.claims
  ADD COLUMN IF NOT EXISTS masked_account TEXT;

CREATE INDEX IF NOT EXISTS claims_payout_method_idx
  ON public.claims (payout_method);
