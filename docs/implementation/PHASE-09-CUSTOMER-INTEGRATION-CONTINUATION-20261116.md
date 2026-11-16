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
