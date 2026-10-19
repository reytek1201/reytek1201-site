-- Site content: releases (the music). Edited in the back office, published by rebuilding the site.
-- Audio lives in the public `site-audio` bucket, covers in `site-media`. The browser listens to each track when it's
-- uploaded and stores what the turntable and karaoke need: length, loudness, waveform peaks, tempo and beat times.
create table if not exists public.releases (
  id bigint generated always as identity primary key,
  sort integer not null default 0,
  published boolean not null default true,
  title text not null check (char_length(title) between 1 and 100),
  is_new boolean not null default false,
  release_date date,
  notes text check (char_length(notes) <= 600),
  audio jsonb not null default '{}'::jsonb check (jsonb_typeof(audio) = 'object'),
  cover jsonb not null default '[]'::jsonb check (jsonb_typeof(cover) = 'array'),
  label_art jsonb not null default '[]'::jsonb check (jsonb_typeof(label_art) = 'array'),
  duration numeric(8,3),
  gain numeric(5,3) not null default 1,
  bpm numeric(5,1),
  peaks jsonb not null default '[]'::jsonb check (jsonb_typeof(peaks) = 'array'),
  beats jsonb not null default '[]'::jsonb check (jsonb_typeof(beats) = 'array'),
  lyrics_text text check (char_length(lyrics_text) <= 8000),
  lyrics jsonb check (lyrics is null or jsonb_typeof(lyrics) = 'object'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists releases_sort_idx on public.releases (sort, id);
create trigger releases_touch before update on public.releases
  for each row execute function public.touch_updated_at();

alter table public.releases enable row level security;
revoke all on table public.releases from public, anon, authenticated;
grant select on table public.releases to anon;
grant all on table public.releases to service_role;
create policy "Published releases are public" on public.releases
  for select to anon using (published);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('site-audio', 'site-audio', true, 41943040, array['audio/mpeg', 'audio/mp4', 'audio/x-m4a'])
on conflict (id) do nothing;
