-- ROBLOX AI VIDEO FACTORY CLOUD EDITION
-- Run this SQL once in Supabase SQL Editor.
-- The Streamlit server uses the service-role key from Secrets.
-- Never expose that key to browsers or commit it to GitHub.

create table if not exists public.ravf_cloud_records (
    id uuid primary key,
    owner_id text not null,
    kind text not null,
    title text not null,
    payload jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

create index if not exists ravf_cloud_records_owner_kind_updated_idx
    on public.ravf_cloud_records (owner_id, kind, updated_at desc);

alter table public.ravf_cloud_records enable row level security;

-- Intentionally do not add anon/authenticated policies.
-- Server-side requests using the Supabase service-role key bypass RLS.
-- Keep SUPABASE_SERVICE_ROLE_KEY only in Streamlit Secrets.
