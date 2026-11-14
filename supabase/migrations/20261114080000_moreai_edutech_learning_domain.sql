-- First-party MoreAI EduTech domain. All writes are performed by the trusted API/worker.
create table if not exists public.learning_paths (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  created_by_run_id uuid not null references public.agent_runs(id) on delete restrict,
  title text not null check (length(btrim(title)) between 1 and 180),
  description text not null default '',
  education_level text not null default 'self_directed',
  learning_goal text not null default '',
  status text not null default 'draft' check (status in ('draft','active','completed','archived')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists learning_paths_owner_updated_idx on public.learning_paths(owner_user_id, updated_at desc, id desc);

create table if not exists public.learning_modules (
  id uuid primary key default gen_random_uuid(),
  path_id uuid not null references public.learning_paths(id) on delete cascade,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  module_index integer not null check (module_index between 0 and 99),
  title text not null check (length(btrim(title)) between 1 and 180),
  summary text not null default '',
  estimated_minutes integer not null default 30 check (estimated_minutes between 1 and 10080),
  created_at timestamptz not null default now(),
  unique(path_id, module_index),
  unique(id, path_id, owner_user_id)
);
create index if not exists learning_modules_path_order_idx on public.learning_modules(path_id, module_index);

create table if not exists public.learning_lessons (
  id uuid primary key default gen_random_uuid(),
  path_id uuid not null references public.learning_paths(id) on delete cascade,
  module_id uuid not null,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  lesson_index integer not null check (lesson_index between 0 and 199),
  title text not null check (length(btrim(title)) between 1 and 180),
  content_md text not null default '',
  objectives jsonb not null default '[]'::jsonb check (jsonb_typeof(objectives) = 'array'),
  content_version integer not null default 1 check (content_version >= 1),
  status text not null default 'outline' check (status in ('outline','ready','archived')),
  source_run_id uuid references public.agent_runs(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key (module_id, path_id, owner_user_id) references public.learning_modules(id, path_id, owner_user_id) on delete cascade,
  unique(module_id, lesson_index),
  unique(id, path_id, owner_user_id)
);
create index if not exists learning_lessons_module_order_idx on public.learning_lessons(module_id, lesson_index);

create table if not exists public.learning_lesson_versions (
  id uuid primary key default gen_random_uuid(),
  lesson_id uuid not null references public.learning_lessons(id) on delete cascade,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  version integer not null check (version >= 1),
  content_md text not null,
  objectives jsonb not null default '[]'::jsonb,
  source_run_id uuid references public.agent_runs(id) on delete set null,
  created_at timestamptz not null default now(),
  unique(lesson_id, version)
);

create table if not exists public.learning_enrollments (
  id uuid primary key default gen_random_uuid(),
  path_id uuid not null references public.learning_paths(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'active' check (status in ('active','completed','paused','withdrawn')),
  enrolled_at timestamptz not null default now(),
  completed_at timestamptz,
  updated_at timestamptz not null default now(),
  unique(path_id, user_id)
);
create index if not exists learning_enrollments_user_idx on public.learning_enrollments(user_id, updated_at desc);

create table if not exists public.learning_quizzes (
  id uuid primary key default gen_random_uuid(),
  path_id uuid not null references public.learning_paths(id) on delete cascade,
  lesson_id uuid not null,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (length(btrim(title)) between 1 and 180),
  questions jsonb not null check (jsonb_typeof(questions) = 'array' and jsonb_array_length(questions) between 1 and 100),
  pass_score numeric(5,2) not null default 70 check (pass_score between 0 and 100),
  source_run_id uuid references public.agent_runs(id) on delete set null,
  created_at timestamptz not null default now(),
  foreign key (lesson_id, path_id, owner_user_id) references public.learning_lessons(id, path_id, owner_user_id) on delete cascade
);
create index if not exists learning_quizzes_lesson_idx on public.learning_quizzes(lesson_id, created_at desc);

create table if not exists public.learning_quiz_attempts (
  id uuid primary key default gen_random_uuid(),
  quiz_id uuid not null references public.learning_quizzes(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  run_id uuid not null references public.agent_runs(id) on delete restrict,
  answers jsonb not null check (jsonb_typeof(answers) = 'array'),
  score numeric(5,2) not null check (score between 0 and 100),
  passed boolean not null,
  feedback jsonb not null default '{}'::jsonb,
  submitted_at timestamptz not null default now(),
  unique(run_id, quiz_id)
);
create index if not exists learning_quiz_attempts_user_idx on public.learning_quiz_attempts(user_id, submitted_at desc);

create table if not exists public.learning_assessments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  path_id uuid not null references public.learning_paths(id) on delete cascade,
  module_id uuid references public.learning_modules(id) on delete set null,
  lesson_id uuid references public.learning_lessons(id) on delete set null,
  run_id uuid not null references public.agent_runs(id) on delete restrict,
  assessment_type text not null check (assessment_type in ('quiz','formative','project','rubric')),
  score numeric(5,2) check (score between 0 and 100),
  rubric jsonb not null default '[]'::jsonb,
  feedback jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists learning_assessments_user_idx on public.learning_assessments(user_id, created_at desc);

create table if not exists public.learning_progress (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  path_id uuid not null references public.learning_paths(id) on delete cascade,
  module_id uuid not null references public.learning_modules(id) on delete cascade,
  lesson_id uuid not null references public.learning_lessons(id) on delete cascade,
  status text not null default 'not_started' check (status in ('not_started','in_progress','completed')),
  progress_percent numeric(5,2) not null default 0 check (progress_percent between 0 and 100),
  last_run_id uuid references public.agent_runs(id) on delete set null,
  started_at timestamptz,
  completed_at timestamptz,
  updated_at timestamptz not null default now(),
  unique(user_id, lesson_id)
);
create index if not exists learning_progress_user_updated_idx on public.learning_progress(user_id, updated_at desc);

create table if not exists public.learning_run_artifacts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  artifact_type text not null check (artifact_type in ('learning_path','lesson','quiz','assessment','progress')),
  resource_id uuid not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(run_id, artifact_type, resource_id)
);
create index if not exists learning_run_artifacts_user_idx on public.learning_run_artifacts(user_id, created_at desc);

do $$
declare t text;
begin
  foreach t in array array['learning_paths','learning_modules','learning_lessons','learning_lesson_versions','learning_enrollments','learning_quizzes','learning_quiz_attempts','learning_assessments','learning_progress','learning_run_artifacts'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on public.%I from anon, authenticated', t);
    execute format('grant all on public.%I to service_role', t);
  end loop;
end $$;

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
  if jsonb_typeof(p_modules) <> 'array' or jsonb_array_length(p_modules) not between 1 and 30 then
    raise exception 'learning_modules_invalid' using errcode='22023';
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
  values(p_user_id,p_run_id,'learning_path',v_path.id,jsonb_build_object('title',v_path.title,'module_count',v_module_index,'lesson_count',v_count));
  return jsonb_build_object('path_id',v_path.id,'title',v_path.title,'module_count',v_module_index,'lesson_count',v_count,'status',v_path.status);
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
  v_next := v_lesson.content_version + 1;
  if v_lesson.content_md <> '' then
    insert into public.learning_lesson_versions(lesson_id,owner_user_id,version,content_md,objectives,source_run_id)
    values(v_lesson.id,p_user_id,v_lesson.content_version,v_lesson.content_md,v_lesson.objectives,v_lesson.source_run_id);
  end if;
  update public.learning_lessons set title=left(btrim(p_title),180),content_md=p_content_md,
    objectives=case when jsonb_typeof(p_objectives)='array' then p_objectives else '[]'::jsonb end,
    content_version=v_next,status='ready',source_run_id=p_run_id,updated_at=now()
  where id=v_lesson.id;
  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'lesson',v_lesson.id,jsonb_build_object('version',v_next,'title',p_title))
  on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
  return jsonb_build_object('lesson_id',v_lesson.id,'content_version',v_next,'status','ready');
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
  if jsonb_typeof(p_questions)<>'array' or jsonb_array_length(p_questions) not between 1 and 100 then raise exception 'learning_questions_invalid' using errcode='22023'; end if;
  insert into public.learning_quizzes(path_id,lesson_id,owner_user_id,title,questions,pass_score,source_run_id)
  values(v_lesson.path_id,v_lesson.id,p_user_id,left(btrim(p_title),180),p_questions,greatest(0,least(100,coalesce(p_pass_score,70))),p_run_id)
  returning * into v_quiz;
  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'quiz',v_quiz.id,jsonb_build_object('lesson_id',v_lesson.id,'question_count',jsonb_array_length(p_questions)));
  return jsonb_build_object('quiz_id',v_quiz.id,'lesson_id',v_lesson.id,'question_count',jsonb_array_length(p_questions));
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
  if jsonb_typeof(p_answers)<>'array' then raise exception 'learning_answers_invalid' using errcode='22023'; end if;
  insert into public.learning_quiz_attempts(quiz_id,user_id,run_id,answers,score,passed,feedback)
  values(v_quiz.id,p_user_id,p_run_id,p_answers,greatest(0,least(100,p_score)),p_score>=v_quiz.pass_score,coalesce(p_feedback,'{}'::jsonb))
  on conflict(run_id,quiz_id) do update set answers=excluded.answers,score=excluded.score,passed=excluded.passed,feedback=excluded.feedback
  returning * into v_attempt;
  insert into public.learning_assessments(user_id,path_id,lesson_id,run_id,assessment_type,score,rubric,feedback)
  values(p_user_id,v_quiz.path_id,v_quiz.lesson_id,p_run_id,'quiz',v_attempt.score,coalesce(p_rubric,'[]'::jsonb),coalesce(p_feedback,'{}'::jsonb))
  returning * into v_assessment;
  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'assessment',v_assessment.id,jsonb_build_object('quiz_id',v_quiz.id,'attempt_id',v_attempt.id,'score',v_attempt.score,'passed',v_attempt.passed));
  return jsonb_build_object('attempt_id',v_attempt.id,'assessment_id',v_assessment.id,'score',v_attempt.score,'passed',v_attempt.passed);
end $$;

create or replace function public.moreai_learning_progress_update(
  p_user_id uuid,p_run_id uuid,p_lesson_id uuid,p_status text
) returns jsonb language plpgsql security invoker set search_path = ''
as $$
declare v_lesson public.learning_lessons%rowtype; v_progress public.learning_progress%rowtype;
begin
  if not exists(select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then raise exception 'learning_run_owner_mismatch' using errcode='42501'; end if;
  if p_status not in ('in_progress','completed') then raise exception 'learning_progress_status_invalid' using errcode='22023'; end if;
  select * into v_lesson from public.learning_lessons where id=p_lesson_id and owner_user_id=p_user_id;
  if not found then raise exception 'learning_lesson_not_found' using errcode='P0002'; end if;
  insert into public.learning_enrollments(path_id,user_id,status) values(v_lesson.path_id,p_user_id,'active') on conflict(path_id,user_id) do nothing;
  insert into public.learning_progress(user_id,path_id,module_id,lesson_id,status,progress_percent,last_run_id,started_at,completed_at,updated_at)
  values(p_user_id,v_lesson.path_id,v_lesson.module_id,v_lesson.id,p_status,case when p_status='completed' then 100 else 1 end,p_run_id,now(),case when p_status='completed' then now() else null end,now())
  on conflict(user_id,lesson_id) do update set status=excluded.status,progress_percent=excluded.progress_percent,last_run_id=excluded.last_run_id,
    started_at=coalesce(public.learning_progress.started_at,now()),completed_at=case when excluded.status='completed' then now() else null end,updated_at=now()
  returning * into v_progress;
  insert into public.learning_run_artifacts(user_id,run_id,artifact_type,resource_id,payload)
  values(p_user_id,p_run_id,'progress',v_progress.id,jsonb_build_object('lesson_id',v_lesson.id,'status',p_status,'progress_percent',v_progress.progress_percent))
  on conflict(run_id,artifact_type,resource_id) do update set payload=excluded.payload;
  return jsonb_build_object('progress_id',v_progress.id,'lesson_id',v_lesson.id,'status',v_progress.status,'progress_percent',v_progress.progress_percent);
end $$;

revoke all on function public.moreai_learning_path_create(uuid,uuid,text,text,text,text,jsonb) from public, anon, authenticated;
revoke all on function public.moreai_learning_lesson_generate(uuid,uuid,uuid,text,text,jsonb) from public, anon, authenticated;
revoke all on function public.moreai_learning_quiz_generate(uuid,uuid,uuid,text,jsonb,numeric) from public, anon, authenticated;
revoke all on function public.moreai_learning_answer_assess(uuid,uuid,uuid,jsonb,numeric,jsonb,jsonb) from public, anon, authenticated;
revoke all on function public.moreai_learning_progress_update(uuid,uuid,uuid,text) from public, anon, authenticated;
grant execute on function public.moreai_learning_path_create(uuid,uuid,text,text,text,text,jsonb) to service_role;
grant execute on function public.moreai_learning_lesson_generate(uuid,uuid,uuid,text,text,jsonb) to service_role;
grant execute on function public.moreai_learning_quiz_generate(uuid,uuid,uuid,text,jsonb,numeric) to service_role;
grant execute on function public.moreai_learning_answer_assess(uuid,uuid,uuid,jsonb,numeric,jsonb,jsonb) to service_role;
grant execute on function public.moreai_learning_progress_update(uuid,uuid,uuid,text) to service_role;
