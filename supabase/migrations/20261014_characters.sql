-- Site content: the Gaming page's characters (Player Select + Now playing). Edited in the back office,
-- published by rebuilding the site. Applied to the reytek project on Oct 14, 2026.
create table if not exists public.characters (
  id bigint generated always as identity primary key,
  sort integer not null default 0,
  published boolean not null default true,
  slug text not null unique check (slug ~ '^[a-z][a-z0-9-]{0,30}$'),
  game text not null check (char_length(game) between 1 and 40),
  name text not null check (char_length(name) between 1 and 60),
  status text not null default 'retired' check (status in ('live', 'retired', 'locked')),
  class_line text check (char_length(class_line) <= 60),
  blurb text check (char_length(blurb) <= 300),
  poe_slug text check (poe_slug ~ '^[A-Za-z0-9_-]{4,40}$'),
  planner_url text check (planner_url ~ '^https://'),
  guide_url text check (guide_url ~ '^https://'),
  guide_credit text check (char_length(guide_credit) <= 80),
  videos text check (char_length(videos) <= 600),
  portrait jsonb not null default '[]'::jsonb check (jsonb_typeof(portrait) = 'array'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists characters_sort_idx on public.characters (sort, id);
create trigger characters_touch before update on public.characters
  for each row execute function public.touch_updated_at();

alter table public.characters enable row level security;
revoke all on table public.characters from public, anon, authenticated;
grant select on table public.characters to anon;
grant all on table public.characters to service_role;
create policy "Published characters are public" on public.characters
  for select to anon using (published);

insert into public.characters (slug, sort, game, name, status, class_line, blurb, poe_slug, planner_url, guide_url, guide_credit, videos)
select * from (values
('le-poison-rogues', 10, 'Last Epoch', 'Poison Rogues Necromancer', 'live', 'Acolyte · Necromancer',
 'A minion build: Summon Skeleton Warrior as Rogues, Dread Shade and Aura of Decay. Season 5.',
 null, 'https://www.lastepochtools.com/planner/Bakv46j9',
 'https://actionrpg.com/last-epoch/guide/poison-rogues-necromancer-endgame-build-guide', 'Following the guide by Aaron (ActionRPG)', null),
('poe2-palsteron', 20, 'Path of Exile 2', 'Palsteron Grim Pillars', 'retired', 'Druid · Oracle',
 null, '3JdN4ZekXw', null, null, null, null),
('kaelen', 30, 'Path of Exile 2', 'Kaelen of the Threefold Path', 'retired', 'Monk · Hollow Palm',
 'The Hollow Palm monk, kept as a character with his video series.',
 null, null, null, null, 'Part 1 of 4 | KDcnnFOW5as'),
('diablo', 40, 'Diablo', 'Diablo', 'locked', null, null, null, null, null, null, null)
) as v(slug, sort, game, name, status, class_line, blurb, poe_slug, planner_url, guide_url, guide_credit, videos)
where not exists (select 1 from public.characters);
