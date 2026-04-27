create extension if not exists pgcrypto;
create extension if not exists postgis;

create table if not exists public.gis_reports (
  id uuid primary key default gen_random_uuid(),
  report_kind text not null check (report_kind in ('problem', 'idea', 'asset')),
  category_id text not null,
  severity text not null check (severity in ('low', 'medium', 'high')),
  title text not null check (char_length(title) between 3 and 60),
  description text not null check (char_length(description) between 10 and 600),
  action_hint text,
  place_hint text,
  reporter_name text,
  latitude double precision not null,
  longitude double precision not null,
  geom geography(point, 4326),
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  review_note text,
  created_at timestamptz not null default now(),
  reviewed_at timestamptz
);

create or replace function public.sync_gis_reports_geom()
returns trigger
language plpgsql
as $$
begin
  new.geom := st_setsrid(st_makepoint(new.longitude, new.latitude), 4326)::geography;
  return new;
end;
$$;

drop trigger if exists trg_sync_gis_reports_geom on public.gis_reports;
create trigger trg_sync_gis_reports_geom
before insert or update on public.gis_reports
for each row
execute function public.sync_gis_reports_geom();

create index if not exists idx_gis_reports_status on public.gis_reports (status);
create index if not exists idx_gis_reports_category on public.gis_reports (category_id);
create index if not exists idx_gis_reports_created_at on public.gis_reports (created_at desc);
create index if not exists idx_gis_reports_geom on public.gis_reports using gist (geom);

create table if not exists public.gis_moderators (
  email text primary key,
  created_at timestamptz not null default now()
);

create or replace function public.is_gis_moderator()
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.gis_moderators
    where lower(email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  );
$$;

alter table public.gis_reports enable row level security;
alter table public.gis_moderators enable row level security;

drop policy if exists "approved reports are public" on public.gis_reports;
create policy "approved reports are public"
on public.gis_reports
for select
using (status = 'approved' or public.is_gis_moderator());

drop policy if exists "anyone can submit pending reports" on public.gis_reports;
create policy "anyone can submit pending reports"
on public.gis_reports
for insert
with check (status = 'pending');

drop policy if exists "moderators can update reports" on public.gis_reports;
create policy "moderators can update reports"
on public.gis_reports
for update
using (public.is_gis_moderator())
with check (public.is_gis_moderator());

insert into public.gis_moderators (email)
values ('teacher@school.kr')
on conflict (email) do nothing;
