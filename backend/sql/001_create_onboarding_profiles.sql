create table if not exists public.onboarding_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique,
  full_name text not null,
  age int not null check (age >= 18 and age <= 70),
  city text not null,
  platform text not null,
  vehicle_type text not null check (vehicle_type in ('Bike', 'Scooter', 'Cycle')),
  work_hours int not null check (work_hours > 0 and work_hours <= 24),
  daily_income int not null check (daily_income > 0),
  weekly_income int not null check (weekly_income > 0),
 risk_preference text not null check (risk_preference in ('Low', 'Medium', 'High')),
  onboarding_completed boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists onboarding_profiles_user_id_idx on public.onboarding_profiles (user_id);
