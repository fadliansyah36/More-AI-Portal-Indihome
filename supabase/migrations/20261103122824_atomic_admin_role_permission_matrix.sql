create or replace function public.moreai_admin_set_role_permission(
 p_actor_user_id uuid,p_role_key text,p_permission_key text,p_enabled boolean,p_correlation_id text default null
) returns jsonb language plpgsql security invoker set search_path=public,pg_temp as $$
declare v_role public.roles%rowtype; v_permission public.permissions%rowtype; v_correlation text:=coalesce(nullif(p_correlation_id,''),gen_random_uuid()::text);
begin
 if p_actor_user_id is null or coalesce(p_role_key,'')='' or coalesce(p_permission_key,'')='' or p_enabled is null then
  raise exception using errcode='22023',message='ROLE_PERMISSION_INVALID';
 end if;
 if not exists(
  select 1 from public.user_role_assignments ura
  join public.roles r on r.id=ura.role_id
  join public.role_permissions rp on rp.role_id=r.id
  join public.permissions p on p.id=rp.permission_id
  where ura.user_id=p_actor_user_id and ura.scope_type='platform' and ura.scope_id is null
   and (ura.expires_at is null or ura.expires_at>now())
   and r.scope='platform' and r.key='super_admin'
   and p.key in ('platform.roles.assign','platform.security.manage')
  group by ura.id having count(distinct p.key)=2
 ) then raise exception using errcode='42501',message='ADMIN_PERMISSION_DENIED'; end if;
 select * into v_role from public.roles where key=p_role_key and scope='platform' for update;
 if not found then raise exception using errcode='P0002',message='PLATFORM_ROLE_NOT_FOUND'; end if;
 if v_role.key='super_admin' then raise exception using errcode='55000',message='SUPER_ADMIN_PERMISSION_MATRIX_IMMUTABLE'; end if;
 if p_enabled and p_permission_key in ('platform.roles.assign','platform.security.manage') then
  raise exception using errcode='42501',message='PRIVILEGED_PERMISSION_CANNOT_BE_DELEGATED';
 end if;
 select * into v_permission from public.permissions where key=p_permission_key;
 if not found then raise exception using errcode='P0002',message='PERMISSION_NOT_FOUND'; end if;
 if p_enabled then
  insert into public.role_permissions(role_id,permission_id) values(v_role.id,v_permission.id)
  on conflict(role_id,permission_id) do nothing;
 else
  delete from public.role_permissions where role_id=v_role.id and permission_id=v_permission.id;
 end if;
 insert into public.admin_audit_logs(actor_user_id,action,resource_type,resource_id,scope_type,correlation_id,outcome,metadata)
 values(p_actor_user_id,case when p_enabled then 'rbac.permission.grant' else 'rbac.permission.revoke' end,
  'role_permission',v_role.id::text,'platform',v_correlation,'success',
  jsonb_build_object('role_key',v_role.key,'permission_key',v_permission.key,'enabled',p_enabled));
 return jsonb_build_object('role_key',v_role.key,'permission_key',v_permission.key,'enabled',p_enabled);
end; $$;
revoke all on function public.moreai_admin_set_role_permission(uuid,text,text,boolean,text) from public,anon,authenticated;
grant execute on function public.moreai_admin_set_role_permission(uuid,text,text,boolean,text) to service_role;