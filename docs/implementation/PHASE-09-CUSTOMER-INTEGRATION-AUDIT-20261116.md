# Phase 09 — Customer dashboard integration audit (2026-11-16)

Target branch: `main`  
Audit mode: source inspection and read-only Supabase metadata only  
Latest source increment covered: `dd8241dab338d86cdb688ce63e51c0e94b11d435`

## Scope and boundaries

This continuation prioritizes the existing customer dashboard and its current integration seams. It does not replace the frontend shell or alter global CSS, Tailwind, design tokens, navigation, typography, or brand colors. FastAPI remains the browser-facing business API; browser-side Supabase access is limited to Auth. Supabase PostgreSQL remains canonical persistence. OpenManus is the single agent runtime; OpenFuse is the browser/workspace adapter.

No test, build, lint, type-check, browser, API runtime, staging, migration apply, or deployment was run, per product-owner instruction. Findings below are source-level audit evidence, not end-to-end proof.

## Customer route-to-service map

| Existing customer surface | Frontend integration seam | FastAPI service family | Persistence / worker path | Audit result |
|---|---|---|---|---|
| Chat | `components/views/chat-view.tsx`, `lib/api/client.ts` | `/api/v1/conversations`, `/api/v1/agent-runs`, tools, workspace/artifact APIs | conversations, messages, durable agent runs, run events, worker/outbox | Source integration exists; full per-control/error-state and stream authorization proof remains open |
| Research | `components/views/research-view.tsx` | Handoff to authenticated Chat submission and durable Agent Run; history/artifacts APIs | agent_runs, events, artifacts | Query action hands off to Chat; no fabricated research result is inserted |
| Create | `components/views/create-view.tsx` | `/api/v1/media/capabilities` and Chat durable-run handoff | worker capability heartbeat, agent run, artifact | UI handoff exists; media generation remains capability-gated |
| Analyse | `components/views/analyse-view.tsx`, `lib/api/knowledge.ts` | `/api/v1/customer/knowledge/documents` upload/list/detail/retry/reindex/archive/retrieval | knowledge_documents, knowledge_chunks, ingestion worker, pgvector | FastAPI knowledge path exists; ingestion/provider runtime remains unverified |
| Tasks | `components/views/tasks-view.tsx` | `/api/v1/customer/agent-runs`, run detail/steps/events/cancel/retry, artifacts/learning | durable agent_runs, steps, event outbox, worker, artifacts | Source integration exists; complete retry/cancel/idempotency behavior requires verification |
| Files | `components/views/files-view.tsx` | `/api/v1/customer/workspaces`, workspace files/versions, `/api/v1/customer/artifacts` | workspace metadata, artifact metadata, private Supabase Storage via FastAPI | Ownership filters and signed-download API are present; artifact bucket deny policy is pending |
| Memory | `components/views/personal-memory-settings.tsx` | `/api/v1/customer/memory`, consent, item create/update/delete, clear | moreai_customer_memory_preferences, moreai_customer_memories, episodic metadata in conversation_messages | Owner-scoped source path exists; clear is multi-step and non-atomic, returns 503 on partial cleanup; full UX/error-state review open |
| Skills | `components/views/skills-library-view.tsx` | `/api/v1/customer/skills` list/import/catalog/ingest/validate/install/permissions | moreai_skill_packages, source files, installs, registry audit; admin review RPC | Source integration and evidence UI exist; publication remains fail-closed while graph or license evidence is incomplete |
| Browser sessions | `components/views/code-view.tsx` | `/api/v1/customer/browser-sessions` list/history/close; internal worker-only lifecycle routes | moreai_browser_sessions/events/action receipts; isolated OpenFuse profile | Customer routes use customer principal; internal routes use worker token; deployed OpenFuse patch and persistent volume remain blocked |

## Authorization and ownership source audit

