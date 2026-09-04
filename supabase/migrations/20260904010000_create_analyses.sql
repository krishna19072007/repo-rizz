-- Per-user analysis history (normal Supabase accounts).
-- Rizz Master admin auth is unrelated to this table.

create table if not exists public.analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,              -- verified server-side from the access token
  owner text not null,
  name text not null,
  score integer not null check (score between 0 and 100),
  status text not null default '',
  summary text not null default '',
  dimensions jsonb not null default '{}'::jsonb,
  rizz_verdict text not null default '',
  critical_count integer not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists analyses_user_created_idx
  on public.analyses (user_id, created_at desc);

-- Row Level Security: a user can only see/delete their own rows.
alter table public.analyses enable row level security;

drop policy if exists analyses_select_own on public.analyses;
create policy analyses_select_own on public.analyses
  for select using (auth.uid() = user_id);

drop policy if exists analyses_insert_own on public.analyses;
create policy analyses_insert_own on public.analyses
  for insert with check (auth.uid() = user_id);

drop policy if exists analyses_delete_own on public.analyses;
create policy analyses_delete_own on public.analyses
  for delete using (auth.uid() = user_id);
