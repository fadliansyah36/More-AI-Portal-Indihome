
insert into public.roles(key,scope,description,system_role) values
('super_admin','platform','Full platform governance',true),
('platform_admin','platform','Platform operations excluding restricted finance/security controls',true),
('finance_admin','platform','Finance, pricing, credits and reconciliation',true),
('support_admin','platform','Limited support operations',true),
('security_admin','platform','Security review and incident response',true),
('partner_manager','platform','Partner onboarding and governance',true),
('read_only_analyst','platform','Read-only platform reporting',true),
('workspace_owner','workspace','Workspace owner',true),
('workspace_admin','workspace','Workspace administrator',true),
('workspace_member','workspace','Workspace member',true),
('partner_owner','partner','Partner organization owner',true),
('partner_admin','partner','Partner organization administrator',true),
('location_manager','location','Selected location manager',true),
('partner_staff','location','Basic venue and session support',true),
('partner_analyst','partner','Read-only partner analytics',true)
on conflict(key) do nothing;
insert into public.permissions(key,description) values
('platform.overview.read','Read platform overview'),
('platform.users.read','Read user directory'),
('platform.users.manage','Manage user accounts'),
('platform.roles.read','Read roles and permissions'),
('platform.roles.assign','Assign scoped roles'),
('platform.audit.read','Read administrative audit'),
('platform.security.read','Read security events'),
('platform.security.manage','Manage security policies'),
('platform.finance.read','Read finance and reconciliation'),
('platform.finance.manage','Manage finance and credit adjustments'),
('platform.models.read','Read model registry'),
('platform.models.manage','Manage model registry and routing'),
('partner.organization.read','Read partner organization'),
('partner.organization.manage','Manage partner organization'),
('partner.members.read','Read partner members'),
('partner.members.manage','Manage partner members'),
('partner.locations.read','Read assigned locations'),
('partner.locations.manage','Manage assigned locations'),
('partner.networks.read','Read assigned networks'),
('partner.networks.manage','Manage assigned networks'),
('partner.campaigns.read','Read partner campaigns'),
('partner.campaigns.manage','Manage partner campaigns'),
('partner.analytics.read','Read partner analytics'),
('network.verification.read','Read verification settings and attempts'),
('network.verification.manage','Manage verification configuration'),
('network.sessions.read','Read authorized network sessions'),
('network.sessions.revoke','Revoke authorized network sessions'),
('workspace.read','Read workspace'),
('workspace.manage','Manage workspace'),
('agent.run.create','Create agent runs'),
('agent.run.read','Read own agent runs'),
('agent.run.cancel','Cancel own agent runs'),
('wallet.read','Read wallet summary'),
('entitlement.read','Read own entitlements')
on conflict(key) do nothing;
with grants(role_key,permission_key) as (
 values
 ('super_admin','platform.overview.read'),('super_admin','platform.users.read'),('super_admin','platform.users.manage'),('super_admin','platform.roles.read'),('super_admin','platform.roles.assign'),('super_admin','platform.audit.read'),('super_admin','platform.security.read'),('super_admin','platform.security.manage'),('super_admin','platform.finance.read'),('super_admin','platform.finance.manage'),('super_admin','platform.models.read'),('super_admin','platform.models.manage'),
 ('platform_admin','platform.overview.read'),('platform_admin','platform.users.read'),('platform_admin','platform.roles.read'),('platform_admin','platform.audit.read'),('platform_admin','platform.models.read'),('platform_admin','partner.organization.read'),('platform_admin','partner.organization.manage'),
 ('finance_admin','platform.overview.read'),('finance_admin','platform.finance.read'),('finance_admin','platform.finance.manage'),
 ('support_admin','platform.overview.read'),('support_admin','platform.users.read'),('support_admin','platform.audit.read'),
 ('security_admin','platform.overview.read'),('security_admin','platform.security.read'),('security_admin','platform.security.manage'),('security_admin','platform.audit.read'),
 ('partner_manager','platform.overview.read'),('partner_manager','partner.organization.read'),('partner_manager','partner.organization.manage'),('partner_manager','partner.members.read'),('partner_manager','partner.members.manage'),
 ('read_only_analyst','platform.overview.read'),('read_only_analyst','platform.audit.read'),('read_only_analyst','platform.users.read'),
 ('workspace_owner','workspace.read'),('workspace_owner','workspace.manage'),('workspace_owner','agent.run.create'),('workspace_owner','agent.run.read'),('workspace_owner','agent.run.cancel'),('workspace_owner','wallet.read'),('workspace_owner','entitlement.read'),
 ('workspace_admin','workspace.read'),('workspace_admin','agent.run.create'),('workspace_admin','agent.run.read'),('workspace_admin','agent.run.cancel'),
 ('workspace_member','workspace.read'),('workspace_member','agent.run.create'),('workspace_member','agent.run.read'),('workspace_member','agent.run.cancel'),('workspace_member','wallet.read'),('workspace_member','entitlement.read'),
 ('partner_owner','partner.organization.read'),('partner_owner','partner.organization.manage'),('partner_owner','partner.members.read'),('partner_owner','partner.members.manage'),('partner_owner','partner.locations.read'),('partner_owner','partner.locations.manage'),('partner_owner','partner.networks.read'),('partner_owner','partner.networks.manage'),('partner_owner','partner.campaigns.read'),('partner_owner','partner.campaigns.manage'),('partner_owner','partner.analytics.read'),('partner_owner','network.sessions.read'),
 ('partner_admin','partner.organization.read'),('partner_admin','partner.members.read'),('partner_admin','partner.members.manage'),('partner_admin','partner.locations.read'),('partner_admin','partner.locations.manage'),('partner_admin','partner.networks.read'),('partner_admin','partner.networks.manage'),('partner_admin','partner.campaigns.read'),('partner_admin','partner.campaigns.manage'),('partner_admin','partner.analytics.read'),
 ('location_manager','partner.locations.read'),('location_manager','partner.networks.read'),('location_manager','partner.networks.manage'),('location_manager','partner.campaigns.read'),('location_manager','partner.campaigns.manage'),('location_manager','network.sessions.read'),('location_manager','network.sessions.revoke'),
 ('partner_staff','partner.locations.read'),('partner_staff','partner.networks.read'),('partner_staff','network.sessions.read'),
 ('partner_analyst','partner.organization.read'),('partner_analyst','partner.locations.read'),('partner_analyst','partner.analytics.read')
)
insert into public.role_permissions(role_id,permission_id)
select r.id,p.id from grants g join public.roles r on r.key=g.role_key join public.permissions p on p.key=g.permission_key
on conflict do nothing;
-- Audit and event history are append-only from the application service role.
revoke update, delete, truncate on public.admin_audit_logs, public.security_events,
 public.network_session_events, public.network_verification_evidence from service_role;
grant select, insert on public.admin_audit_logs, public.security_events,
 public.network_session_events, public.network_verification_evidence to service_role;
