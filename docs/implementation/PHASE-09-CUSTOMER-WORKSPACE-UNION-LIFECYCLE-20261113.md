# Phase 09 — Customer Workspace Union Pagination & File Lifecycle

Date: 2026-11-13  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Supabase project: `uunfgimtokhucegqbpce`  
Status: incremental implementation; Phase 09 remains IN PROGRESS.

## Scope delivered

### 1. Database-side workspace union pagination

- Added `public.moreai_customer_workspaces_page(p_user_id, p_limit, p_cursor_updated_at, p_cursor_id)`.
- The database unions active workspaces owned by the Customer and active workspace memberships, deduplicates workspace IDs, then applies a stable descending `(updated_at, id)` keyset cursor and bounded `limit + 1`.
- FastAPI no longer fetches separate owner/member collections and merges them behind a 1,000-row fan-in ceiling.
- Added partial indexes for active workspace owner ordering and active membership lookup.
- The RPC is `SECURITY INVOKER`, has an empty search path, validates the user/cursor pair, and is executable only by `service_role`. FastAPI supplies the authenticated Customer ID.

Supabase migrations applied:
- `moreai_customer_workspace_union_pagination`
- `moreai_customer_workspace_pagination_indexes`

### 2. Customer workspace file lifecycle

- Added owner/member-authorized FastAPI actions for soft delete and restore, both fenced by the current expected version.
- Soft delete preserves the last committed object in `agent_workspace_file_versions` before marking the current file deleted. Repeated delete is idempotent for the same version.
- Deleted files can be included in the paged workspace file list. Exact path lookup now resolves the authoritative current version before a CAS upload; an upload to a deleted path is blocked until explicit restore.
- Restore verifies the source object's private Storage path, recorded SHA-256 and byte size, copies the bytes to the next version-addressed Storage path, then commits the new metadata version in a transaction. This prevents a restored version number from pointing at an older version's object path.
- The Files screen now surfaces deleted state, disables ordinary download for deleted current files, and exposes explicit Restore/Delete actions. Version history and explicit version download remain available, including the latest archived version after soft delete.
- Explicit download of a deleted file requires selecting its archived version; the normal current-file download remains unavailable until restore.

Supabase migrations applied:
- `moreai_customer_workspace_file_lifecycle`
- `moreai_customer_workspace_restore_immutable_version`
- `moreai_customer_workspace_delete_version_archive`
- `moreai_customer_workspace_restore_empty_file`

### 3. OpenManus Worker parity

- Updated the lease-fenced `moreai_workspace_restore_deleted_file` RPC to require the active Agent Run lease and verify the next immutable Storage path, bucket privacy, SHA-256, size and workspace ownership.
- Worker `str_replace_editor(operation="restore_deleted")` now reads and verifies the prior object, writes a new immutable version object, and commits that object through the lease-fenced RPC.
- The previous six-argument worker restore RPC overload is no longer executable by `service_role`.

Supabase migration applied:
- `moreai_worker_workspace_restore_immutable_version`

### 4. Learning progress collection

- Removed the 1,000-row learning progress cap. The endpoint now uses a stable `(completed_at, id)` keyset cursor and returns an exact total count separately from the current page count.
- Added matching indexes for owner-scoped progress ordering with and without module filtering.
- The EduTech overview reads `total_count` rather than treating the first page length as the total saved progress count. Typed `progressPage` is available for incremental consumers.
- Progress writes now return an explicit `503 learning_catalog_unavailable` until the official EduTech catalog supplies verified module/lesson identifiers; arbitrary caller-provided identifiers cannot be persisted.

Supabase migration applied:
- `moreai_customer_learning_progress_pagination`

### 4. Contract and screen reconciliation

- Conversation session detail now returns `available_at`, `heartbeat_at` and `cancel_requested_at` in addition to the existing run lifecycle fields.
- Conversation message attachments now use a typed nested response model rather than unbounded dictionaries.
- Workspace file list supports exact path lookup and optional deleted rows; the frontend has typed lifecycle results and resolves current versions from the server before upload.
- The Customer profile identity contract matches the normalized `current_user` projection (`id`, `email`, `display_name`); profile routes intentionally remain authenticated identity routes rather than Customer-only business routes.
- Customer Knowledge Library list uses keyset pagination and owner-scoped document actions. Knowledge chunk detail remains capped at 500 rows and is not yet a paged UI surface.
- Workspace member and run endpoints already have typed keyset-paged response/client contracts and owner/member checks. The current Customer UI has no dedicated member/run management screen; no fabricated navigation or actions were added for screens that do not exist.
- A lexical review of the main Customer views found no explicit mock/dummy/sample/demo-data markers in Home, Agent Studio, Tools Catalog, Analytics, Create, Analyse, Code, Chat, Research, Tasks, Workflow, Results, Files, Knowledge Library, EduTech, Profile, Notifications, Devices, Wi-Fi Session, Benefit Credit, Speedtest and device-control views. Create/Code starter material remains clearly presented as editor examples, not persisted business data. This source scan is not runtime verification.

