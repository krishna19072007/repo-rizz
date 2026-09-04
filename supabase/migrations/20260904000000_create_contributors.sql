-- ============================================================
-- Repo Rizz — contributors table (Supabase)
--
-- Run with the Supabase CLI:
--   supabase db push
-- or execute this file in the Supabase SQL editor.
--
-- This matches the table the Repo Rizz backend writes to. The backend
-- store translates between these column names and the app's canonical
-- contributor shape:
--   name      <- display_name
--   image_url <- custom avatar upload URL (GitHub avatars are derived
--                from github_username by the frontend, never stored)
--
-- The id is a uuid; the app treats contributor ids as opaque strings, so
-- SQLite (integer ids) and Supabase (uuid ids) both work with the same API.
--
-- Authorization model:
--   - Public visitors may SELECT (read) contributor rows. No
--     INSERT / UPDATE / DELETE policies are granted to anon or
--     authenticated roles, so the public can NEVER mutate contributors
--     directly via the Supabase API.
--   - All writes are performed by the Repo Rizz backend using the
--     service-role key, which bypasses RLS. The backend independently
--     enforces the Rizz Master admin session + CSRF before writing.
-- ============================================================

create table if not exists public.contributors (
    id              uuid primary key default gen_random_uuid(),
    name            text not null,
    github_username text not null unique,
    github_url      text not null,
    role            text not null default '',
    description     text not null default '',
    image_url       text not null default '',
    display_order   integer not null default 0,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

-- Enable Row Level Security: the table is locked down by default.
alter table public.contributors enable row level security;

-- Public read access for everyone (anonymous visitors).
create policy "contributors_public_read"
    on public.contributors
    for select
    to anon, authenticated
    using (true);

-- NOTE: No insert/update/delete policies exist for anon/authenticated.
-- The backend writes through the service-role key only.
