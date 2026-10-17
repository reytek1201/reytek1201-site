-- Site content: music videos for the Music page (Watch mode). Edited in the back office, published by
-- rebuilding the site. YouTube hosts the video; the site frames it. One row per video, tied to a release by title.
create table if not exists public.videos (
  id bigint generated always as identity primary key,
  sort integer not null default 0,
  published boolean not null default true,
  slug text not null unique check (slug ~ '^[a-z][a-z0-9-]{0,40}$'),
  release_title text not null check (char_length(release_title) between 1 and 100),
  title text not null check (char_length(title) between 1 and 120),
  kind text not null default 'music-video' check (kind in ('music-video', 'visualizer', 'live', 'making-of')),
  youtube_url text not null check (youtube_url ~ '^https://(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[A-Za-z0-9_-]{11}'),
  published_on date,
  duration text check (char_length(duration) <= 12),
  blurb text check (char_length(blurb) <= 300),
  poster jsonb not null default '[]'::jsonb check (jsonb_typeof(poster) = 'array'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists videos_sort_idx on public.videos (sort, id);
create trigger videos_touch before update on public.videos
  for each row execute function public.touch_updated_at();

alter table public.videos enable row level security;
revoke all on table public.videos from public, anon, authenticated;
grant select on table public.videos to anon;
grant all on table public.videos to service_role;
create policy "Published videos are public" on public.videos
  for select to anon using (published);

insert into public.videos (slug, sort, release_title, title, kind, youtube_url, published_on, blurb)
select 'dawn-on-the-loading-dock', 10, 'Dawn on the Loading Dock', 'Dawn on the Loading Dock', 'music-video',
 'https://www.youtube.com/watch?v=QE1W_VIECWQ', date '2026-10-17',
 'Big drums, sweeping female vocals, and an empty warehouse full of lasers and smoke. 131 BPM.'
where not exists (select 1 from public.videos);