- Customer routes reviewed use `Depends(customer_principal)`; that dependency resolves through the server-side customer context rather than trusting client role claims.
- Conversation, run, artifact, knowledge-document, skill-package, memory and browser-session reads/mutations include authenticated user/owner filters or use the repository's owner-scoped record helper.
- Workspace access uses owner or active membership resolution; owner-only mutations additionally compare the authenticated owner ID before update/archive/member removal.
- Browser internal routes use `X-MoreAI-Worker-Token` validation. Worker-supplied user IDs are not treated as customer authentication; they are paired with canonical session/run ownership lookups before lifecycle mutation.
- Admin Skills review uses separate administrative route authorization and server-side reviewer RPC. Customer permission requests do not themselves grant execution permission.
- RLS is defense in depth. The browser must not use PostgREST, Storage, RPC, or Realtime directly for business data.

This is a source-level pass over the principal routes, not a complete control-by-control threat model. Cross-tenant denial, token validation, RLS role behavior, signed URL expiry, streaming reconnect/cancellation, idempotency and all error states have not been exercised because runtime testing is prohibited.

## Skills dependency graph increments

Committed to `main`:
- `8c0cf9d4da7b7e07692c4d19a4d5e8a98dcd685a`: npm lockfile v1 recursive package instances now retain nested `node_modules` locators and resolve edges by nearest ancestor lookup. Duplicate package versions are not collapsed by name.
- `3fea6d9fc04707ad2d82d618dd0868f2754b0b9f`: Cargo edges now resolve only against an exact package/version/source tuple present in Cargo.lock; missing or ambiguous nodes remain unresolved.
- `22c5d37e8aeb0fd542969b222743c0dcf0b741d0`: Ruby exact constraints now resolve only when exactly one matching locked gem node exists. Non-exact constraints and source/platform ambiguity remain unresolved.
- Existing fail-closed publication gate requires complete graph evidence and zero unresolved edges.

Remaining dependency graph work:
- pnpm importer parsing still needs exact workspace descriptor, alias, peer-context and package/snapshot join handling. Current text parser is intentionally bounded and does not implement a complete YAML grammar.
- Yarn Berry workspace, portal, patch, git and alias protocols need explicit source-aware resolution. The current parser is not a full Yarn lock grammar implementation.
- Python markers, extras, optional dependency groups, workspace groups and non-registry source identity need environment-aware resolution. Poetry/uv edges are extracted only where lock records expose them; Pipfile.lock remains graph-blocking.
- Go requires a module-aware graph (including go.work, replace, exclude, selected versions, platform/build tags and checksum identity); go.mod/go.sum alone are not accepted as a complete parent-child graph.
- Cargo target resolution now uses exact source identity, but workspace/path/git source normalization and package alias cases still need review.
- Ruby platform variants, git/path sources and Bundler source blocks need exact instance resolution; ambiguous or non-exact constraints remain blocked.
- Registry metadata/license resolution is currently authoritative only for supported npm, PyPI and crates.io package records. Other registries and non-registry packages remain human-review blockers.
- The parser is bounded source parsing, not a standards-complete package-manager implementation. No parser execution or tests were run.

## Supabase migration postcondition reconciliation

Canonical project: `uunfgimtokhucegqbpce`.

Read-only live inspection confirmed:
- Browser session event constraint still permits only `created`, `restored`, `state_saved`, `closed`, `expired`; new close/retention events are absent.
- Browser profile retention columns are absent.
- Live `moreai_review_skill_package` remains the older function definition and does not enforce the repository's new complete dependency graph, zero unresolved edges, empty findings and registry metadata conditions.
- `moreai-artifacts` bucket exists and is private, but no artifact-specific server-only policy was found.
- Six Phase 09D migrations remain unapplied; their order is dependency-safe: close-event vocabulary → Skills review gate → retention columns/event vocabulary → claim/ack RPC → Storage policy → retry lease column/RPC replacement.
- Four historical SQL definitions moved to `docs/implementation/sql-reconciliation-reference/` must not be replayed as new migrations. Exact historical SQL equivalence remains unresolved because the migration ledger does not expose historical SQL bodies.

