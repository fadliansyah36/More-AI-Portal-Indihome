-- Atomic Skill Registry source ingestion and permission review audit.
create table if not exists public.moreai_skill_registry_audit (
  id uuid primary key default gen_random_uuid(),
  skill_package_id uuid not null references public.moreai_skill_packages(id) on delete restrict,
  skill_install_id uuid references public.moreai_skill_installs(id) on delete restrict,
  actor_user_id uuid references auth.users(id) on delete set null,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  event_type text not null check (event_type in ('source_ingested','permission_reviewed','license_reviewed','publication_reviewed')),
  decision text,
  permission_snapshot jsonb not null default '[]'::jsonb check (jsonb_typeof(permission_snapshot)='array'),
  event_detail jsonb not null default '{}'::jsonb check (jsonb_typeof(event_detail)='object'),
  created_at timestamptz not null default now()
);
create index if not exists moreai_skill_registry_audit_package_idx
  on public.moreai_skill_registry_audit(skill_package_id,created_at desc);
alter table public.moreai_skill_registry_audit enable row level security;
revoke all on public.moreai_skill_registry_audit from public,anon,authenticated;
grant select,insert on public.moreai_skill_registry_audit to service_role;
drop policy if exists moreai_skill_registry_audit_server_only on public.moreai_skill_registry_audit;
create policy moreai_skill_registry_audit_server_only on public.moreai_skill_registry_audit
  for all to anon,authenticated using(false) with check(false);

create or replace function public.moreai_ingest_skill_source(
  p_skill_id uuid, p_owner_user_id uuid, p_files jsonb, p_validation_report jsonb
) returns jsonb
language plpgsql security definer set search_path=''
as $function$
declare
  v_package public.moreai_skill_packages%rowtype;
  v_count integer;
  v_bytes bigint;
begin
  if p_skill_id is null or p_owner_user_id is null
     or jsonb_typeof(p_files)<>'array' or jsonb_array_length(p_files)<1
     or jsonb_array_length(p_files)>40 or jsonb_typeof(p_validation_report)<>'object' then
    raise exception 'skill_source_ingestion_payload_invalid' using errcode='22023';
  end if;
  select * into v_package from public.moreai_skill_packages
   where id=p_skill_id and owner_user_id=p_owner_user_id for update;
  if not found then raise exception 'skill_not_found' using errcode='42501'; end if;
  if exists(select 1 from public.moreai_skill_source_files where skill_package_id=p_skill_id) then
    raise exception 'skill_source_already_ingested_immutable' using errcode='23505';
  end if;
  select count(*),coalesce(sum((x->>'byte_size')::bigint),0)
    into v_count,v_bytes from jsonb_array_elements(p_files) x;
  if v_count<>jsonb_array_length(p_files) or v_bytes>5242880 then
    raise exception 'skill_source_package_size_limit_exceeded' using errcode='22023';
  end if;
  if exists(
    select 1 from jsonb_array_elements(p_files) x
    where coalesce(x->>'relative_path','')='' or x->>'relative_path' ~ '(^/|(^|/)\.\.(/|$))'
       or coalesce(x->>'git_blob_sha','') !~ '^[0-9a-f]{40}$'
       or coalesce(x->>'content_sha256','') !~ '^[0-9a-f]{64}$'
       or coalesce((x->>'byte_size')::integer,-1)<0
       or (x->>'byte_size')::integer>524288
       or ((x->>'text_content') is null) = ((x->>'binary_content_base64') is null)
  ) then raise exception 'skill_source_file_record_invalid' using errcode='22023'; end if;
  if (select count(distinct x->>'relative_path') from jsonb_array_elements(p_files) x)<>v_count then
    raise exception 'skill_source_duplicate_path' using errcode='22023';
  end if;
  insert into public.moreai_skill_source_files(
    skill_package_id,owner_user_id,relative_path,git_blob_sha,content_sha256,
    media_type,byte_size,text_content,binary_content_base64
  )
  select p_skill_id,p_owner_user_id,x->>'relative_path',x->>'git_blob_sha',x->>'content_sha256',
    x->>'media_type',(x->>'byte_size')::integer,x->>'text_content',x->>'binary_content_base64'
  from jsonb_array_elements(p_files) x;
  update public.moreai_skill_packages set
    validation_status='review_required',validation_report=p_validation_report,updated_at=now()
  where id=p_skill_id and owner_user_id=p_owner_user_id;
  insert into public.moreai_skill_registry_audit(
    skill_package_id,owner_user_id,event_type,event_detail
  ) values(
    p_skill_id,p_owner_user_id,'source_ingested',
    jsonb_build_object('file_count',v_count,'total_bytes',v_bytes,'source_commit',v_package.source_commit)
  );
  return jsonb_build_object('skill_id',p_skill_id,'file_count',v_count,'total_bytes',v_bytes,'integrity','verified');
