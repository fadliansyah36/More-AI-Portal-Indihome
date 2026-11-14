-- Aggregate curriculum progress in Postgres instead of fetching every lesson into FastAPI.
create or replace view public.learning_path_progress_summary
with (security_invoker = true)
as
select
  p.id as path_id,
  p.owner_user_id,
  count(l.id)::integer as lessons_total,
  count(pr.id)::integer as lessons_started,
  count(pr.id) filter (where pr.status='completed')::integer as lessons_completed,
  case
    when count(l.id)=0 then 0::numeric
    else round(coalesce(sum(pr.progress_percent),0) / count(l.id), 1)
  end as average_percent
from public.learning_paths p
left join public.learning_lessons l
  on l.path_id=p.id and l.owner_user_id=p.owner_user_id
left join public.learning_progress pr
  on pr.lesson_id=l.id and pr.user_id=p.owner_user_id
group by p.id,p.owner_user_id;

revoke all on public.learning_path_progress_summary from anon, authenticated;
grant select on public.learning_path_progress_summary to service_role;
