-- Enforce the MoreAI browser-to-FastAPI-only business-data boundary explicitly.
-- These tables are accessed through FastAPI/service_role; browser clients must not
-- query them directly. RLS was already enabled; policies make the deny intent explicit.

do $$
declare
  v_table text;
  v_policy text;
  v_tables text[] := array[
    'learning_assessments',
    'learning_enrollments',
    'learning_lesson_versions',
    'learning_lessons',
    'learning_modules',
    'learning_paths',
    'learning_progress',
    'learning_quiz_attempts',
    'learning_quizzes',
    'learning_run_artifacts',
    'moreai_browser_action_receipts',
    'moreai_browser_session_events',
    'moreai_browser_sessions',
    'moreai_computer_action_receipts',
    'moreai_customer_agent_configs',
    'moreai_worker_capability_snapshots'
  ];
begin
  foreach v_table in array v_tables loop
    if not exists (
      select 1
      from pg_class c
      join pg_namespace n on n.oid=c.relnamespace
      where n.nspname='public'
        and c.relname=v_table
        and c.relkind='r'
        and c.relrowsecurity
    ) then
      raise exception 'server_only_rls_table_missing_or_rls_disabled: %', v_table;
    end if;

    v_policy := 'moreai_deny_client_' || v_table;
    execute format('drop policy if exists %I on public.%I', v_policy, v_table);
    execute format(
      'create policy %I on public.%I for all to anon, authenticated using (false) with check (false)',
      v_policy, v_table
    );
    execute format(
      'comment on policy %I on public.%I is %L',
      v_policy, v_table,
      'Explicitly deny browser anon/authenticated access; all application data/actions are mediated by the trusted FastAPI service.'
    );
  end loop;
end
$$;