end;
$function$;
revoke all on function public.moreai_ingest_skill_source(uuid,uuid,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.moreai_ingest_skill_source(uuid,uuid,jsonb,jsonb) to service_role;

create or replace function public.moreai_review_skill_permissions(
  p_skill_id uuid,p_install_id uuid,p_actor_user_id uuid,p_decision text,
  p_granted_permissions text[],p_review_note text,p_execution_enabled boolean
) returns jsonb
language plpgsql security definer set search_path=''
as $function$
declare
  v_install public.moreai_skill_installs%rowtype;
  v_package public.moreai_skill_packages%rowtype;
  v_requested text[];
begin
  if p_decision not in ('approved','rejected') or p_granted_permissions is null
     or coalesce(cardinality(p_granted_permissions),0)>20 then
    raise exception 'skill_permission_review_payload_invalid' using errcode='22023';
  end if;
  select * into v_install from public.moreai_skill_installs
   where id=p_install_id and skill_package_id=p_skill_id for update;
  if not found then raise exception 'skill_install_not_found' using errcode='P0002'; end if;
  select * into v_package from public.moreai_skill_packages where id=p_skill_id for share;
  if not found then raise exception 'skill_not_found' using errcode='P0002'; end if;
  select coalesce(array_agg(value),'{}'::text[]) into v_requested
    from jsonb_array_elements_text(coalesce(v_install.permission_request,'[]'::jsonb)) as value;
  if p_decision='approved' and not (p_granted_permissions <@ v_requested) then
    raise exception 'granted_permissions_must_be_subset_of_requested' using errcode='22023';
  end if;
  update public.moreai_skill_installs set
    permission_status=p_decision,
    granted_permissions=case when p_decision='approved' then to_jsonb(p_granted_permissions) else '[]'::jsonb end,
    execution_enabled=(p_decision='approved' and p_execution_enabled
      and v_package.validation_status='validated' and v_package.license_status='approved'
      and v_package.publication_status='published'),
    updated_at=now()
  where id=p_install_id returning * into v_install;
  insert into public.moreai_skill_registry_audit(
    skill_package_id,skill_install_id,actor_user_id,owner_user_id,event_type,decision,
    permission_snapshot,event_detail
  ) values(
    p_skill_id,p_install_id,p_actor_user_id,v_install.owner_user_id,'permission_reviewed',
    p_decision,to_jsonb(v_install.granted_permissions),
    jsonb_build_object('review_note',left(coalesce(p_review_note,''),2000),
      'execution_enabled',v_install.execution_enabled,'requested_permissions',to_jsonb(v_requested))
  );
  return jsonb_build_object('install_id',v_install.id,'permission_status',v_install.permission_status,
    'granted_permissions',to_jsonb(v_install.granted_permissions),
    'execution_enabled',v_install.execution_enabled);
end;
$function$;
revoke all on function public.moreai_review_skill_permissions(uuid,uuid,uuid,text,text[],text,boolean) from public,anon,authenticated;
grant execute on function public.moreai_review_skill_permissions(uuid,uuid,uuid,text,text[],text,boolean) to service_role;
