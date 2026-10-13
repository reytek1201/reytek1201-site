-- Site content: the Origin timeline. Edited in the back office, published by rebuilding the site.
create table if not exists public.timeline_moments (
  id bigint generated always as identity primary key,
  sort integer not null default 0,
  year_label text not null check (char_length(year_label) between 1 and 40),
  lane text not null check (lane in ('life', 'kitchen', 'sound', 'code', 'play')),
  title text not null check (char_length(title) between 1 and 160),
  body text not null default '' check (char_length(body) <= 2000),
  anchor text unique check (anchor ~ '^[a-z][a-z0-9-]{0,40}$'),
  media jsonb not null default '[]'::jsonb check (jsonb_typeof(media) = 'array'),
  media_style text check (media_style in ('flat', 'photo', 'pair')),
  published boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists timeline_moments_sort_idx on public.timeline_moments (sort, id);

create or replace function public.touch_updated_at()
returns trigger language plpgsql set search_path = '' as $$
begin new.updated_at = now(); return new; end; $$;
create trigger timeline_moments_touch before update on public.timeline_moments
  for each row execute function public.touch_updated_at();

-- The site build reads published moments with the publishable key; nothing else is public.
alter table public.timeline_moments enable row level security;
revoke all on table public.timeline_moments from public, anon, authenticated;
grant select on table public.timeline_moments to anon;
grant all on table public.timeline_moments to service_role;
create policy "Published moments are public" on public.timeline_moments
  for select to anon using (published);

-- Photos uploaded from the back office. Public to read; only the back office (service role) writes.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('site-media', 'site-media', true, 10485760, array['image/webp', 'image/jpeg', 'image/png'])
on conflict (id) do nothing;

-- The 21 moments as they were on the site on Oct 13, 2026.
insert into public.timeline_moments (sort, year_label, lane, title, body, anchor, media, media_style)
select * from (values
(10, '1976', 'life', 'Born in Puerto Rico', 'Computers and games were part of my life from the very beginning.', null, '[]'::jsonb, null),
(20, '1984', 'play', 'Raised on quarters', 'My dad’s arcades were my first playground: neon signs, cosmic carpet and a change machine that never slept. Galaga taught me patterns. Donkey Kong taught me patience. I was eight, and every game was a world to figure out.', 'y1984', '[{"src": "img/arcade-1984.webp", "alt": "A packed 1980s arcade with Pac-Man, Galaga and Donkey Kong cabinets under neon signs", "w": 1200, "h": 896}]'::jsonb, 'flat'),
(30, '1988', 'life', 'Puerto Rico to North Miami', 'We moved to the US and settled in North Miami, Florida. South Florida became home.', null, '[]'::jsonb, null),
(40, '1991', 'code', 'My first real PC', 'Computers came first. The rave was two years away.', null, '[]'::jsonb, null),
(50, '1992', 'kitchen', 'Dishwasher, Boston Market', 'Hollywood, Florida. My first kitchen job, and the start of more than three decades on the line.', null, '[{"src": "img/boston-market-1992.webp", "alt": "A Boston Market restaurant under palm trees in South Florida", "w": 348, "h": 348}]'::jsonb, 'flat'),
(60, '1993', 'sound', 'The Edge, Fort Lauderdale', 'My first rave. The music took me over and I started dancing to the beats. That day changed my life.', 'y1993', '[{"src": "img/edge-crowd.webp", "alt": "The crowd on the dancefloor at The Edge, Fort Lauderdale", "w": 720, "h": 540}]'::jsonb, 'photo'),
(70, '1994', 'sound', 'First synths', 'A Nord Lead and a Quasimidi Rave-O-Lution 309. I spent every penny I had on that thing.', null, '[{"src": "img/rave-o-lution-309.webp", "alt": "The Quasimidi Rave-O-Lution 309, a silver groovebox covered in knobs and blue buttons", "w": 460, "h": 366}]'::jsonb, 'flat'),
(80, '1995', 'sound', 'Winter Music Conference at The Edge', 'Rabbit in the Moon leading the gathering. Nights with DJ Icey and DJ Sharpe. My friends from the club ate at my restaurants; my crews came out to The Edge.', null, '[{"src": "img/edge-flyer-1995.webp", "alt": "The Edge flyer, March 25, 1995, during Winter Music Conference: Rabbit in the Moon, Spacetime Continuum, Mixmaster Morris", "w": 320, "h": 250}, {"src": "img/edge-flyer-icey.webp", "alt": "The Edge flyer: DJ Icey, DJ Mot, Flux and the resident DJ Sharpe", "w": 320, "h": 250}]'::jsonb, 'pair'),
(90, '1997', 'code', 'My first website', 'It looked good on my computer. On a friend’s it took about 30 minutes to load.', null, '[]'::jsonb, null),
(100, '2005', 'life', 'Georgia, and Benjamin', 'A new state, and on December 1st my son Benjamin was born. Everything changed, in the best way.', null, '[]'::jsonb, null),
(110, '2007', 'sound', 'Full Sail University', 'Audio engineering in Orlando.', 'y2007', '[{"src": "img/full-sail-2007.webp", "alt": "The Full Sail Studios entrance arch in Winter Park, Florida", "w": 250, "h": 187}]'::jsonb, 'flat'),
(120, '2009', 'life', 'Los Angeles', 'I went west for new kitchens and new flavors. LA gave me both, and something I didn’t see coming: film scores. Music that tells a story without saying a word.', null, '[]'::jsonb, null),
(130, 'One night', 'kitchen', '1,000 covers. Four cooks.', 'At Wolfgang Puck’s. The night I’ll never forget.', null, '[]'::jsonb, null),
(140, '2011', 'kitchen', 'Back to South Florida', 'Geronimo’s Bar and Grill: line cook, assistant manager, bartender.', null, '[]'::jsonb, null),
(150, '2016', 'kitchen', 'Executive chef, St. Augustine', 'Three successful restaurants. There is not one kitchen I will work in without music. It’s a necessity, not a want.', 'y2016', '[{"src": "img/keymacro-kitchen.webp", "alt": "Ray Burgos in a chef''s apron at a kitchen counter with fresh vegetables", "w": 400, "h": 300}]'::jsonb, 'flat'),
(160, '2024', 'code', 'Now or never', 'I always wanted to build apps and never had the time. So I saved up and bought my time.', 'y2024', '[]'::jsonb, null),
(170, '2024', 'code', 'KeyMacro', 'My AI nutrition and training partner: meal plans and workouts off one plan, with Coach Key in your corner. Seven months from concept to first sale.', null, '[]'::jsonb, null),
(180, '2025', 'code', 'SlidePress', 'Built out of necessity: social posts used to take me three apps and hours. Now it’s ten minutes, everywhere at once. In production in two months.', null, '[]'::jsonb, null),
(190, '2026', 'sound', 'Back in the studio', 'Threshold of Sound, Sonic Illusion, Dawn on the Loading Dock. I’ve stopped many times, but music always calls me back.', null, '[]'::jsonb, null),
(200, '2026', 'code', 'This hub', 'Every lane in one place.', null, '[]'::jsonb, null),
(210, 'Dec 2026', 'play', 'POE Source', 'Gaming is another parallel highway in my life. POE Source is built to launch with Path of Exile 2 1.0 on December 11.', null, '[]'::jsonb, null)
) as v(sort, year_label, lane, title, body, anchor, media, media_style)
where not exists (select 1 from public.timeline_moments);
