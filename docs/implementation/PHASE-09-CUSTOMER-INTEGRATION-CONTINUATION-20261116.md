# Phase 09 — Customer Dashboard Integration Continuation

Date: 2026-11-16  
Branch: `main`  
Baseline HEAD inspected: `d56ffbd6198dba6513a45261f6c437db9f6d2e5b`

## Scope

Reconcile durable Agent Run/event lifecycle, Customer dashboard screens and API contracts, skill governance/resolution, and provider/wallet/entitlement paths. This is source inspection and implementation planning only; no runtime verification was performed.

## Confirmed implemented source contracts

### Durable OpenManus lifecycle

- `apps/api/app/routers/agent_runs.py` exposes owner-scoped run list/detail, steps, logs, thinking/progress, events, SSE stream, cancellation and related lifecycle APIs.
- Event cursors validate 64-bit sequence values and honor `Last-Event-ID`; events are ordered by sequence and owner scope is checked before access.
- Event/checkpoint projection filters private checkpoint state and sensitive tool payloads before exposing Customer-safe progress.
- Customer Tasks opens run detail, consumes steps/activity/progress/artifacts, subscribes to the authenticated run stream and refreshes canonical snapshots. Workflow screen consumes run, approvals and artifact APIs.
- Worker runtime restores persisted checkpoints, renews run leases, watches cancellation and lease loss, stops execution when lease ownership cannot be proven, and leaves interrupted work recoverable. Retryable errors use durable finish/requeue handling.
- Durable event outbox has claim/ack/retry handling. These features must not be reimplemented as a second event or task subsystem.

### Skills

- FastAPI Skills router and Customer typed client expose catalog/import/ingest/validate/install/permissions/revoke workflows.
- Worker resolver accepts only owner-bound, validated, license-approved, published and installed packages with approved permission snapshots.
- Resolver verifies the full source inventory against SBOM SHA-256, Git blob SHA and package root provenance, and writes resolution audit records.
- Skill resolver fails closed for missing/incomplete source files or permission mismatches.
- Motion child repositories are catalogued by pinned source; the aggregator remains a catalogue, not a skill package. Recursive governance must finish per-child/per-file license, attribution and dependency review before publish.

### Provider, wallet and entitlement

- Customer API has wallet, ledger, usage, usage analytics, entitlement and quota endpoints; frontend typed client exposes corresponding reads.
- Worker Model Router reads enabled route/model/provider policy records and validates provider secret environment references without making provider calls in readiness snapshot.
- LLM gateway is configured for metered routing/accounting. Source-level presence does not prove production provider/model rows, secrets, price schedules or active workers are provisioned.
- Previous read-only inventory found provider/model catalogue tables empty; no fake rows or defaults should be inserted to make the UI appear active.

## Remaining integration gaps / decisions

