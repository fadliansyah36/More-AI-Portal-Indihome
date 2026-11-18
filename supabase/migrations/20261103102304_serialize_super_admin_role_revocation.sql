create or replace function public.moreai_admin_revoke_platform_role(
 p_actor_user_id uuid,p_assignment_id uuid,p_reason text default null,p_correlation_id text default null
) returns jsonb language plpgsql security definer set search_path=public,pg_temp as $$
declare v_assignment public.user_role_assignments%rowtype; v_role public.roles%rowtype; v_super_admin_count integer; v_correlation text:=coalesce(nullif(p_correlation_id,''),gen_random_uuid()::text);
begin
 if p_actor_user_id is null or p_assignment_id is null or length(coalesce(p_reason,''))>500 then raise exception using errcode='22023',message='ROLE_REVOCATION_INVALID'; end if;
 if not exists(select 1 from public.user_role_assignments ura join public.roles r on r.id=ura.role_id join public.role_permissions rp on rp.role_id=r.id join public.permissions p on p.id=rp.permission_id
  where ura.user_id=p_actor_user_id and ura.scope_type='platform' and ura.scope_id is null and (ura.expires_at is null or ura.expires_at>now()) and r.scope='platform' and r.key='super_admin' and p.key='platform.roles.assign') then
  raise exception using errcode='42501',message='ADMIN_PERMISSION_DENIED'; end if;
 select * into v_assignment from public.user_role_assignments where id=p_assignment_id and scope_type='platform' and scope_id is null for update;
 if not found then raise exception using errcode='P0002',message='ROLE_ASSIGNMENT_NOT_FOUND'; end if;
 select * into v_role from public.roles where id=v_assignment.role_id;
 if v_role.key='super_admin' and (v_assignment.expires_at is null or v_assignment.expires_at>now()) then
  perform pg_advisory_xact_lock(hashtextextended('moreai:super_admin_revocation',0));
  select count(*) into v_super_admin_count from public.user_role_assignments ura join public.roles r on r.id=ura.role_id
   where r.key='super_admin' and ura.scope_type='platform' and ura.scope_id is null and (ura.expires_at is null or ura.expires_at>now());
  if v_super_admin_count<=1 then raise exception using errcode='55000',message='LAST_SUPER_ADMIN_CANNOT_BE_REVOKED'; end if;
 end if;
 delete from public.user_role_assignments where id=p_assignment_id;
 insert into public.admin_audit_logs(actor_user_id,action,resource_type,resource_id,scope_type,correlation_id,outcome,metadata)
 values(p_actor_user_id,'rbac.role.revoke','user_role_assignment',p_assignment_id::text,'platform',v_correlation,'success',jsonb_build_object('target_user_id',v_assignment.user_id,'role_key',v_role.key,'reason',p_reason));
 return jsonb_build_object('assignment_id',p_assignment_id,'revoked',true);
end; $$;