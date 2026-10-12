-- Applied Oct 12, 2026 to the Supabase project "Reytek1201" (ref pehytilcqrmzeuoewdnk, KeyMacro org).
-- Project requests from the order pad on reytek1201.com/work.
create table public.inquiries (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  name text not null,
  email text not null,
  items text[] not null default '{}',
  details text,
  timeline text,
  budget text,
  source text,
  status text not null default 'new',
  constraint inquiries_name_ok check (length(btrim(name)) between 1 and 120),
  constraint inquiries_email_ok check (length(email) <= 254 and email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  constraint inquiries_details_ok check (details is null or length(details) <= 4000),
  constraint inquiries_items_ok check (items <@ array['website','modernize','webapp','mobile','ai','automation']::text[]),
  constraint inquiries_timeline_ok check (timeline is null or timeline in ('asap','month','quarter','exploring')),
  constraint inquiries_budget_ok check (budget is null or budget in ('under-1500','1500-5000','5000-15000','15000-plus','unsure')),
  constraint inquiries_status_ok check (status in ('new','replied','won','passed'))
);
create index inquiries_created on public.inquiries (created_at desc);
create index inquiries_email_recent on public.inquiries (lower(email), created_at desc);
comment on table public.inquiries is 'Orders from the /work page. Written only through public.place_order(); not readable from the browser.';

alter table public.inquiries enable row level security;
revoke all on table public.inquiries from anon, authenticated;

-- the one door in: validates everything and quietly drops floods from one address
create or replace function public.place_order(
  p_name text, p_email text, p_items text[] default '{}', p_details text default null,
  p_timeline text default null, p_budget text default null, p_source text default null)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  e text := lower(btrim(coalesce(p_email, '')));
  n text := btrim(coalesce(p_name, ''));
  d text := nullif(btrim(coalesce(p_details, '')), '');
  its text[] := coalesce(p_items, '{}');
begin
  if length(n) < 1 or length(n) > 120 then raise exception 'invalid name' using errcode = '22023'; end if;
  if length(e) > 254 or e !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then raise exception 'invalid email' using errcode = '22023'; end if;
  if d is not null and length(d) > 4000 then raise exception 'details too long' using errcode = '22023'; end if;
  if not (its <@ array['website','modernize','webapp','mobile','ai','automation']::text[]) or cardinality(its) > 6 then raise exception 'invalid items' using errcode = '22023'; end if;
  if p_timeline is not null and p_timeline not in ('asap','month','quarter','exploring') then raise exception 'invalid timeline' using errcode = '22023'; end if;
  if p_budget is not null and p_budget not in ('under-1500','1500-5000','5000-15000','15000-plus','unsure') then raise exception 'invalid budget' using errcode = '22023'; end if;
  if cardinality(its) = 0 and d is null then raise exception 'empty order' using errcode = '22023'; end if;
  -- more than 5 orders from one address in a day: accept politely, save nothing
  if (select count(*) from public.inquiries where lower(email) = e and created_at > now() - interval '1 day') >= 5 then return true; end if;
  insert into public.inquiries (name, email, items, details, timeline, budget, source)
  values (n, e, (select coalesce(array_agg(distinct x), '{}') from unnest(its) x), d, p_timeline, p_budget, nullif(left(btrim(coalesce(p_source, '')), 40), ''));
  return true;
end;
$$;
revoke all on function public.place_order(text, text, text[], text, text, text, text) from public;
grant execute on function public.place_order(text, text, text[], text, text, text, text) to anon, authenticated;