| Area | Existing source | Remaining work / blocker |
|---|---|---|
| Browser Human Takeover | Owner-scoped sessions, encrypted profile state, worker acquire/close, event history | No authenticated short-lived scoped takeover grant, same-session attach transport, one-time consumption/revocation or takeover audit flow. Must be implemented across FastAPI + OpenFuse supervisor + worker before UI affordance. |
| Browser Session History | History endpoint and typed client | Profile UI does not consume history. UI edit remains gated by AGENTS requirement for before/after screenshots; no UI change made without that evidence. |
| Computer Workspace | Isolated Python/Bash supervisor, worker approval gate, action receipt claim/finish, customer receipt listing | No customer-authorized interactive workspace session, terminal stream/reconnect, resize/input/output protocol, cancellation contract or customer audit timeline. Do not expose interactive controls until the entire isolated path exists. |
| Worker fencing | Heartbeat loss fails closed; checkpoint and retry paths exist | Need a source-level cross-check of every mutation RPC for fencing token/lease generation conditions, especially late event/checkpoint/finish writes. Do not equate heartbeat alone with full fencing proof. |
| Event replay | Durable ordered events, SSE cursor and Last-Event-ID, outbox retry | Need reconciliation of reconnect bounds, retention/compaction, duplicate delivery semantics, event gap recovery and frontend cursor persistence. Existing foundation should be extended, not duplicated. |
| Customer screen mapping | Customer routers, typed API client, many screen integrations | Complete route-by-route inventory remains outstanding for Home, Create/Generate, Agent Studio, Skills, Knowledge, EduTech, Files, Benefits, Wallet, Notifications, Connections, Profile, Workflow and Tasks, including loading/empty/error/retry and ownership boundaries. |
| Skills governance | Pinned catalog/import, recursive ingestion, validation and execution resolver | P1 recursive file/license/dependency inventory, Visual attribution and Scenario nested content review remain incomplete; publish/install must remain approval-gated. |
| Provider/billing | Router, metering, wallet/ledger, quota and entitlement APIs | Need source-to-table and provider pricing/version reconciliation; confirm every generation/agent path charges usage exactly once, handles unknown provider outcome and applies entitlement/quota before dispatch. No live provider configuration is asserted. |

## Human Takeover and Computer Workspace implementation constraints

Human Takeover cannot be implemented as a frontend-only control or a generic WebSocket proxy. Required design:
- authenticated Customer endpoint verifies owner, tenant, active session, active run/session status and policy;
- server creates cryptographically random, one-time, short TTL grant bound to user + session + browser profile + allowed operations;
- raw OpenFuse credentials/profile state never leave backend/worker;
- private supervisor atomically consumes grant and attaches to the existing profile (never creates a parallel profile);
- revoke on expiry, close, owner logout, run terminal state, policy denial or explicit revoke;
- durable audit records grant issuance, consumption, actions and revocation;
- all high-impact actions continue through backend approval and receipt lifecycle.

Computer Workspace requires a similar owner-bound grant, but the isolated supervisor must additionally provide bounded stdin/stdout streaming, reconnect cursor, cancellation/process-tree termination, resource accounting, artifact handling and immutable action receipts. It must never expose Docker/socket/host filesystem access to the browser.

## UI gate and verification boundary

No UI files were changed. The existing UI is protected under AGENTS.md. Adding History, Takeover or Computer Workspace UI requires baseline and after screenshots plus a minimal-diff justification. The user's prohibition on real tests/staging/deployment is respected; screenshot evidence is a separate UI change gate, not a runtime test.

No tests, lint, build, type-check, screenshot capture, browser/API/worker runtime, Docker, provider/OAuth calls, staging, deployment, migration apply or Supabase mutation were performed.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED**. Phase 11 remains **BLOCKED**.


## Implementation update — Browser action worker-lease fencing

Commits:
- API: `7de4e7bc2dc7c731d56e8b437a225cfde404ac2c`
- OpenFuse adapter: `8943a7aa25436963d5f51f5539c4deb1909512ae`

Implemented on `main`:
- Browser action receipt claim now carries the authenticated internal worker identity and only accepts a run that is still running, owned by that worker ID, and has an unexpired lease.
- Browser action receipt finish now applies the same active-owner/unexpired-lease condition. A late worker cannot finalize a receipt after lease loss or after the run has left the active state.
- OpenFuse BrowserSupervisor supplies its configured worker ID on both claim and finish calls.
- Existing receipt idempotency and unknown-outcome handling remain intact.

Scope boundary:
- This fences browser receipt claim/finalization by the current worker lease owner identity and expiry. It does not add a monotonic lease-generation token; if a deployment reuses the same worker ID across overlapping process incarnations, a generation/fencing token is still required.
- Computer action receipt path is not yet updated to the same contract and remains an explicit gap.
- No runtime, tests, lint, build, typecheck, screenshots, staging, deployment, Docker or Supabase mutation were performed.


## Implementation update — Computer action worker-lease fencing

