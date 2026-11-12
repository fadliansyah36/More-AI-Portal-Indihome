# Customer Workspace Integration — Direct Main Increment

Date: 2026-11-12  
Repository: fadliansyah36/More-AI-Portal-Indihome  
Branch: main

## Objective

Continue integration of the existing MoreAI Customer application with the canonical FastAPI, OpenManus runtime and Supabase persistence without replacing or redesigning the existing UI. Per product-owner instruction, this increment is source implementation only: no tests, runtime verification, staging, migration application or deployment.

## Implemented

### FastAPI Customer workspace routes

Added `apps/api/app/routers/workspaces.py` and registered it in `apps/api/app/main.py`.

- `GET /api/v1/customer/workspaces`: returns active workspaces owned by the authenticated Customer plus active workspace memberships.
- `POST /api/v1/customer/workspaces`: creates a workspace with the authenticated user as owner and a collision-resistant slug.
- `GET /api/v1/customer/workspaces/{workspace_id}/files`: lists workspace file metadata after active owner/member authorization.
- `GET /api/v1/customer/workspaces/{workspace_id}/files/{file_id}/versions`: lists immutable prior-version metadata and the current version.

Workspace authorization is checked server-side using the authenticated principal, active workspace status, owner identity or active membership. File listing is workspace-scoped after this check so members can see files shared within the workspace rather than only files created by themselves. The endpoints do not expose file bytes or raw signed Storage URLs.

### Supabase version metadata migration

Added `supabase/migrations/20261112100000_moreai_workspace_file_version_history.sql`.

- Adds `agent_workspace_file_versions` with workspace/user/path/version identity, Storage object path, SHA-256, size and commit timestamp.
- Enables RLS and denies direct anon/authenticated access; grants server-side service role access.
- Adds an archival trigger that snapshots the previous committed version metadata before the CAS file metadata row advances to a new version.
- Keeps object bytes in private Storage; version history is metadata, not a duplicate content store.

The migration is forward-only and additive. It has NOT been applied to the canonical Supabase project.

## Source commits

- `42d3cb1` — add immutable workspace file version history migration.
- `3f8d5d2` — add Customer workspace and file history endpoints.
- `f5f9ab3` — register workspace router in FastAPI.
- `ca88a91` — update phase tracker.
- `f51b8df` — honor workspace membership for shared file metadata/history.

## Not completed

This increment does not complete SWE workspace parity. Remaining work includes file content read/write/delete/restore orchestration, safe Storage copy/restore, workspace lifecycle mutation and full upstream OpenManus Flow/server/session parity.

The wider Customer integration remains incomplete: screen-by-screen binding for all Customer modules, Captive Portal gateway lifecycle, Wi-Fi device inventory, EduTech persistence/API, complete notification/profile settings actions, and full credit/entitlement journeys remain open. EduTech must not be backed by fabricated records; its persistence contract must be approved before implementing real CRUD.

Phase 07 still requires approval decision-to-worker continuation, retry/dead-letter policy, timeout/cancellation race handling, lease recovery and outbox replay completion. Phase 08 still requires full upstream provider/agent/tool/flow parity, durable RAG lifecycle and accounting reconciliation. Phase 06 still requires complete OpenAPI and authorization coverage.

## Verification and release boundary

As explicitly instructed:
- No unit/integration tests.
- No lint, typecheck or build.
- No live API or worker execution.
- No Supabase migration application or production data mutation.
- No staging, browser QA or deployment.

No runtime correctness, security acceptance, phase completion or production readiness is claimed. The new API and migration are committed source changes only.

## Next phase

Continue Phase 04 with workspace content operations and restore semantics, then close Phase 07 worker continuation/recovery, Phase 08 upstream runtime parity, Phase 06 API contract coverage and Phase 09 screen-to-API integration. Keep Phase 10/11 blocked until the owner authorizes verification and release activities.
