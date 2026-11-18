-- Forward-only hardening for retry-safe EduTech tool invocations.
alter table public.learning_assessments
  add column if not exists quiz_id uuid references public.learning_quizzes(id) on delete cascade;

create unique index if not exists learning_paths_created_run_unique
  on public.learning_paths(created_by_run_id);
create unique index if not exists learning_quizzes_source_run_lesson_unique
  on public.learning_quizzes(source_run_id, lesson_id) where source_run_id is not null;
create unique index if not exists learning_assessments_run_quiz_unique
  on public.learning_assessments(run_id, quiz_id) where quiz_id is not null;

create or replace function public.moreai_learning_path_create(
  p_user_id uuid, p_run_id uuid, p_title text, p_description text,
  p_education_level text, p_learning_goal text, p_modules jsonb
) returns jsonb language plpgsql security invoker set search_path = ''
as $$
declare
  v_path public.learning_paths%rowtype;
  v_module jsonb;
  v_lesson jsonb;
  v_module_row public.learning_modules%rowtype;
  v_module_index integer := 0;
  v_lesson_index integer;
  v_count integer := 0;
begin
  if not exists(select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then
    raise exception 'learning_run_owner_mismatch' using errcode='42501';
  end if;
  if jsonb_typeof(p_modules) is distinct from 'array' then
    raise exception 'learning_modules_invalid' using errcode='22023';
  end if;
  if jsonb_array_length(p_modules) not between 1 and 30 then
    raise exception 'learning_modules_invalid' using errcode='22023';
  end if;
  select * into v_path from public.learning_paths where created_by_run_id=p_run_id and owner_user_id=p_user_id;
  if found then
    select count(*) into v_module_index from public.learning_modules where path_id=v_path.id;
    select count(*) into v_count from public.learning_lessons where path_id=v_path.id;
    return jsonb_build_object('path_id',v_path.id,'title',v_path.title,'module_count',v_module_index,'lesson_count',v_count,'status',v_path.status,'replayed',true);
  end if;
  insert into public.learning_paths(owner_user_id,created_by_run_id,title,description,education_level,learning_goal,status)
  values(p_user_id,p_run_id,left(btrim(p_title),180),coalesce(p_description,''),coalesce(p_education_level,'self_directed'),coalesce(p_learning_goal,''),'active')
  returning * into v_path;
  for v_module in select value from jsonb_array_elements(p_modules) loop
    if length(btrim(coalesce(v_module->>'title',''))) = 0 then raise exception 'learning_module_title_required' using errcode='22023'; end if;
    insert into public.learning_modules(path_id,owner_user_id,module_index,title,summary,estimated_minutes)
    values(v_path.id,p_user_id,v_module_index,left(btrim(v_module->>'title'),180),coalesce(v_module->>'summary',''),greatest(1,least(10080,coalesce((v_module->>'estimated_minutes')::integer,30))))
    returning * into v_module_row;
    v_lesson_index := 0;
    if jsonb_typeof(v_module->'lessons') = 'array' then
      for v_lesson in select value from jsonb_array_elements(v_module->'lessons') loop
        insert into public.learning_lessons(path_id,module_id,owner_user_id,lesson_index,title,content_md,objectives,source_run_id,status)
        values(v_path.id,v_module_row.id,p_user_id,v_lesson_index,left(btrim(coalesce(v_lesson->>'title','Lesson')),180),coalesce(v_lesson->>'content_md',''),case when jsonb_typeof(v_lesson->'objectives')='array' then v_lesson->'objectives' else '[]'::jsonb end,p_run_id,case when coalesce(v_lesson->>'content_md','')='' then 'outline' else 'ready' end);
        v_lesson_index := v_lesson_index + 1; v_count := v_count + 1;
      end loop;
    end if;
    v_module_index := v_module_index + 1;
  end loop;
  insert into public.learning_enrollments(path_id,user_id,status) values(v_path.id,p_user_id,'active') on conflict(path_id,user_id) do nothing;
  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'learning_path',v_path.id,jsonb_build_object('title',v_path.title,'module_count',v_module_index,'lesson_count',v_count))
  on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
  return jsonb_build_object('path_id',v_path.id,'title',v_path.title,'module_count',v_module_index,'lesson_count',v_count,'status',v_path.status,'replayed',false);
end $$;

create or replace function public.moreai_learning_lesson_generate(
  p_user_id uuid,p_run_id uuid,p_lesson_id uuid,p_title text,p_content_md text,p_objectives jsonb
) returns jsonb language plpgsql security invoker set search_path = ''
as $$
declare v_lesson public.learning_lessons%rowtype; v_next integer;
begin
  if not exists(select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then raise exception 'learning_run_owner_mismatch' using errcode='42501'; end if;
  select * into v_lesson from public.learning_lessons where id=p_lesson_id and owner_user_id=p_user_id for update;
  if not found then raise exception 'learning_lesson_not_found' using errcode='P0002'; end if;
  if v_lesson.status='ready' and v_lesson.source_run_id=p_run_id then
    return jsonb_build_object('lesson_id',v_lesson.id,'content_version',v_lesson.content_version,'status','ready','replayed',true);
  end if;
  v_next := case when btrim(v_lesson.content_md)='' then 1 else v_lesson.content_version + 1 end;
  if btrim(v_lesson.content_md) <> '' then
    insert into public.learning_lesson_versions(lesson_id,owner_user_id,version,content_md,objectives,source_run_id)
    values(v_lesson.id,p_user_id,v_lesson.content_version,v_lesson.content_md,v_lesson.objectives,v_lesson.source_run_id)
    on conflict(lesson_id,version) do nothing;
  end if;
  update public.learning_lessons set title=left(btrim(p_title),180),content_md=p_content_md,
    objectives=case when jsonb_typeof(p_objectives)='array' then p_objectives else '[]'::jsonb end,
    content_version=v_next,status='ready',source_run_id=p_run_id,updated_at=now()
  where id=v_lesson.id;
  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'lesson',v_lesson.id,jsonb_build_object('version',v_next,'title',p_title))
  on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
  return jsonb_build_object('lesson_id',v_lesson.id,'content_version',v_next,'status','ready','replayed',false);
