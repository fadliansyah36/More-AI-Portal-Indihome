create or replace function public.moreai_review_skill_package(
  p_skill_id uuid,p_actor_user_id uuid,p_license_status text,
  p_publication_status text,p_review_note text
) returns jsonb
language plpgsql security definer set search_path=''
as $function$
declare v_package public.moreai_skill_packages%rowtype;
begin
  if p_license_status not in ('approved','rejected')
     or p_publication_status not in ('private','published','deprecated')
     or length(btrim(coalesce(p_review_note,'')))<3 then
    raise exception 'skill_package_review_payload_invalid' using errcode='22023';
  end if;
  select * into v_package from public.moreai_skill_packages where id=p_skill_id for update;
  if not found then raise exception 'skill_not_found' using errcode='P0002'; end if;
  if p_license_status='approved' and (
    coalesce(v_package.license_evidence,'')='' or v_package.validation_status<>'validated'
  ) then raise exception 'skill_requires_validation_and_license_evidence' using errcode='23514'; end if;
  if p_publication_status='published' and (
    p_license_status<>'approved' or v_package.manifest='{}'::jsonb
  ) then raise exception 'license_approval_and_manifest_required_before_publication' using errcode='23514'; end if;
  update public.moreai_skill_packages set
    license_status=p_license_status,publication_status=p_publication_status,
    validation_report=jsonb_set(
      coalesce(validation_report,'{}'::jsonb),'{review}',
      jsonb_build_object('reviewer_user_id',p_actor_user_id,'review_note',left(p_review_note,2000),'reviewed_at',now()),true
    ),updated_at=now()
  where id=p_skill_id returning * into v_package;
  insert into public.moreai_skill_registry_audit(
    skill_package_id,actor_user_id,owner_user_id,event_type,decision,event_detail
  ) values(
    p_skill_id,p_actor_user_id,v_package.owner_user_id,
    case when p_license_status='approved' then 'license_reviewed' else 'publication_reviewed' end,
    p_license_status,jsonb_build_object('publication_status',p_publication_status,'review_note',left(p_review_note,2000))
  );
  return jsonb_build_object('id',v_package.id,'license_status',v_package.license_status,
    'publication_status',v_package.publication_status,'validation_status',v_package.validation_status);
end;
$function$;
revoke all on function public.moreai_review_skill_package(uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.moreai_review_skill_package(uuid,uuid,text,text,text) to service_role;
