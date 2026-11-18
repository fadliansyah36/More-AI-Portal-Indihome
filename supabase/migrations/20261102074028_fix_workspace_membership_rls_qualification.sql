drop policy if exists workspaces_read_member on public.workspaces;
create policy workspaces_read_member on public.workspaces
for select to authenticated
using (
  exists (
    select 1 from public.workspace_members m
    where m.workspace_id = workspaces.id
      and m.user_id = (select auth.uid())
      and m.status = 'active'
  )
  or owner_user_id = (select auth.uid())
);