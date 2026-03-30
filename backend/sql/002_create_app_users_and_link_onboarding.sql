create extension if not exists pgcrypto;

create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  phone text not null unique check (phone ~ '^\d{10}$'),
  password_hash text not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists app_users_phone_idx on public.app_users (phone);

-- Re-point onboarding_profiles.user_id FK from auth.users to app_users
do $$
begin
  if exists (
    select 1
    from information_schema.tables
    where table_schema = 'public' and table_name = 'onboarding_profiles'
  ) then
    alter table public.onboarding_profiles drop constraint if exists onboarding_profiles_user_id_fkey;
    alter table public.onboarding_profiles
      add constraint onboarding_profiles_user_id_fkey
      foreign key (user_id)
      references public.app_users(id)
      on delete cascade;
  end if;
end $$;