Commits:
- FastAPI claim/finish fencing: `13599f9e5e54de6a1e18591d41bffe5625d67c12`
- Isolated sandbox adapter worker identity: `adad58945bca37a0c68a471f5edfbe2c5b324430`
- Worker runtime identity binding: `4eed28a8e3cfd5b1f54f1513482438880c9307ea`

Implemented on `main`:
- Computer action claim now requires a running Agent Run, matching workspace, matching `lease_owner`, and an unexpired lease.
- Computer action finish now requires the same active worker ownership and unexpired lease; stale workers cannot finalize after lease loss or run termination.
- IsolatedSandboxToolAdapter sends worker identity for claim and finish, bound to the WorkerRuntime's configured `WORKER_ID`.

Remaining safety boundary:
- Human Takeover is not marked implemented. Current OpenFuse browser console is a signed preview/input console, but MoreAI does not yet provide a customer-authorized, one-time, short-lived, session/profile-bound grant with revocation and audit that the browser supervisor consumes. Adding only a frontend button or signed URL would bypass the required grant contract, so that shortcut was deliberately not introduced.
- A monotonic lease-generation/fencing token is still needed to protect against worker process reincarnation that reuses the same worker ID.
- Computer workspace streaming/reconnect/cancellation/resource accounting and broader Customer screen reconciliation remain open.
- No tests, build, lint, typecheck, runtime calls, staging, deployment, Docker execution, or Supabase mutation were performed.


## Implementation update — takeover revocation lifecycle hardening

Commits:
- Agent Run terminal-state revocation migration: `296aa3ffe284027982d956385c66d074795d2629`
- Customer logout revocation RPC migration: `f93868e0c192a074ce87081e2ce9793ea58f7348`
- FastAPI owner-scoped logout revocation endpoint: `7daacc6783eed84a7232fd478bc511a12e5a2fda`
- Typed Customer API method: `41aa34432ffff2a595e6006b06f82d8819f8db79`

Implemented:
- Unconsumed grants associated with a browser session are revoked when its linked Agent Run transitions to a terminal state (`succeeded`, `failed`, `cancelled`, `timed_out`, `expired`). The trigger covers both `run_id` and `last_run_id` associations and records a per-session audit event.
- Added a service-role-only RPC to revoke all unconsumed browser takeover grants for one customer, with per-session `customer_logout` audit events.
- Added authenticated FastAPI `POST /api/v1/customer/browser-sessions/takeover-grants/revoke-all`, scoped to the current customer principal.
- Added a typed frontend API method `customerApi.revokeBrowserTakeoverGrantsOnLogout()`.

Important remaining gap:
- The logout revocation endpoint and typed client method are available, but the existing logout callback has **not yet been wired** to invoke it before Supabase Auth sign-out. UI-file edits remain gated by AGENTS.md screenshot evidence.
- The dashboard-to-worker takeover command transport and customer input/preview interface are still not wired. Thus Human Takeover remains **backend lifecycle foundation**, not end-to-end.
- The migrations are committed but not applied to Supabase. No tests, build, lint, type-check, screenshots, runtime, Docker, staging, deployment or Supabase mutation were performed.
- Phase 09 remains IN PROGRESS; Phase 10 NOT ACCEPTED; Phase 11 BLOCKED.


## Implementation update — customer logout now invokes takeover revocation

- Commit: `9918b1c2a8c32e3f98efa096c4870349f0add94f`
- Updated `app/page.tsx` to provide the existing Profile Settings `onLogout` callback.
- Logout now attempts the authenticated FastAPI customer revoke-all endpoint before calling Supabase Auth `signOut()`, then routes the user to the existing login screen.
- If the revoke API is unavailable, the customer is still signed out; grants remain bounded by their short TTL. The failure is logged and is not represented as a successful revoke.
- This closes the missing callback path identified in the prior inspection. It does not complete Human Takeover: dashboard grant issuance/input, preview streaming, reconnect and private worker command delivery remain outstanding.
- UI structure and styling were not changed; only the existing callback wiring was added. No screenshot was produced, no tests/build/lint/typecheck/runtime were run, and no migration was applied.


