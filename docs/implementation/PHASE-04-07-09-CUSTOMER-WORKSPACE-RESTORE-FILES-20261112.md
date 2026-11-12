# Customer OpenManus Workspace Restore & Files Integration

Date: 2026-11-12  
Repository: fadliansyah36/More-AI-Portal-Indihome  
Branch: main

## Scope

Continue direct-main implementation of the existing MoreAI Customer frontend against the canonical FastAPI, OpenManus Runtime/Worker and Supabase architecture. Existing UI shell is retained; no OpenManus web frontend is introduced.

## Implemented in this increment

### 1. Workspace version restore in OpenManus Runtime

- Added `workspace_restore_version` to the canonical tool catalog.
- Registered the handler in `DurableOpenManusRuntime` when the persistent workspace adapter is available.
- Passed the run's workspace context through the policy-enforced registry to the handler.
- Added restore behavior to `SupabaseWorkspaceTool`:
  - Validates the workspace-relative path and requested older version.
  - Resolves immutable historical metadata from Supabase.
  - Reads source bytes from private Storage.
  - Verifies byte length and SHA-256 before use.
  - Reserves a new write through the existing worker/run lease-fenced CAS RPC.
  - Uploads restored bytes to the newly reserved object path.
  - Commits as a new version; never overwrites the historical object.

### 2. Approval and security contract alignment

- Added `workspace_restore_version` to the high-risk default-deny approval policy.
- Added the tool key to the Customer approval request schema.
- Added forward-only migration `20261112120000_moreai_workspace_restore_approval_key.sql` to extend both the approval table constraint and `moreai_request_tool_approval` allowlist.
- The tool cannot run unless its run-scoped approval is approved and atomically consumed by the existing worker approval gate.

### 3. Customer workspace file API and UI

- Added a Customer API endpoint for signed download of current or historical workspace file versions.
- Requires active workspace owner/member authorization and a private Storage bucket.
- Signed URLs expire after 60 seconds.
- Workspace file and version queries are scoped by authorized workspace membership, supporting files shared by other members in the same workspace.
- Added typed workspace API methods to `lib/api/client.ts`.
- Existing `FilesView` now lists accessible workspace files and requests short-lived download links. Existing artifact library remains unchanged.

## Source commits in this continuation

- `23b6095` — signed workspace file download endpoint.
- `21f57ea` — workspace membership-scoped file listing and history.
- `1fa07fd` — typed Customer workspace API client.
- `c88597f` — connect existing Files view to workspace file listing/download.
- `795ceb2` — workspace restore tool contract.
- `dd863b5` — restore historical bytes as a new CAS version.
- `6366a8f` — register restore in durable runtime.
- `326f503` — pass workspace context into restore handler.
- `b4dea33` — require explicit approval for restore.
- `85b26f8` — allow Customer approval requests for restore tool key.
- `e254455`, `66ad9af` — forward-only database approval allowlist migration and correction.
- `0c05763` — honor configured workspace Storage bucket.
- `d4490ae` — update phase tracker.

## Verification boundary

No tests, lint, typecheck, build, browser checks, runtime calls, database migration application, staging or deployment were run, as explicitly instructed. GitHub source reads confirmed the latest files and the main branch head, but this is not runtime acceptance. The new migration is committed but not applied. The Storage bucket must exist and be private before signed downloads or worker workspace operations can function.

## Remaining work

- Full workspace CRUD, safe delete semantics, and complete restore UX/version selection.
- OpenManus upstream Flow/server/session/stream behavioral parity and source-to-target capability-map closure.
- Browser supervisor, DNS/egress enforcement, redirect checks and controlled downloads.
- Sandbox lifecycle and approval gates.
- Phase 07 worker approval continuation, retry, timeout, cancellation, lease recovery and outbox replay acceptance.
- Phase 08 full provider adapters/fallback, agent/tool/flow coverage, memory/RAG and accounting.
- Phase 06 complete FastAPI/OpenAPI contracts and authorization coverage.
- Phase 09 remaining Customer screens: profile settings, Wi-Fi/gateway device inventory, Captive Portal, voucher/access code, wallet/top-up/ledger, quota/entitlements, analytics, notifications, EduTech and all remaining workflows.

No phase is declared complete. Phase 10/11 remain blocked until the owner authorizes real verification and release work.
