create table if not exists public.customer_learning_progress (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  module_key text not null check (module_key ~ '^[a-z0-9][a-z0-9_-]{0,79}$'),
  lesson_key text not null check (length(lesson_key) between 1 and 512),
  completed_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id,module_key,lesson_key)
);
create index if not exists customer_learning_progress_user_idx
  on public.customer_learning_progress(user_id,module_key,completed_at desc);
alter table public.customer_learning_progress enable row level security;
drop policy if exists customer_learning_progress_server_only on public.customer_learning_progress;
create policy customer_learning_progress_server_only on public.customer_learning_progress
  for all to anon,authenticated using(false) with check(false);
revoke all on public.customer_learning_progress from public,anon,authenticated;
grant all on public.customer_learning_progress to service_role;

create or replace function public.moreai_set_customer_learning_progress(
 p_user_id uuid,p_module_key text,p_lesson_key text,p_completed boolean
) returns jsonb language plpgsql security definer set search_path='' as $$
declare v_row public.customer_learning_progress%rowtype;
begin
 if p_module_key !~ '^[a-z0-9][a-z0-9_-]{0,79}$' or char_length(p_lesson_key) not between 1 and 512 then
   raise exception 'invalid_learning_progress_key' using errcode='22023';
 end if;
 if p_completed then
   insert into public.customer_learning_progress(user_id,module_key,lesson_key,completed_at,updated_at)
   values(p_user_id,p_module_key,p_lesson_key,now(),now())
   on conflict(user_id,module_key,lesson_key) do update set completed_at=now(),updated_at=now()
   returning * into v_row;
   return jsonb_build_object('module_key',v_row.module_key,'lesson_key',v_row.lesson_key,'completed',true,'completed_at',v_row.completed_at);
 else
   delete from public.customer_learning_progress
    where user_id=p_user_id and module_key=p_module_key and lesson_key=p_lesson_key;
   return jsonb_build_object('module_key',p_module_key,'lesson_key',p_lesson_key,'completed',false,'completed_at',null);
 end if;
end; $$;
revoke all on function public.moreai_set_customer_learning_progress(uuid,text,text,boolean) from public,anon,authenticated;
grant execute on function public.moreai_set_customer_learning_progress(uuid,text,text,boolean) to service_role;