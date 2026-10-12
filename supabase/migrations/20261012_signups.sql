-- Applied Oct 12, 2026 to the Supabase project "Reytek1201" (ref pehytilcqrmzeuoewdnk, KeyMacro org).
-- Emails from the "Join the transmission" form on reytek1201.com.
create table public.signups (
  id bigint generated always as identity primary key,
  email text not null,
  source text,
  created_at timestamptz not null default now(),
  constraint signups_email_ok check (length(email) <= 254 and email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  constraint signups_source_ok check (source is null or length(source) <= 40)
);
create unique index signups_email_unique on public.signups (lower(email));
comment on table public.signups is 'Emails from the site signup form. Written only through public.join_transmission(); not readable from the browser.';

-- RLS on with no policies: the browser keys can neither read nor write the table directly
alter table public.signups enable row level security;
revoke all on table public.signups from anon, authenticated;

-- the one door in: validates, lowercases, ignores repeats, and never reveals whether an email was already there
create or replace function public.join_transmission(p_email text, p_source text default null)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  e text := lower(btrim(coalesce(p_email, '')));
begin
  if length(e) > 254 or e !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then
    raise exception 'invalid email' using errcode = '22023';
  end if;
  insert into public.signups (email, source)
  values (e, nullif(left(btrim(coalesce(p_source, '')), 40), ''))
  on conflict ((lower(email))) do nothing;
  return true;
end;
$$;
revoke all on function public.join_transmission(text, text) from public;
grant execute on function public.join_transmission(text, text) to anon, authenticated;
