-- Agent progress is start-only; passing persisted assessments derive completion.
create or replace function public.moreai_learning_progress_update(
 p_user_id uuid,p_run_id uuid,p_lesson_id uuid,p_status text
) returns jsonb language plpgsql security invoker set search_path = ''
as $$
declare v_lesson public.learning_lessons%rowtype; v_progress public.learning_progress%rowtype;
begin
 if not exists(select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then raise exception 'learning_run_owner_mismatch' using errcode='42501'; end if;
 if p_status <> 'in_progress' then raise exception 'learning_progress_completion_is_assessment_derived' using errcode='22023'; end if;
 select * into v_lesson from public.learning_lessons where id=p_lesson_id and owner_user_id=p_user_id;
 if not found then raise exception 'learning_lesson_not_found' using errcode='P0002'; end if;
 insert into public.learning_enrollments(path_id,user_id,status) values(v_lesson.path_id,p_user_id,'active')
 on conflict(path_id,user_id) do update set status=case when public.learning_enrollments.status='completed' then 'completed' else 'active' end,updated_at=now();
 insert into public.learning_progress(user_id,path_id,module_id,lesson_id,status,progress_percent,last_run_id,started_at,completed_at,updated_at)
 values(p_user_id,v_lesson.path_id,v_lesson.module_id,v_lesson.id,'in_progress',1,p_run_id,now(),null,now())
 on conflict(user_id,lesson_id) do update set
 status=case when public.learning_progress.status='completed' then 'completed' else 'in_progress' end,
 progress_percent=case when public.learning_progress.status='completed' then 100 else greatest(public.learning_progress.progress_percent,1) end,
 last_run_id=excluded.last_run_id,started_at=coalesce(public.learning_progress.started_at,now()),
 completed_at=case when public.learning_progress.status='completed' then public.learning_progress.completed_at else null end,updated_at=now()
 returning * into v_progress;
 insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
 values(p_user_id,p_run_id,'progress',v_progress.id,jsonb_build_object('lesson_id',v_lesson.id,'status',v_progress.status,'progress_percent',v_progress.progress_percent))
 on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
 return jsonb_build_object('progress_id',v_progress.id,'lesson_id',v_lesson.id,'status',v_progress.status,'progress_percent',v_progress.progress_percent);
end $$;

create or replace function public.moreai_learning_answer_assess(
 p_user_id uuid,p_run_id uuid,p_quiz_id uuid,p_answers jsonb,p_score numeric,p_feedback jsonb,p_rubric jsonb
) returns jsonb language plpgsql security invoker set search_path = ''
as $$
declare v_quiz public.learning_quizzes%rowtype; v_attempt public.learning_quiz_attempts%rowtype;
 v_assessment public.learning_assessments%rowtype; v_all_passed boolean; v_progress public.learning_progress%rowtype; v_remaining integer;
begin
 if not exists(select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then raise exception 'learning_run_owner_mismatch' using errcode='42501'; end if;
 select * into v_quiz from public.learning_quizzes where id=p_quiz_id and owner_user_id=p_user_id;
 if not found then raise exception 'learning_quiz_not_found' using errcode='P0002'; end if;
 if jsonb_typeof(p_answers)<>'array' then raise exception 'learning_answers_invalid' using errcode='22023'; end if;
 insert into public.learning_quiz_attempts(quiz_id,user_id,run_id,answers,score,passed,feedback)
 values(v_quiz.id,p_user_id,p_run_id,p_answers,greatest(0,least(100,p_score)),p_score>=v_quiz.pass_score,coalesce(p_feedback,'{}'::jsonb))
 on conflict(run_id,quiz_id) do update set answers=excluded.answers,score=excluded.score,passed=excluded.passed,feedback=excluded.feedback returning * into v_attempt;
 insert into public.learning_assessments(user_id,path_id,lesson_id,run_id,assessment_type,score,rubric,feedback)
 values(p_user_id,v_quiz.path_id,v_quiz.lesson_id,p_run_id,'quiz',v_attempt.score,coalesce(p_rubric,'[]'::jsonb),coalesce(p_feedback,'{}'::jsonb)) returning * into v_assessment;
 insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
 values(p_user_id,p_run_id,'assessment',v_assessment.id,jsonb_build_object('quiz_id',v_quiz.id,'attempt_id',v_attempt.id,'score',v_attempt.score,'passed',v_attempt.passed));
 if v_attempt.passed then
  select not exists(select 1 from public.learning_quizzes q where q.lesson_id=v_quiz.lesson_id and q.owner_user_id=p_user_id
   and not exists(select 1 from public.learning_quiz_attempts a where a.quiz_id=q.id and a.user_id=p_user_id and a.passed=true)) into v_all_passed;
  if v_all_passed then
   update public.learning_progress set status='completed',progress_percent=100,completed_at=coalesce(completed_at,now()),updated_at=now(),last_run_id=p_run_id
   where user_id=p_user_id and lesson_id=v_quiz.lesson_id returning * into v_progress;
   if found then
    insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
    values(p_user_id,p_run_id,'progress',v_progress.id,jsonb_build_object('lesson_id',v_quiz.lesson_id,'status','completed','progress_percent',100,'completion_source','all_required_quizzes_passed'))
    on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
   end if;
   select count(*) into v_remaining from public.learning_lessons l where l.path_id=v_quiz.path_id and l.owner_user_id=p_user_id
    and not exists(select 1 from public.learning_progress p where p.lesson_id=l.id and p.user_id=p_user_id and p.status='completed');
   if v_remaining=0 then update public.learning_enrollments set status='completed',completed_at=coalesce(completed_at,now()),updated_at=now() where path_id=v_quiz.path_id and user_id=p_user_id; end if;
  end if;
 end if;
 return jsonb_build_object('attempt_id',v_attempt.id,'assessment_id',v_assessment.id,'score',v_attempt.score,'passed',v_attempt.passed,'lesson_completed',coalesce(v_progress.status='completed',false));
end $$;
revoke all on function public.moreai_learning_progress_update(uuid,uuid,uuid,text) from public,anon,authenticated;
revoke all on function public.moreai_learning_answer_assess(uuid,uuid,uuid,jsonb,numeric,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.moreai_learning_progress_update(uuid,uuid,uuid,text) to service_role;
grant execute on function public.moreai_learning_answer_assess(uuid,uuid,uuid,jsonb,numeric,jsonb,jsonb) to service_role;