Active pending migrations:
1. `20261116100000_moreai_browser_session_close_event_constraint.sql`
2. `20261116150000_moreai_skill_publication_evidence_gate.sql`
3. `20261116153000_moreai_browser_profile_retention.sql`
4. `20261116160000_moreai_browser_profile_retention_rpcs.sql`
5. `20261116170000_moreai_artifacts_storage_server_only.sql`
6. `20261116180000_moreai_browser_profile_retention_retry_lease.sql`

No migration was applied. Before application, reconcile every migration against actual object definitions, check policy-name collisions and review function ownership/grants. Never use `db push` against the 60 timestamp-mismatched historical files.

## OpenFuse profile deletion and storage

- Pinned upstream remains `CopilotKit/openfuse@7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`.
- The committed delete-profile patch adds an authenticated DELETE route, refuses active Chromium contexts, validates UUID identity, removes profile/session metadata and download residue, and treats already-absent profiles idempotently.
- Patch commit `dd8241dab338d86cdb688ce63e51c0e94b11d435` also ensures download residue is removed when the session metadata is already absent.
- MoreAI worker deletion remains gated on canonical FastAPI retention claims and acknowledges only after OpenFuse confirms deletion.
- The five-minute retention claim lease permits retry after worker/network failure. A successful delete followed by a lost acknowledgement can safely retry because OpenFuse deletion is idempotent.
- The OpenFuse patch is not applied to the deployed service. No deployment credential/host action was available.
- `WORKER_DATA_DIR` persistent private volume, encryption-at-rest, backup/restore and retention controls remain infrastructure blockers. No live OpenFuse runtime or volume is claimed.

## UI preservation

No customer UI file was changed in this continuation. The previous Research action and Skills evidence panel remain minimal additions in the existing component style. No navigation, layout, global CSS, Tailwind, theme token, font, button system or brand asset was redesigned. Before/after screenshots were not captured because browser interaction is explicitly prohibited.

## Phase decision and next work

**Phase 09 remains IN PROGRESS.** The source-level dashboard map is substantially populated, but end-to-end behavior, per-control authorization, error/retry/loading states and operational service configuration are not proven.

Next:
1. Finish pnpm/Yarn/Python/Go/Cargo/Ruby package locator edge cases while retaining fail-closed behavior.
2. Complete per-control API-client ↔ FastAPI route mapping, especially chat streaming/events, workspace membership, artifacts and memory clear/consent.
3. Complete migration-by-migration SQL object postcondition and privilege/policy collision reconciliation.
4. Apply the OpenFuse patch and configure its persistent private volume only when deployment access is authorized.
5. Complete Phase 09 evidence report without claiming Phase 10/11.

Phase 10 (end-to-end integration verification) and Phase 11 (integration release gate) remain blocked by the explicit no-testing/no-staging instruction. No test, build, lint, type-check, runtime, screenshot, staging, migration apply or deployment was performed.


## Follow-up package locator correction

Additional source commits after the initial audit:
- `a5d04a90eb419874455b856ea8d13dfa777d2455`: corrected npm v1 and v2/v3 nearest-ancestor lookup to begin at the package directory itself, then walk its ancestors. This matches Node's nested `node_modules` resolution order; starting at the parent directory skipped the package-local nested dependency directory.
- `3fea6d9fc04707ad2d82d618dd0868f2754b0b9f`: Cargo target edges are joined against an exact name/version/source tuple in the lockfile rather than synthesizing a locator from an edge string.
- `22c5d37e8aeb0fd542969b222743c0dcf0b741d0`: Ruby exact constraints only resolve when a unique locked gem node exists; a fabricated locator is no longer enough to make the graph appear complete.

These changes are source-only and intentionally unverified. npm v1 direct workspace-root edges are not yet represented as explicit graph edges, even though direct manifest names are checked against lockfile package inventory. That remains an SBOM graph completeness item and must not be silently represented as fully closed.


## Continuation — Python dependency declaration evidence (2026-11-16)

