DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_policy_onboarding'
  ) THEN
    ALTER TABLE public.policies
      ADD CONSTRAINT fk_policy_onboarding
      FOREIGN KEY (user_id)
      REFERENCES public.onboarding_profiles(user_id)
      ON DELETE CASCADE;
  END IF;
END;
$$;
