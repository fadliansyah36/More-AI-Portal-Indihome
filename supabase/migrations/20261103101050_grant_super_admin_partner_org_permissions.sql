insert into public.role_permissions(role_id, permission_id)
select r.id, p.id
from public.roles r
cross join public.permissions p
where r.key = 'super_admin'
  and p.key in ('partner.organization.read', 'partner.organization.manage')
on conflict do nothing;