Updated `apps/api/app/routers/skills.py` on `main`:
- Python `pyproject.toml` inventory now includes PEP 621 project dependencies, optional dependency groups/extras, PEP 735 dependency groups when present, Poetry dependencies and Poetry dependency groups.
- PEP 508 marker text and requested extras are retained as evidence instead of being flattened into a single dependency string. Poetry table-form declarations retain source selectors (git/url/path/rev/tag/branch), markers and extras when exposed by the manifest.
- These declarations are explicitly marked as requiring environment-aware lock resolution. This is an evidence-preservation improvement, not proof that markers, extras, optional groups, platform selection or lock target package instances have been resolved.
- Pipfile.lock parent-child dependency edges remain unsupported; Go still lacks a module-aware selected-version graph; pnpm peer-context joins and Yarn Berry workspace/portal/patch/git/alias protocol resolution remain open. npm v1 root/workspace declaration edges still need a precise root locator join. The graph must remain incomplete for affected manifests and publication must remain fail-closed.

Commits:
- `b14b2e1ee6739a6190173f89e12355f41c27c6dc` — inventory Python extras and dependency groups.
- `f4bff561f85ede135d21055b03fb6117222f4f8f` — correct marker separator parsing.

No test, parser execution, build, lint, type-check, staging, browser/runtime verification, migration application, or deployment was performed. This source change is unverified by execution. No UI files or live Supabase objects were changed.


## Continuation — dependency protocol fail-closed and dashboard control review (2026-11-16)

### Dependency graph source changes

Additional changes in `apps/api/app/routers/skills.py`:

- npm lockfile v1 now emits explicit workspace-root → direct dependency edges from sibling `package.json` declarations, binding only to the top-level `node_modules/<name>` package instance actually present in the v1 nested lock tree. Missing direct targets remain unresolved.
- pnpm and Yarn dependency edges now explicitly refuse to bind non-registry protocols to a same-name registry package. Workspace/link/file/portal/patch/git/GitHub/npm alias protocol forms are marked unresolved until a protocol-aware workspace/alias resolver exists. This prevents false graph closure from name-only matching.
- pnpm peer-context and importer descriptor joins are still not a complete semantic resolver. Yarn Berry descriptor/protocol/portal/patch/workspace and alias resolution remains incomplete. These cases must keep the graph incomplete.
- Go module graph/workspace/replace/exclude/build-tag/selected-version resolution remains unsupported. Pipfile lock parent-child graph remains unsupported. Python marker/extras/group metadata is now preserved, but environment-specific lock resolution remains open.
- No unsupported protocol is silently treated as an ordinary registry dependency. The publication gate must remain fail-closed.

Commits:
- `df3747e96725f01b64c53de7b7ae5bef4c4f00ee` — fail closed on pnpm/Yarn workspace and Berry protocols.
- `fb60d7a6115e1d7949a8471882e1bf03a26f5462` — add npm v1 direct workspace-root edges.

### Dashboard control and authorization source audit

Read-only source review of customer controls confirmed these existing paths:

- Chat: durable conversation/session restoration, event cursor replay, SSE stream, retry as a new run, cancellation request to the durable worker, workspace selection and pagination.
- Tasks: run detail stream with AbortController cleanup, cancellation, retry as a new run, run/artifact pagination and signed artifact download.
- Research: run/artifact pagination and signed artifact download; handoff remains through Chat durable Agent Run.
- Files: artifact and workspace file listing, workspace membership access, file version history, signed downloads, upload, delete/restore lifecycle.
- Personal Memory: consent toggle, CRUD, episodic memory deletion and clear-all operation. Clear-all remains multi-step/non-atomic; API reports failure on partial cleanup and supports retry.
- Skills Library: import/ingest/validate/install/permission request/revoke. Execution remains server-gated and disabled until the server-side publication and permission conditions are met.
- FastAPI customer routes use authenticated customer principal and owner-scoped record lookups. Workspace routes resolve owner or active membership and role permissions. Internal worker routes use the worker token and canonical run/session ownership checks.

