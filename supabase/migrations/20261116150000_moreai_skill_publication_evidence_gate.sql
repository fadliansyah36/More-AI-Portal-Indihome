-- Harden skill publication against incomplete dependency inventories and unresolved license evidence.
create or replace function public.moreai_review_skill_package(
  p_skill_id uuid,
  p_actor_user_id uuid,
  p_license_status text,
  p_publication_status text,
  p_review_note text
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_package public.moreai_skill_packages%rowtype;
  v_report jsonb;
  v_inventory jsonb;
  v_registry jsonb;
  v_findings jsonb;
begin
  if p_skill_id is null or p_actor_user_id is null
     or p_license_status not in ('approved','rejected')
     or p_publication_status not in ('private','published','deprecated')
     or length(btrim(coalesce(p_review_note,''))) < 3 then
    raise exception 'skill_package_review_payload_invalid' using errcode='22023';
  end if;

  select * into v_package
  from public.moreai_skill_packages
  where id=p_skill_id
  for update;

  if not found then
    raise exception 'skill_not_found' using errcode='P0002';
  end if;

  v_report := coalesce(v_package.validation_report,'{}'::jsonb);
  v_inventory := coalesce(v_report->'source_inventory','{}'::jsonb);
  v_registry := coalesce(v_inventory->'registry_resolution','{}'::jsonb);
  v_findings := coalesce(v_report->'findings','[]'::jsonb);

  if jsonb_typeof(v_findings) <> 'array' then
    raise exception 'skill_validation_findings_must_be_an_array' using errcode='23514';
  end if;
  if jsonb_array_length(v_findings) <> 0 then
    raise exception 'skill_validation_findings_must_be_resolved' using errcode='23514';
  end if;
  if p_license_status='approved' and jsonb_typeof(v_inventory->'license_files') <> 'array' then
    raise exception 'skill_license_file_evidence_missing' using errcode='23514';
  end if;
  if p_license_status='approved' and jsonb_array_length(v_inventory->'license_files') = 0 then
    raise exception 'skill_license_file_evidence_missing' using errcode='23514';
  end if;

  if p_license_status='approved' and (
    coalesce(v_package.license_evidence,'')=''
    or v_package.validation_status<>'validated'
    or coalesce((v_inventory->>'unresolved_dependency_count')::integer, -1) <> 0
    or coalesce((v_registry->>'unresolved_count')::integer, -1) <> 0
    or coalesce((v_registry->>'registry_metadata_resolved_count')::integer, -1)
       <> coalesce((v_registry->>'exact_version_count')::integer, -2)
  ) then
    raise exception 'skill_requires_complete_dependency_and_license_evidence' using errcode='23514';
  end if;

  if p_publication_status='published' and (
    p_license_status<>'approved'
    or v_package.manifest='{}'::jsonb
    or v_package.validation_status<>'validated'
    or jsonb_typeof(v_inventory->'sbom') <> 'object'
    or jsonb_typeof(v_inventory->'dependencies') <> 'array'
    or coalesce((v_inventory->>'unresolved_dependency_count')::integer, -1) <> 0
    or coalesce((v_registry->>'unresolved_count')::integer, -1) <> 0
  ) then
    raise exception 'skill_requires_complete_validation_and_approved_license_before_publication' using errcode='23514';
  end if;

  update public.moreai_skill_packages
  set
    license_status=p_license_status,
    publication_status=p_publication_status,
    validation_report=jsonb_set(
      coalesce(validation_report,'{}'::jsonb),
      '{review}',
      jsonb_build_object(
        'reviewer_user_id',p_actor_user_id,
        'review_note',left(p_review_note,2000),
        'reviewed_at',now(),
        'decision',p_license_status,
        'publication_status',p_publication_status
      ),
      true
    ),
    updated_at=now()
  where id=p_skill_id
  returning * into v_package;

  insert into public.moreai_skill_registry_audit(
    skill_package_id,actor_user_id,owner_user_id,event_type,decision,event_detail
  ) values (
    p_skill_id,p_actor_user_id,v_package.owner_user_id,
    case when p_license_status='approved' then 'license_reviewed' else 'publication_reviewed' end,
    p_license_status,
    jsonb_build_object(
      'publication_status',p_publication_status,
      'review_note',left(p_review_note,2000),
      'validation_status',v_package.validation_status,
      'unresolved_dependency_count',v_inventory->>'unresolved_dependency_count',
      'registry_unresolved_count',v_registry->>'unresolved_count'
    )
  );

  return jsonb_build_object(
    'id',v_package.id,
    'license_status',v_package.license_status,
    'publication_status',v_package.publication_status,
    'validation_status',v_package.validation_status
  );
end;
$function$;

revoke all on function public.moreai_review_skill_package(uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.moreai_review_skill_package(uuid,uuid,text,text,text) to service_role;
