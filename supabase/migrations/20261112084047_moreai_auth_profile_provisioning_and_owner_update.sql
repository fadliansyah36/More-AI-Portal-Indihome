begin;
create schema if not exists auth_private;
revoke all on schema auth_private from public, anon, authenticated;

create or replace function auth_private.handle_new_user_profile()
returns trigger language plpgsql security definer set search_path = '' as $$
declare v_display_name text;
begin
  v_display_name := nullif(left(regexp_replace(coalesce(new.raw_user_meta_data ->> 'full_name', ''), '[[:cntrl:]]', '', 'g'), 80), '');
  insert into public.profiles (id, display_name, locale, timezone)
  values (new.id, v_display_name, 'id-ID', 'Asia/Jakarta')
  on conflict (id) do nothing;
  return new;
end;
$$;
revoke all on function auth_private.handle_new_user_profile() from public, anon, authenticated;
drop trigger if exists moreai_auth_user_profile_created on auth.users;
create trigger moreai_auth_user_profile_created after insert on auth.users for each row execute function auth_private.handle_new_user_profile();
drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
insert into public.profiles (id, display_name, locale, timezone)
select u.id, nullif(left(regexp_replace(coalesce(u.raw_user_meta_data ->> 'full_name', ''), '[[:cntrl:]]', '', 'g'), 80), ''), 'id-ID', 'Asia/Jakarta'
from auth.users u on conflict (id) do nothing;
commit;