This is a source-level review, not proof of runtime isolation. Remaining unverified areas include cross-tenant denial under real identities, event reconnect under network interruption, cancellation race handling, retry idempotency under duplicate delivery, signed URL expiration/origin behavior against live Storage, partial Memory clear recovery, all UI error/loading/empty/forbidden states and worker/API availability.

### Artifact signed-download origin hardening

Updated `apps/api/app/routers/artifacts.py`:
- The signed-download response now rejects absolute Storage URLs outside the configured Supabase HTTPS origin.
- Rejects credentials, protocol-relative paths, backslashes and paths outside the Storage signed-object endpoint.
- Rebuilds the canonical signed URL from the configured Supabase origin while preserving the Storage query token.
- This aligns the artifact download boundary with the stricter origin validation already present in the workspace file download path.

Commit: `3b587997d35967ee23c1d0c0abf45d6357bd5ae9`.

### Verification and deployment boundary

No tests, parser execution, build, lint, type-check, staging, browser/runtime calls, migration application, OpenFuse deployment or Vercel deployment were performed. The code changes above are committed source changes only and remain execution-unverified. No frontend UI files were changed, no Supabase object was modified, and the six Phase 09D migrations remain pending. OpenFuse patch remains unapplied to the active service; persistent private volume configuration remains outstanding.


## Continuation — Phase 09 resolver, migration and OpenFuse lifecycle (2026-11-16)

### Latest source commit

This continuation's baseline was `e99a468c1aa1f15b31b36021eee38ca22df483ab`. The current source update adds migration postcondition documentation in commit `860f1e7ba33e51ab051aff4e2fff0814f4024eea`.

### Dependency resolver decision

A source re-review confirms:
- Pipfile.lock parser inventories exact `==` versions and hashes for default/develop groups but does not yet represent parent-child edges. It therefore remains graph-blocking.
- Go `go.sum` is checksum evidence, not a selected build graph. The source does not synthesize edges from checksum rows; Go remains blocked until module-aware selected graph resolution can account for MVS, go.work, replace/exclude, toolchain and build constraints.
- pnpm peer-context/importer and Yarn Berry protocol joins remain incomplete. Non-registry workspace/link/file/portal/patch/git/alias descriptors are explicitly unresolved instead of being bound to a coincidental registry package.
- Python marker/extras/group environment selection remains incomplete. Exact lock package records do not by themselves prove selected environment graph.
- The publication validator and database publication RPC continue to require a complete graph and zero unresolved edges. This is intentionally fail-closed.

### OpenFuse worker and browser lifecycle source review

Re-read the current MoreAI browser supervisor, worker reconciliation loop and FastAPI browser-session routes:
- The browser supervisor targets the pinned OpenFuse session API and exposes profile deletion as a separate adapter operation.
- Worker retention flow obtains candidates from FastAPI, requests OpenFuse profile deletion, and only then calls the FastAPI acknowledgement endpoint. Failures are logged and do not create a false deletion acknowledgement.
- The database claim lease is five minutes. The final retry migration replaces the claim/ack RPC definitions so a failed worker attempt can be retried after lease expiry and the claim is cleared on successful acknowledgement.
- Browser session and run ownership filters are present on internal lifecycle paths. This is source review only; worker token validation, concurrent deletion, real OpenFuse profile state, durable volume persistence, crash recovery and cross-tenant runtime behavior remain unverified.
- The OpenFuse patch must be applied to the separately deployed pinned service before profile deletion can succeed. The deployment still requires a persistent private `WORKER_DATA_DIR` volume, backup/restore, encryption-at-rest and retention operations.

### Migration reconciliation status

The earlier section describing five pending migrations is historical; the current active set is six, with the retry lease migration last. The companion Phase 09D report now includes:
- the dependency order and required live postconditions for all six migrations;
- post-apply catalog/function/ACL/Storage checks required for acceptance;
- explicit statements that Pipfile and Go graph evidence is incomplete;
- a warning that migration names/timestamps do not prove SQL-body equivalence.

