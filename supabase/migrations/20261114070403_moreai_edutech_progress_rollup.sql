-- Keep enrollment/path lifecycle in sync with canonical lesson completion.
create or replace function public.moreai_learning_progress_update(
  p_user_id uuid,p_run_id uuid,p_lesson_id uuid,p_status text
) returns jsonb language plpgsql security invoker set search_path = ''
as $$
declare
  v_lesson public.learning_lessons%rowtype;
  v_progress public.learning_progress%rowtype;
  v_total integer;
  v_completed integer;
  v_percent numeric(5,2);
  v_path_status text;
begin
  if not exists(select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then
    raise exception 'learning_run_owner_mismatch' using errcode='42501';
  end if;
  if p_status not in ('in_progress','completed') then
    raise exception 'learning_progress_status_invalid' using errcode='22023';
  end if;
  select * into v_lesson from public.learning_lessons where id=p_lesson_id and owner_user_id=p_user_id;
  if not found then raise exception 'learning_lesson_not_found' using errcode='P0002'; end if;

  insert into public.learning_enrollments(path_id,user_id,status)
  values(v_lesson.path_id,p_user_id,'active')
  on conflict(path_id,user_id) do update set status='active',completed_at=null,updated_at=now();

  insert into public.learning_progress(user_id,path_id,module_id,lesson_id,status,progress_percent,last_run_id,started_at,completed_at,updated_at)
  values(p_user_id,v_lesson.path_id,v_lesson.module_id,v_lesson.id,p_status,case when p_status='completed' then 100 else 1 end,p_run_id,now(),case when p_status='completed' then now() else null end,now())
  on conflict(user_id,lesson_id) do update set status=excluded.status,progress_percent=excluded.progress_percent,last_run_id=excluded.last_run_id,
    started_at=coalesce(public.learning_progress.started_at,now()),completed_at=case when excluded.status='completed' then now() else null end,updated_at=now()
  returning * into v_progress;

  select count(*),count(*) filter (where p.status='completed')
    into v_total,v_completed
    from public.learning_lessons l
    left join public.learning_progress p on p.lesson_id=l.id and p.user_id=p_user_id
   where l.path_id=v_lesson.path_id and l.owner_user_id=p_user_id;
  v_percent := case when v_total=0 then 0 else round((v_completed::numeric / v_total::numeric) * 100, 2) end;
  v_path_status := case when v_total>0 and v_completed=v_total then 'completed' else 'active' end;

  update public.learning_enrollments
     set status=case when v_path_status='completed' then 'completed' else 'active' end,
         completed_at=case when v_path_status='completed' then coalesce(completed_at,now()) else null end,
         updated_at=now()
   where path_id=v_lesson.path_id and user_id=p_user_id;
  update public.learning_paths set status=v_path_status,updated_at=now()
   where id=v_lesson.path_id and owner_user_id=p_user_id;

  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'progress',v_progress.id,jsonb_build_object(
    'lesson_id',v_lesson.id,'status',p_status,'progress_percent',v_progress.progress_percent,
    'path_progress_percent',v_percent,'completed_lessons',v_completed,'total_lessons',v_total
  ))
  on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
  return jsonb_build_object(
    'progress_id',v_progress.id,'lesson_id',v_lesson.id,'status',v_progress.status,
    'progress_percent',v_progress.progress_percent,'path_status',v_path_status,
    'path_progress_percent',v_percent,'completed_lessons',v_completed,'total_lessons',v_total
  );
end $$;

revoke all on function public.moreai_learning_progress_update(uuid,uuid,uuid,text) from public, anon, authenticated;
grant execute on function public.moreai_learning_progress_update(uuid,uuid,uuid,text) to service_role;
