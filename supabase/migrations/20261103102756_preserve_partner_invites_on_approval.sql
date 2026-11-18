create or replace function public.moreai_admin_review_partner(
 p_actor_user_id uuid,p_partner_id uuid,p_decision text,p_reason text default null,p_correlation_id text default null
) returns jsonb language plpgsql security definer set search_path=public,pg_temp as $$
declare
 v_partner public.partner_organizations%rowtype;
 v_next_status text;
 v_correlation text:=coalesce(nullif(p_correlation_id,''),gen_random_uuid()::text);
begin
 if p_actor_user_id is null or p_partner_id is null or p_decision is null or p_decision not in ('approve','reject','suspend') or length(coalesce(p_reason,''))>500 then
  raise exception using errcode='22023',message='PARTNER_REVIEW_INVALID';
 end if;
 if not exists(select 1 from public.user_role_assignments ura join public.roles r on r.id=ura.role_id join public.role_permissions rp on rp.role_id=r.id join public.permissions p on p.id=rp.permission_id
  where ura.user_id=p_actor_user_id and ura.scope_type='platform' and ura.scope_id is null and (ura.expires_at is null or ura.expires_at>now()) and r.scope='platform' and p.key='partner.organization.manage') then
  raise exception using errcode='42501',message='ADMIN_PERMISSION_DENIED';
 end if;
 select * into v_partner from public.partner_organizations where id=p_partner_id for update;
 if not found then raise exception using errcode='P0002',message='PARTNER_NOT_FOUND'; end if;
 v_next_status:=case p_decision when 'approve' then 'active' when 'reject' then 'rejected' when 'suspend' then 'suspended' end;
 if v_partner.status=v_next_status then return jsonb_build_object('partner',to_jsonb(v_partner),'replayed',true); end if;
 if (p_decision in ('approve','reject') and v_partner.status<>'pending') or (p_decision='suspend' and v_partner.status<>'active') then
  raise exception using errcode='55000',message='PARTNER_STATUS_TRANSITION_INVALID';
 end if;
 update public.partner_organizations set status=v_next_status,updated_at=now() where id=p_partner_id returning * into v_partner;
 if p_decision='approve' then
  update public.partner_members set status='active' where partner_id=p_partner_id and role_key='partner_owner' and status in ('active','invited');
 else
  update public.partner_members set status='suspended' where partner_id=p_partner_id and status='active';
 end if;
 insert into public.admin_audit_logs(actor_user_id,action,resource_type,resource_id,scope_type,scope_id,correlation_id,outcome,metadata)
 values(p_actor_user_id,'partner.application.'||p_decision,'partner_organization',p_partner_id::text,'partner',p_partner_id,v_correlation,'success',
  jsonb_build_object('previous_status',case when p_decision in ('approve','reject') then 'pending' else 'active' end,'new_status',v_next_status,'reason',p_reason));
 return jsonb_build_object('partner',to_jsonb(v_partner),'replayed',false);
end; $$;