No migration was applied, and no live database object was changed.

### UI and release boundary

No customer UI file changed in this continuation. Existing styles, colors, typography, button classes, layout and navigation remain untouched. The existing Browser Sessions, Skills Library, Chat, Tasks, Files and Memory views continue to call FastAPI through the typed API client.

No tests, parser execution, build, lint, type-check, browser/runtime, staging, migration apply, OpenFuse deployment or Vercel deployment were performed. Phase 09 remains IN PROGRESS. Phase 10 and Phase 11 remain blocked.


## Continuation — Go workspace fail-closed and browser lifecycle endpoint audit (2026-11-16)

### Source change: Go workspace dependency evidence

Commit `c73d5370b9972c2ca6a1eb9e2d1db0dd6bd5476f`:
- Added `go.work` to dependency-file inventory.
- Explicitly records workspace manifests as requiring a module-aware resolver.
- Go `go.sum` checksum rows are now labelled `checksum_record_not_selected_build_node`, so checksum evidence cannot be mistaken for a selected build node.
- `go.mod`, `go.sum`, and `go.work` remain graph-blocking until selected module graph resolution handles MVS, workspace use/replace, module replace/exclude, toolchain and build constraints.
- This is a source change only; no parser execution was performed.

### Browser lifecycle endpoint review

Re-read FastAPI browser session routes, worker reconciliation and OpenFuse supervisor:
- Retention claim endpoint is worker-token protected and delegates to the service-role RPC.
- Acknowledgement endpoint is worker-token protected and passes canonical session/user identity to the service-role RPC.
- Worker only acknowledges after OpenFuse returns the expected profile ID and `status=deleted`.
- Failed OpenFuse deletion or failed acknowledgement is logged and retried by the five-minute claim lease after the final migration is applied.
- Close-request polling defers a session while its last run remains queued/running/waiting_approval. Physical close occurs in OpenFuse before FastAPI records the closed state.
- Owner-scoped customer session/history queries use the authenticated user's ID. Internal lifecycle endpoints depend on the worker token and canonical owner filters.

### Source-level risks still open

- The close-complete endpoint updates the session and writes its event in separate repository calls; it is not a single database transaction. A failure between those calls can leave a closed session without the matching event. This should be moved behind an atomic service-role RPC before calling lifecycle audit fully closed.
- Retention claim and acknowledgement are atomic within their SQL RPCs, but remain unavailable until the six pending migrations are applied.
- Worker/OpenFuse behavior remains unverified. In particular, the separately deployed OpenFuse worker still needs the delete-profile patch and persistent private volume.
- No claim is made about cross-tenant denial, concurrency, process-crash recovery, or real browser profile deletion without runtime evidence.

No UI files were modified. No tests, build, lint, type-check, browser/runtime, staging, migration apply or deployment were performed. Phase 09 remains IN PROGRESS.


## Continuation — atomic browser close completion (2026-11-16)

Baseline: `6b760c110faf76cce4bf060229afe057ed35e7d9`.
Implementation commit: `23832ff3f8b630644134b3375484baf1ce0cdd4f`.

- Added forward-only migration source `20261116190000_moreai_browser_session_close_atomic.sql`.
- Added `public.moreai_complete_browser_session_close(uuid,uuid)`: validates non-null identity, locks the canonical session row, verifies the owner and `close_requested` state, updates the session to `closed`, clears encrypted state, sets close/retention timestamps, and inserts the `closed` lifecycle event in the same PostgreSQL transaction.
- The function is idempotent for an already-closed session and returns a replay result without inserting a duplicate event.
- Execute privilege is revoked from `PUBLIC`, `anon`, and `authenticated`; only `service_role` is granted execution. FastAPI continues to authenticate the worker token before invoking the RPC.
- FastAPI `/internal/{session_id}/close-complete` now delegates to this RPC and validates its response contract; it no longer performs separate PATCH and INSERT requests.

