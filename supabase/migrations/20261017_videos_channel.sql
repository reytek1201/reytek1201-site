-- Reytek Vision: a one-line tagline for the channel guide and an optional accent color per channel.
alter table public.videos
  add column if not exists tagline text check (char_length(tagline) <= 60),
  add column if not exists color text check (color ~ '^#[0-9a-f]{6}$');
update public.videos set tagline = 'Breakbeat · 131 BPM' where slug = 'dawn-on-the-loading-dock' and tagline is null;
