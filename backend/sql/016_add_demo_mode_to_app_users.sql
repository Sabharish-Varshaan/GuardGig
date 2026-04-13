-- Add per-user demo-mode persistence for frontend toggle backend sync

ALTER TABLE public.app_users
  ADD COLUMN IF NOT EXISTS demo_mode_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS demo_mode_enabled_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS app_users_demo_mode_enabled_idx
  ON public.app_users (demo_mode_enabled);