Limitations:
- The migration is committed as source only and has **not** been applied to Supabase project `uunfgimtokhucegqbpce`. Until applied, the endpoint will fail closed because the RPC does not yet exist in the live database.
- The customer close-request path, TTL expiry reconciler and acquire-expiry guard still have separate status/event writes; these remain the next atomicity work.
- The migration was added directly to the repository using the GitHub file/tree API because no local Supabase CLI workspace was available in this execution. It was not generated with `supabase migration new`; reconcile this against the project's migration-generation convention before applying.
- No SQL execution, tests, build, lint, type-check, staging, browser/runtime verification or deployment was performed.

Phase 09 remains **IN PROGRESS**. No Phase 10 or Phase 11 gate is claimed.


## Continuation — complete atomic browser close request/worker paths (2026-11-16)

Baseline: `f88f15a7bf25603e6684fbd06f26d688fa86c6f5`.
Source commits:
- `70413f5f11028665edcc2bfb58735395ec9f155a` — atomic close request for customer, TTL reconciler and acquire-expiry guard.
- `ac322ad222dfc6146a43ed63840d278bc947b377` — atomic worker close path.

Changes:
- Added `20261116200000_moreai_browser_session_close_request_atomic.sql` with `moreai_request_browser_session_close(uuid,uuid,text,text)`. It row-locks and validates owner/status/source/reason, transitions active → close_requested and appends one event in the same transaction. Replays of close_requested/closed return without duplicate events.
- Customer `POST /{session_id}/close`, internal TTL/idle expiry reconciler, and acquire-expiry guard now call this RPC. The TTL scanner still discovers candidates through a bounded read; the state transition and event append are atomic and concurrency-safe.
- Added `20261116210000_moreai_browser_session_worker_close_atomic.sql` with `moreai_mark_browser_session_closed(uuid,uuid,uuid)`. The worker close endpoint now validates the owning Agent Run and delegates the session transition plus event append to one transaction.
- The prior `moreai_complete_browser_session_close` RPC remains the reconciler close-completion path. All three close state transitions now use atomic database functions; duplicate close requests/completions are idempotent.

Customer API audit snapshot:
- `customer.py`: customer-principal dependency on all customer routes; conversation/run reads use owner-scoped repository methods; enqueue/cancel/usage/memory-consent paths use server-side RPCs. Memory clear disables consent, purges episodic metadata, then deletes user memories as separate operations. Failure returns 503 and invites retry, but this is not a single atomic transaction; partial progress is possible and must remain visible/retryable.
- `knowledge.py`: upload/list/detail/retry/reindex/archive routes require customer principal and workspace-access checks. Detail chunk count uses a scoped RPC. Processing depends on durable worker availability; live processing not verified.
- `skills.py`: all customer skill routes require customer principal. Validation, import, ingestion, installation and permission workflows are distinct. Install/execute remain gated by publication/validation and permission policy; parser graph incompleteness remains fail-closed. Live worker publication/installation not verified.
- `artifacts.py`: customer list/create/download routes use authenticated principal and owner-scoped run/conversation/artifact checks; signed download URLs are server-created and origin-validated. Storage policy migration remains unapplied.
- `workspaces.py`: list and file lifecycle operations use workspace membership/role checks; delete/restore/upload use server RPCs; run listing requires `agent.run.read`. No browser-side direct Storage/PostgREST access is intended.
- `agent_runs.py` and customer run routes: owner-scoped run reads, steps/logs/thinking/progress/events/stream, cancel through worker RPC; workspace access checked for enqueue. Runtime stream/retry/cancel behavior remains unverified.
- Memory router is housed in `customer.py`, not a separate `personal_memory.py` module.

