CREATE TABLE IF NOT EXISTS onboarding_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  age INT NOT NULL CHECK (age >= 18 AND age <= 70),
  city TEXT NOT NULL,
  platform TEXT NOT NULL,
  vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('Bike', 'Scooter', 'Cycle')),
  work_hours INT NOT NULL CHECK (work_hours > 0 AND work_hours <= 24),
  daily_income INT NOT NULL CHECK (daily_income > 0),
  weekly_income INT NOT NULL CHECK (weekly_income > 0),
  risk_preference TEXT NOT NULL CHECK (risk_preference IN ('Low', 'Medium', 'High')),
  onboarding_completed BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS onboarding_profiles_user_id_idx ON onboarding_profiles (user_id);