## Implementation update — customer-visible Skill execution audit API

Commits:
- FastAPI owner-scoped audit reader: `24cbd18946dcf7b6c79f3d86f9c907c5309db11e`
- Typed Customer API client: `8b3087b8396b011d356f32d6233a07d59ce05cbf`

Implemented:
- Added authenticated `GET /api/v1/customer/skills/audit` with bounded limit (1–100), optional Agent Run and Skill filters, owner scoping, and newest-first ordering.
- Exposes only the caller's existing durable `moreai_skill_execution_audit` receipts: resolved/rejected/executed event, immutable skill version/content hash, permission snapshot, run/install references and event detail.
- Added `CustomerSkillExecutionAudit` and `customerSkillApi.audit()` typed client contract. No new table or duplicate audit ledger was introduced.

Boundary:
- This exposes audit data to the existing Customer API layer; the Skills Library UI has not yet been changed to render the audit timeline.
- Existing source catalog/batch implementation already covers 2 Visual, 172 Scenario and 56 Motion child-pack entrypoints; the Motion aggregator itself is a catalogue and has no executable SKILL.md. Actual batch ingestion and approval remain separate owner/reviewer actions. No customer package rows were fabricated.
- No tests, build, lint, typecheck, screenshots, runtime, staging, deployment or Supabase mutation were performed. Phase 09 remains IN PROGRESS.


## Implementation update — durable Human Takeover command transport

Commits:
- Durable encrypted command queue and atomic worker claim/finish RPCs: `fed6338177d243467686e4e587f26c346c9119b2`
- Browser audit event vocabulary alignment: `3dfd1f7003de68e7a250c09d1f37d3a73d10f735`
- FastAPI customer enqueue/status and worker claim/finish routes: `1c01c497c9b9a07a4256916bdfe1e29386623d4b`
- Worker polling and OpenFuse execution: `197739643fff388de37f6002f9e413d3c972cbce`
- Worker task shutdown handling: `c1c19ff9cd4c40d64463011f8faf62a411b05185`
- Typed Customer API grant/submit/status/revoke methods: `60e6a5cd5a05d21df4f94f6f64bc4b637e1eac1f`
- Queue lease-expiry and no-blind-replay hardening: `6edc5a746d0585c8648d37202f3f584d5faee4c0`

Implemented on main:
- Added a service-role-only durable command queue in the existing Supabase project. The grant token and bounded input payload are encrypted using the existing browser-session encryption key; the table stores no plaintext bearer token.
- Customer FastAPI route verifies session ownership/status and grant digest/expiry before queueing one command per one-time grant.
- Worker-only claim/finish routes require the internal worker token and worker identity. Claim uses an atomic `SKIP LOCKED` RPC and returns the decrypted command only over the authenticated worker API.
- Worker polls the queue only when the OpenFuse BrowserSupervisor is enabled, invokes the existing one-time `takeover_input()` method, and records the durable command outcome. Existing grant consumption and per-session input audit remain in force.
- Added owner-scoped command status retrieval and typed frontend methods.
- Expired queued grants are marked expired. A command with an expired worker lease is marked failed with an explicit unknown-outcome code and is not blindly replayed, because the grant may already have been consumed and the browser action may have reached Chromium.
- Added the `takeover_command_queued` event to the browser session event constraint while retaining existing close and takeover event vocabulary.

