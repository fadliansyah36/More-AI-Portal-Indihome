-- Index the two branches of the Customer workspace union cursor.
create index if not exists workspaces_customer_owner_active_updated_idx
  on public.workspaces (owner_user_id, updated_at desc, id desc)
  where status = 'active';

create index if not exists workspace_members_customer_active_user_workspace_idx
  on public.workspace_members (user_id, workspace_id)
  where status = 'active';
