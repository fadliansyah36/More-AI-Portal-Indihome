# Customer OpenManus Workspace Lifecycle Increment — 2026-11-12

## Implemented

- Added `POST /api/v1/customer/workspaces/{workspace_id}/archive`.
- Only workspace owner can archive; membership access is checked before mutation.
- Archive is soft, not destructive. Immutable file versions and audit history remain preserved.
- Archive is rejected with HTTP 409 when the workspace has queued, running, or waiting-approval agent runs. This prevents active execution from being orphaned.
- Added typed `customerWorkspaceApi.archive(workspaceId)` in the existing frontend API client.
- No Customer UI component or visual behavior was changed.

## Commits

- API: `70101b310847040f6af9be75f2846bd2a55b4cec`
- API client: `e2af2140438ab7c20aa2848e3c0107f33b8feee8`
- Tracker: `7a05780f739432074be825c445b6b50aa0fb5687`

## Boundaries

This is a concrete Phase 04 increment, not completion of full workspace lifecycle or full OpenManus integration. Workspace member management, file CRUD/rename/delete, complete server/session parity, all Flow/agent/tool parity, full RAG, and runtime acceptance remain open.

No tests, lint, typecheck, build, browser E2E, staging, or deployment were run. The existing restriction against staging/runtime tests remains in effect.

## Next

Continue Phase 04 with durable server/session compatibility and full workspace file lifecycle. Then proceed Phase 07 → Phase 08 → Phase 06 → Phase 09. Do not start gateway network integration until the OpenManus Customer integration gates are accepted.
