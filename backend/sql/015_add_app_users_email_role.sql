-- Add email and role support to app_users for admin authentication

ALTER TABLE public.app_users
  ADD COLUMN IF NOT EXISTS email TEXT;

ALTER TABLE public.app_users
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';

UPDATE public.app_users
SET role = COALESCE(role, 'user')
WHERE role IS NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND tablename = 'app_users'
      AND indexname = 'app_users_email_idx'
  ) THEN
    CREATE UNIQUE INDEX app_users_email_idx ON public.app_users (email) WHERE email IS NOT NULL;
  END IF;
END $$;