Remaining audit/implementation gaps:
- Memory clear-all still consists of multiple database operations rather than one transaction. A dedicated owner-scoped atomic purge RPC should replace the sequence, while preserving episodic cleanup semantics and auditability.
- Browser session creation, restore/update, state-save and initial event append still contain multi-request write sequences. The close-specific lifecycle paths are atomic; this does not yet establish full atomicity for every browser event.
- TTL candidate discovery is bounded to 100 active rows and currently does not page. A sustained backlog may delay later candidates; use cursor/claim batching or a database-side expiry claim RPC.
- Migration sources `20261116190000`, `20261116200000`, and `20261116210000` are committed but not applied. Their dependency is after existing close-event vocabulary and retention columns (the prior Phase 09D six-migration chain); verify live postconditions and function privileges before any apply.
- No actual tests/build/lint/type-check, SQL execution, staging, browser/runtime verification or deployment was performed.

Phase 09 remains **IN PROGRESS**. UI files were not changed in this continuation; existing frontend visual system remains untouched.


## Continuation — production customer API origin/CORS correction (2026-11-16)

### Evidence from the reported customer screens

The supplied production screenshots show the same transport-level error in:
- AI Skills Library;
- AI Agent Studio (catalogue reports zero active models because the catalogue request cannot complete);
- the Chat conversation composer (workspace availability lookup fails and the screen falls back to private conversation).

These surfaces use the shared typed browser API client in `lib/api/client.ts` and FastAPI as their business API. The repeated transport error is therefore consistent with a shared API-origin/CORS failure rather than three independent feature defects. The screenshots are user-observed evidence; they do not by themselves distinguish a missing CORS header from an incorrect API URL or unavailable API process.

### Source-level cause found and correction committed

At baseline `e7c4b67f7b95b8e7b65102e4e515814bd1e530f5`:
- `apps/api/app/main.py` built `_cors_origins` solely from `MOREAI_CORS_ALLOWED_ORIGINS` and registered CORSMiddleware only when that list was non-empty.
- `.env.example` contained only `http://localhost:3000` for that setting.
- The customer production origin `https://moreai.web.id` was not a default allowed origin.
- Mutating browser requests also compare the Origin header against this same list in the correlation middleware, so an omitted production origin affects both preflight/read access and the server-side mutation origin guard.

Source changes on `main`:
- `5ee9c7aeb6692c330d3b1fced60b6957e7ab376a` — `apps/api/app/main.py` now always includes the exact production origin `https://moreai.web.id` and merges in explicitly configured origins with duplicate removal. The existing explicit methods, headers, bearer-token behavior and non-credentialed CORS policy are preserved; no wildcard origin was introduced.
- `ef025ba1d813719a7ad6d1b2c6c3dff41bd055cd` — `.env.example` now documents `https://moreai.web.id,http://localhost:3000`.

This change covers the shared browser-to-FastAPI origin gate. It does not invent a frontend API URL, bypass FastAPI, or add direct browser access to Supabase business data.

### Deployment and environment boundary

- Vercel read-only project/deployment/environment inspection was attempted for the already-existing MoreAI web and API projects, but the connected Vercel account returned HTTP 403 `forbidden` for project/deployment reads. Domain configuration lookup also returned 403. No environment variable values or deployment state could therefore be verified.
- `NEXT_PUBLIC_MOREAI_API_URL` in the deployed web build must still point to the actual public FastAPI deployment/alias. Its production value is not visible from the current authorized connector response; it has not been guessed or changed.
- The FastAPI CORS source correction takes effect only when the API service runs a version containing the commit. No deployment was manually triggered and no live effect is claimed.
- No UI route, component, design token, CSS, font, navigation or visual style was changed.

### Verification boundary and decision

No browser/API runtime test, preflight request, test suite, build, lint, type-check, staging, migration application or deployment was run, in accordance with the product-owner instruction. The CORS fix is committed source code but remains production-runtime unverified. The domain's API URL and Vercel deployment configuration remain operational blockers until read access is restored.

Phase 09 remains **IN PROGRESS**. The next required work is to verify the existing Vercel production environment variable names (without exposing secret values), confirm the API project is mapped to the actual FastAPI service, and then continue the customer control-by-control integration audit and atomic Memory cleanup. Phase 10 and Phase 11 are not claimed.
