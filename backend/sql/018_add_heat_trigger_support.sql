-- Add HEAT trigger support and persist trigger metadata on claims

ALTER TABLE IF EXISTS public.claims
  ADD COLUMN IF NOT EXISTS trigger_reason TEXT,
  ADD COLUMN IF NOT EXISTS payout_percentage INTEGER;

DO $$
DECLARE
  constraint_name text;
BEGIN
  SELECT tc.constraint_name
    INTO constraint_name
  FROM information_schema.table_constraints tc
  JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name
   AND tc.table_schema = ccu.table_schema
  WHERE tc.table_schema = 'public'
    AND tc.table_name = 'claims'
    AND tc.constraint_type = 'CHECK'
    AND ccu.column_name = 'trigger_type'
  LIMIT 1;

  IF constraint_name IS NOT NULL THEN
    EXECUTE format('ALTER TABLE public.claims DROP CONSTRAINT %I', constraint_name);
  END IF;
END $$;

ALTER TABLE IF EXISTS public.claims
  ADD CONSTRAINT claims_trigger_type_check
  CHECK (trigger_type IN ('rain', 'aqi', 'orders', 'HEAT'));
