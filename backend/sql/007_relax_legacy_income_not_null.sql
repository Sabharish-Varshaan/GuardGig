ALTER TABLE IF EXISTS onboarding_profiles
  ALTER COLUMN daily_income DROP NOT NULL,
  ALTER COLUMN weekly_income DROP NOT NULL;