Important remaining integration:
- The existing dashboard still does not render a customer takeover control, input form, preview stream or reconnect experience. Typed API methods are ready, but UI edits are gated by AGENTS.md's before/after screenshot requirement; no baseline screenshot tool/evidence was available in this implementation context.
- OpenFuse preview transport is not yet exposed through an owner-authorized FastAPI artifact/stream route.
- The new migration is committed only; it has NOT been applied to Supabase. Worker/API host configuration and browser service availability are not confirmed. Therefore this is a code-level transport implementation, not a claim of live production interaction.
- No tests, lint, typecheck, build, runtime, screenshots, staging, deployment, Docker or Supabase mutation were performed.
- Phase 09 remains IN PROGRESS; Phase 10 NOT ACCEPTED; Phase 11 BLOCKED.


## Customer AI Skills audit timeline wiring

- Commit `02f700b62873b52ad6bec7105e4c2b308f78ed9b` connects the existing Skills Library screen to the owner-scoped `customerSkillApi.audit()` endpoint already backed by `moreai_skill_execution_audit`.
- The existing screen now renders the last 50 durable Skill resolver/rejection/execution receipts, including immutable Skill version/content hash, Agent Run reference, permission snapshot, timestamp and rejection reason when present. Loading, empty and API error states use the existing card, typography, border and red/neutral status styles.
- No new table, mock data, direct Supabase browser access, automatic publication, permission grant or Skill execution was introduced.
- Source change only; no tests, lint, typecheck, build, runtime, staging, deployment or Supabase mutation were performed.


## Implementation update — Customer Human Takeover dashboard wiring

- Component commit: `1ee94506eca59df5731456563c59a09c319fe98a`; Profile Settings integration: `ae3926b9b96d3676ecc4b650d4d8dfa2e7964a55`; input-schema neutrality correction: `2ae92fcc8775e959fe353b36f44564ef0e75a9ac`.
- Added `components/views/browser-session-takeover.tsx` and mounted it inside each existing Profile Settings browser-session card, alongside the existing preview.
- Customer can submit a JSON object to the existing FastAPI takeover contract. The UI obtains a 90-second one-time grant, holds its raw token only in component memory, queues the command through the typed Customer API, and polls the owner-scoped command status. It surfaces queued/processing/succeeded/failed/expired states and API errors. Closed/expired sessions do not expose input controls.
- The payload editor intentionally does not prescribe an OpenFuse action schema; the adapter accepts a bounded object and forwards it to the existing OpenFuse session input endpoint. The exact payload semantics remain determined by the deployed OpenFuse contract.
- UI follows the existing Profile Settings card, Tailwind, red action, slate border, compact typography and responsive patterns. No direct Supabase data access or mock responses were added.
- Source-only implementation. The takeover queue/grant migrations remain committed but unapplied; worker/API/OpenFuse runtime and deployed input payload semantics are unverified. No tests, lint, typecheck, build, runtime, staging, deployment, screenshot capture or Supabase mutation was performed.
- Phase 09 remains **IN PROGRESS**; Phase 10 remains **NOT ACCEPTED**; Phase 11 remains **BLOCKED**. Next: persist/recover recent takeover command status from the existing session event/command history contract where available, then continue Memory Coordinator lifecycle and full route-to-screen reconciliation.

- Follow-up commit `e95785ab2dd975b08fc7aeec532443592cc80bfe` restores the newest queued Human Takeover command after page reload by reading the existing owner-scoped browser-session event projection and retrieving command status from FastAPI. Failed/ambiguous submission attempts revoke any still-unconsumed grant; no token is persisted. This is source-only and remains subject to unapplied migrations and unverified worker/OpenFuse runtime.


## Contract correction — Human Takeover status response

- Commit `fbf03b0bde78b16492c535ba4d723adfce43079b` aligns `GET /api/v1/customer/browser-sessions/takeover-input/{command_id}` with the existing typed client: the database `id` is now returned as `command_id`, with only the documented owner-scoped status fields. This fixes the response mismatch that would otherwise prevent the newly wired UI from reading command status/reconnect state. Source-only; no tests/runtime/migration apply/staging/deployment.
