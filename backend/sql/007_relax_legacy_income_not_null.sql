ALTER TABLE IF EXISTS onboarding_profiles
  ALTER COLUMN daily_income DROP NOT NULL,
  ALTER COLUMN weekly_income DROP NOT NULL;

CREATE OR REPLACE FUNCTION public.guardgig_migration_007_applied()
RETURNS BOOLEAN
LANGUAGE SQL
SECURITY DEFINER
AS $$
  SELECT
    COALESCE(
      (
        SELECT is_nullable = 'YES'
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'onboarding_profiles'
          AND column_name = 'daily_income'
      ),
      FALSE
    )
    AND
    COALESCE(
      (
        SELECT is_nullable = 'YES'
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'onboarding_profiles'
          AND column_name = 'weekly_income'
      ),
      FALSE
    );
$$;

GRANT EXECUTE ON FUNCTION public.guardgig_migration_007_applied() TO anon, authenticated, service_role;