## Authorization and data boundary

- Customer business routes continue to require `customer_principal`; workspace operations re-check active owner/member access before invoking service-role RPCs.
- Profile identity GET/PATCH uses `current_user` because it is an authenticated account identity resource shared across roles, and profile mutation remains scoped by the caller's Supabase JWT/RLS.
- Worker restore remains bound to a running Agent Run, matching worker ID, unexpired lease, run user and workspace.
- Storage buckets remain private. Browser code receives only short-lived signed downloads from FastAPI.
- No service-role key, Storage credential or raw provider credential is exposed to the browser.

## Supabase static advisor notes

The post-migration Supabase advisor reported:
- Security: one existing warning — leaked-password protection is disabled. No new function/RPC exposure warning was returned.
- Performance: 61 unindexed foreign-key findings across the project and 49 unused-index findings. The newly added workspace and learning pagination indexes appear in the unused-index snapshot because they were created moments before the advisor read; usage should be assessed after normal workload, not removed on this snapshot.
- These advisor results are static schema observations, not runtime tests.

## Verification boundary

Per instruction, no test suite, lint, typecheck, build, browser run, API probe, worker execution, staging deployment or production application deployment was run. Supabase DDL migrations were applied directly to the canonical project because the Customer endpoints now depend on the new database RPCs. The advisor is a static schema/security review only. The changes have not been accepted through real Customer → FastAPI → Worker → Storage end-to-end use.

## Remaining Phase 09 work

1. Continue route-by-route response-schema and authorization audit, including Knowledge chunk pagination, learning-progress collection semantics, nested session/event payload projections, and all remaining Customer actions.
2. Add a dedicated Customer workspace member/run navigation surface only if the approved UI/UX reference and PRD require it; existing API/client contracts are paged, but no current screen exposes management.
3. Continue auditing all screen states and ensure local editor examples are never mistaken for saved backend data.
4. Continue provider-independent integration where contracts exist. Gateway/OTP, EduTech catalog/video, media generation, payment settlement and support remain fail-closed until official provider contracts and credentials are supplied.
5. Phase 09 remains IN PROGRESS. Phase 10 and Phase 11 must not be marked complete or started as accepted integration work without authorization for their respective verification gates.

- Learning progress keyset/count migration: `supabase/migrations/20261113240000_moreai_customer_learning_progress_pagination.sql` (applied to the canonical Supabase project).
- Knowledge chunk count migration: `supabase/migrations/20261113250000_moreai_customer_knowledge_chunk_count.sql` (applied to the canonical Supabase project).

## Main repository evidence

- Workspace union pagination migration file: `supabase/migrations/20261113160000_moreai_customer_workspace_union_pagination.sql` (blob `5a4f337687dfbc24832c1d395aa410f03c59615e`); Supabase apply succeeded.
- Workspace pagination index migration file: `supabase/migrations/20261113180000_moreai_customer_workspace_pagination_indexes.sql` (blob `15c5bd0bc6d475f2cf1991ebcc61ea771e3dd257`); Supabase apply succeeded.
- Workspace file lifecycle migration file: `supabase/migrations/20261113170000_moreai_customer_workspace_file_lifecycle.sql` (blob `0278942b405b9f6ad3b9a230ca08521d3be4ee37`); Supabase apply succeeded.
- Customer immutable restore migration: `20261113190000_moreai_customer_workspace_restore_immutable_version.sql` (blob `9740a410506331916b5527c727765b661b78f625`); delete archive migration: `20261113200000_moreai_customer_workspace_delete_version_archive.sql` (blob `498794d75e0f6de1a0d75ca0d40524035c7cbffb`); empty-file compatibility migration: `20261113230000_moreai_customer_workspace_restore_empty_file.sql` (blob `707926e48c9cf59d3f088c8f10970da085ffac37`). Supabase applies succeeded.
- Worker lease-fenced restore migration: `20261113220000_moreai_worker_workspace_restore_immutable_version.sql` (blob `cbcaef705f423e985f39e2a66d58cd9b5cfdefe6`); Supabase apply succeeded.
- API/client/UI/worker source changes are committed on `main`; no CI or runtime validation was invoked in this continuation. Exact file revisions are visible in the repository history.
