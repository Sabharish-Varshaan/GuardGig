DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_policies_user'
  ) THEN
    ALTER TABLE public.policies
      ADD CONSTRAINT fk_policies_user
      FOREIGN KEY (user_id)
      REFERENCES public.app_users(id)
      ON DELETE CASCADE;
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_claims_user'
  ) THEN
    ALTER TABLE public.claims
      ADD CONSTRAINT fk_claims_user
      FOREIGN KEY (user_id)
      REFERENCES public.app_users(id)
      ON DELETE CASCADE;
  END IF;
END;
$$;
