-- Site content: the Projects ticket rail. Edited in the back office, published by rebuilding the site.
create table if not exists public.projects (
  id bigint generated always as identity primary key,
  sort integer not null default 0,
  published boolean not null default true,
  slug text not null unique check (slug ~ '^[a-z][a-z0-9-]{0,30}$'),
  name text not null check (char_length(name) between 1 and 60),
  what text not null default '' check (char_length(what) <= 80),
  tag text not null default '' check (char_length(tag) <= 20),
  status text not null default 'live' check (status in ('live', 'served', 'here', 'fire')),
  color text not null default '#22d3ee' check (color ~ '^#[0-9a-fA-F]{6}$'),
  logo jsonb not null default '[]'::jsonb check (jsonb_typeof(logo) = 'array'),
  logo_style text not null default 'logo' check (logo_style in ('logo', 'face')),
  mod text not null default '' check (char_length(mod) <= 80),
  time_value text not null default '' check (char_length(time_value) <= 20),
  lede text not null default '' check (char_length(lede) <= 160),
  story text not null default '' check (char_length(story) <= 2000),
  order_note text not null default '' check (char_length(order_note) <= 40),
  fire_note text not null default '' check (char_length(fire_note) <= 40),
  plated_note text not null default '' check (char_length(plated_note) <= 40),
  stat1_value text check (char_length(stat1_value) <= 20),
  stat1_label text check (char_length(stat1_label) <= 60),
  stat2_value text check (char_length(stat2_value) <= 20),
  stat2_label text check (char_length(stat2_label) <= 60),
  shots jsonb not null default '[]'::jsonb check (jsonb_typeof(shots) = 'array'),
  shots_style text check (shots_style in ('phone', 'wide')),
  link_url text check (link_url ~ '^https://'),
  link_label text check (char_length(link_label) <= 60),
  note text check (char_length(note) <= 120),
  more_url text check (char_length(more_url) <= 200),
  more_label text check (char_length(more_label) <= 60),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists projects_sort_idx on public.projects (sort, id);
create trigger projects_touch before update on public.projects
  for each row execute function public.touch_updated_at();

alter table public.projects enable row level security;
revoke all on table public.projects from public, anon, authenticated;
grant select on table public.projects to anon;
grant all on table public.projects to service_role;
create policy "Published projects are public" on public.projects
  for select to anon using (published);

-- The 5 tickets as they were on the site on Oct 13, 2026.
insert into public.projects (slug, sort, color, tag, name, what, status, logo, logo_style, mod, time_value, lede, story, order_note, fire_note, plated_note, stat1_value, stat1_label, stat2_value, stat2_label, shots, shots_style, link_url, link_label, note, more_url, more_label)
select * from (values
('km', 10, '#34d399', '2024', 'KeyMacro', 'AI nutrition & training app', 'live', '[{"src": "img/logo-keymacro.webp", "alt": "", "w": 512, "h": 512}]'::jsonb, 'logo', 'Eat and train off one plan.', '7 mo', 'My AI nutrition and training partner.', 'KeyMacro builds your meals and your workouts off one plan, so eating and training stop living in separate apps. Coach Key checks in and adjusts when real life happens, Snap logs a plate from a photo, and the Green Zone rewards consistency over perfect grams. The kitchen is still in there: Prep Station splits the week''s cooking by station, just like running a line.', '2024', 'built in 7 months', 'first sale', '7 months', 'concept to first sale', '3 platforms', 'web, iOS and Android', '[{"src": "img/proj/km-today.webp", "alt": "Today''s progress", "w": 540, "h": 1150}, {"src": "img/proj/km-snap.webp", "alt": "Snap a meal", "w": 540, "h": 1150}, {"src": "img/proj/km-coach.webp", "alt": "Coach Key", "w": 540, "h": 1150}]'::jsonb, 'phone', 'https://keymacro.fit', 'Open keymacro.fit ↗', null, null, null),
('sp', 20, '#f16931', '2025', 'SlidePress', 'Social posting app', 'live', '[{"src": "img/logo-slidepress.webp", "alt": "", "w": 485, "h": 512}]'::jsonb, 'logo', 'Three apps → one. Hours → 10 min.', '2 mo', 'Three apps and hours, down to ten minutes.', 'I was making social posts for KeyMacro and bouncing between three apps for every one. A post could take hours. Now I make it and publish it to every account in about ten minutes. It has so many moving parts and reviews to get through, and it still went to production in two months. It''s the build I''m proudest of so far.', '2025', '2 months', 'in production', '2 months', 'to production', '10 min', 'per post, everywhere', '[{"src": "img/proj/sp-editor.webp", "alt": "The slide editor", "w": 560, "h": 1118}, {"src": "img/proj/sp-slide.webp", "alt": "A finished slide", "w": 600, "h": 750}]'::jsonb, 'phone', 'https://www.slidepress.co', 'Open slidepress.co ↗', null, null, null),
('fh', 30, '#c0714f', 'Client', 'FunkHarp', 'Artist website', 'served', '[{"src": "img/logo-funkharp.webp", "alt": "", "w": 360, "h": 360}]'::jsonb, 'logo', 'For a friend who lives both lives.', '2 wk', 'A site for a friend who lives both lives too.', 'Built for a buddy of mine in St. Augustine who is also a chef, and a great musician.', 'a friend', 'built in 2 weeks', 'live', null, null, null, null, '[{"src": "img/proj/fh-site.webp", "alt": "funkharp.com", "w": 960, "h": 504}]'::jsonb, 'wide', 'https://funkharp.com', 'Open funkharp.com ↗', null, null, null),
('rt', 40, '#22d3ee', '2026', 'reytek1201', 'This hub', 'here', '[{"src": "img/proj/face.webp", "alt": "", "w": 320, "h": 320}]'::jsonb, 'face', 'Music, art, projects, play.', '2 wk', 'Music, art, projects and play, under one name.', 'A light-trail vortex, a turntable you can scratch, and four decades on four lanes. Seeing how it''s coming along, it might give the others some competition.', '2026', 'built in 2 weeks', 'you are here', null, null, null, null, '[{"src": "img/proj/rt-site.webp", "alt": "reytek1201.com", "w": 960, "h": 504}]'::jsonb, 'wide', null, null, 'You''re looking at it.', null, null),
('poe', 50, '#e8c06a', 'Dec 11', 'POE Source', 'Path of Exile 2 companion', 'fire', '[{"src": "img/logo-poesource.webp", "alt": "", "w": 720, "h": 720}]'::jsonb, 'logo', 'Leveling guide out. Endgame next.', '{days} d', 'I''ve had this idea since POE2 came out.', 'I never had the tools to build something of this caliber. Now I do. Free guides and tools for Path of Exile 2, and the campaign leveling guide is already live: every act, checkable step by step. The endgame companion is next, and I''m aiming to have it ready for the 1.0 launch.', 'since POE2', 'early access, live', 'Dec 11 · 1.0', null, null, null, null, '[]'::jsonb, null, 'https://poe2source.com/?utm_source=reytek1201&utm_medium=referral&utm_campaign=projects_page', 'Open poe2source.com ↗', null, '../gaming/', 'More on the Gaming page →')
) as v(slug, sort, color, tag, name, what, status, logo, logo_style, mod, time_value, lede, story, order_note, fire_note, plated_note, stat1_value, stat1_label, stat2_value, stat2_label, shots, shots_style, link_url, link_label, note, more_url, more_label)
where not exists (select 1 from public.projects);

-- Optional fields may be left empty in the back office.
alter table public.projects
  alter column what drop not null, alter column tag drop not null, alter column mod drop not null,
  alter column time_value drop not null, alter column lede drop not null, alter column order_note drop not null,
  alter column fire_note drop not null, alter column plated_note drop not null, alter column logo_style drop not null;