end $$;

create or replace function public.moreai_learning_quiz_generate(
  p_user_id uuid,p_run_id uuid,p_lesson_id uuid,p_title text,p_questions jsonb,p_pass_score numeric
) returns jsonb language plpgsql security invoker set search_path = ''
as $$
declare v_lesson public.learning_lessons%rowtype; v_quiz public.learning_quizzes%rowtype;
begin
  if not exists(select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then raise exception 'learning_run_owner_mismatch' using errcode='42501'; end if;
  select * into v_lesson from public.learning_lessons where id=p_lesson_id and owner_user_id=p_user_id;
  if not found then raise exception 'learning_lesson_not_found' using errcode='P0002'; end if;
  if jsonb_typeof(p_questions) is distinct from 'array' then raise exception 'learning_questions_invalid' using errcode='22023'; end if;
  if jsonb_array_length(p_questions) not between 1 and 100 then raise exception 'learning_questions_invalid' using errcode='22023'; end if;
  select * into v_quiz from public.learning_quizzes where source_run_id=p_run_id and lesson_id=p_lesson_id and owner_user_id=p_user_id;
  if found then return jsonb_build_object('quiz_id',v_quiz.id,'lesson_id',v_lesson.id,'question_count',jsonb_array_length(v_quiz.questions),'replayed',true); end if;
  insert into public.learning_quizzes(path_id,lesson_id,owner_user_id,title,questions,pass_score,source_run_id)
  values(v_lesson.path_id,v_lesson.id,p_user_id,left(btrim(p_title),180),p_questions,greatest(0,least(100,coalesce(p_pass_score,70))),p_run_id)
  returning * into v_quiz;
  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'quiz',v_quiz.id,jsonb_build_object('lesson_id',v_lesson.id,'question_count',jsonb_array_length(p_questions)))
  on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
  return jsonb_build_object('quiz_id',v_quiz.id,'lesson_id',v_lesson.id,'question_count',jsonb_array_length(p_questions),'replayed',false);
end $$;

create or replace function public.moreai_learning_answer_assess(
  p_user_id uuid,p_run_id uuid,p_quiz_id uuid,p_answers jsonb,p_score numeric,p_feedback jsonb,p_rubric jsonb
) returns jsonb language plpgsql security invoker set search_path = ''
as $$
declare v_quiz public.learning_quizzes%rowtype; v_attempt public.learning_quiz_attempts%rowtype; v_assessment public.learning_assessments%rowtype;
begin
  if not exists(select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then raise exception 'learning_run_owner_mismatch' using errcode='42501'; end if;
  select * into v_quiz from public.learning_quizzes where id=p_quiz_id and owner_user_id=p_user_id;
  if not found then raise exception 'learning_quiz_not_found' using errcode='P0002'; end if;
  if jsonb_typeof(p_answers) is distinct from 'array' then raise exception 'learning_answers_invalid' using errcode='22023'; end if;
  insert into public.learning_quiz_attempts(quiz_id,user_id,run_id,answers,score,passed,feedback)
  values(v_quiz.id,p_user_id,p_run_id,p_answers,greatest(0,least(100,p_score)),p_score>=v_quiz.pass_score,coalesce(p_feedback,'{}'::jsonb))
  on conflict(run_id,quiz_id) do update set answers=excluded.answers,score=excluded.score,passed=excluded.passed,feedback=excluded.feedback
  returning * into v_attempt;
  insert into public.learning_assessments(user_id,path_id,lesson_id,quiz_id,run_id,assessment_type,score,rubric,feedback)
  values(p_user_id,v_quiz.path_id,v_quiz.lesson_id,v_quiz.id,p_run_id,'quiz',v_attempt.score,coalesce(p_rubric,'[]'::jsonb),coalesce(p_feedback,'{}'::jsonb))
  on conflict(run_id,quiz_id) where quiz_id is not null do update
    set score=excluded.score,rubric=excluded.rubric,feedback=excluded.feedback
  returning * into v_assessment;
  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'assessment',v_assessment.id,jsonb_build_object('quiz_id',v_quiz.id,'attempt_id',v_attempt.id,'score',v_attempt.score,'passed',v_attempt.passed))
  on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
  return jsonb_build_object('attempt_id',v_attempt.id,'assessment_id',v_assessment.id,'score',v_attempt.score,'passed',v_attempt.passed);
end $$;
