ALTER TABLE IF EXISTS onboarding_profiles
  ADD COLUMN IF NOT EXISTS min_income DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS max_income DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS mean_income DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS income_variance DECIMAL(10,4) NOT NULL DEFAULT 0;

ALTER TABLE IF EXISTS policies
  ADD COLUMN IF NOT EXISTS min_income DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS max_income DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS mean_income DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS income_variance DECIMAL(10,4) NOT NULL DEFAULT 0;

UPDATE onboarding_profiles
SET
  mean_income = COALESCE(mean_income, daily_income::DECIMAL(10,2)),
  min_income = COALESCE(min_income, ROUND((daily_income * 0.7)::NUMERIC, 2)),
  max_income = COALESCE(max_income, ROUND((daily_income * 1.3)::NUMERIC, 2));

UPDATE onboarding_profiles
SET
  income_variance = CASE
    WHEN COALESCE(mean_income, 0) = 0 THEN 0
    ELSE ROUND(((COALESCE(max_income, 0) - COALESCE(min_income, 0)) / mean_income)::NUMERIC, 4)
  END;

UPDATE policies p
SET
  min_income = COALESCE(p.min_income, o.min_income),
  max_income = COALESCE(p.max_income, o.max_income),
  mean_income = COALESCE(p.mean_income, o.mean_income),
  income_variance = COALESCE(p.income_variance, o.income_variance, 0),
  weekly_income = CASE
    WHEN COALESCE(o.mean_income, 0) > 0 THEN ROUND((o.mean_income * 7)::NUMERIC)::INT
    ELSE p.weekly_income
  END
FROM onboarding_profiles o
WHERE p.user_id = o.user_id;
