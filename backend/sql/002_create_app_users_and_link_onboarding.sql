CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.app_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name TEXT NOT NULL,
  phone TEXT NOT NULL UNIQUE CHECK (phone ~ '^\d{10}$'),
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS app_users_phone_idx ON public.app_users (phone);

-- Re-point onboarding_profiles.user_id FK from auth.users to app_users
ALTER TABLE public.onboarding_profiles DROP CONSTRAINT IF EXISTS onboarding_profiles_user_id_fkey;
ALTER TABLE public.onboarding_profiles
  ADD CONSTRAINT onboarding_profiles_user_id_fkey
  FOREIGN KEY (user_id)
  REFERENCES public.app_users(id)
  ON DELETE CASCADE;
