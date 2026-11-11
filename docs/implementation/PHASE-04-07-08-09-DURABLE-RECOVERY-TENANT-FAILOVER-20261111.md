# MoreAI Direct-Main Integration Report — Durable Recovery, Customer/Partner API, Provider Failover & Sandbox Adapter

**Date:** 2026-11-11  
**Target repository:** `fadliansyah36/More-AI-Portal-Indihome`  
**Branch:** `main`  
**Implementation HEAD at report time:** `895253b7176f25ef76f1f0852376612f25c05d0d`  
**Supabase project:** `uunfgimtokhucegqbpce`  
**Execution mode:** direct commits to `main`; no branch created.

## 1. Executive result

The requested three integration seams have been implemented as a main-branch increment:

1. OpenManus runtime ↔ Supabase: restore run checkpoints and conversation/tool transcript after worker restart.
2. Existing frontend ↔ FastAPI: separate Customer and Partner route groups, server-side role/tenant checks, and typed frontend API integration.
3. Provider ↔ sandbox: ordered primary/fallback provider candidates under one metered reservation, plus a digest-pinned isolated Docker adapter with explicit approval gating.

This is **not a sign-off of Phases 04–11**. Upstream tool/domain parity, approval service, real-provider E2E, and release evidence remain outstanding.

## 2. Runtime and Supabase recovery

### Implemented

- `WorkerRpcClient.list_checkpoints(run_id)` reads the existing `agent_run_checkpoints` rows through the server-only Supabase REST client.
- `RegisteredAgentDispatcher` restores checkpoint state before constructing `AgentRunContext`.
- `AgentRunContext.recovery_checkpoints` carries the persisted run state into OpenManus.
- `SupabaseConversationMemoryStore.load_run()` restores messages for the active run; `load()` restores the owner/workspace-scoped conversation transcript.
- Manus now persists:
  - the assistant tool-call message before execution;
  - a per-tool intent checkpoint;
  - the settled tool observation;
  - the tool response message;
  - completed round markers;
  - the final result.
- Restart recovery reuses saved response/tool results and does not re-execute a tool whose settled checkpoint already exists.
- A process interruption no longer marks a run terminally failed just because the worker task was cancelled during shutdown. The lease and checkpoints remain available for reclaim; an explicit user cancellation remains terminal.
- The worker factory now passes the persistent Supabase memory store into the active Manus runtime.

### Recovery semantics

The durable recovery path is:

`claim → restore checkpoints → restore run transcript → resume pending tool calls → continue next round → persist final output → finish`

Tool observations are truncated before persistence to a bounded size. The only currently exposed tool is the existing metered nested chat-completion tool, which uses a deterministic request key. Non-idempotent tools remain unavailable until their own idempotency and approval contracts exist.

## 3. Customer and Partner server-side API isolation

### Customer API

- `GET /api/v1/customer/context`
- `POST /api/v1/customer/conversations`
- `GET /api/v1/customer/conversations`
- `GET /api/v1/customer/conversations/{conversation_id}`
- `POST /api/v1/customer/conversations/{conversation_id}/messages`
- `GET /api/v1/customer/agent-runs`
- `GET /api/v1/customer/agent-runs/{run_id}`
- `GET /api/v1/customer/agent-runs/{run_id}/stream`

### Partner API

- `GET /api/v1/partner/tenants`
- `GET /api/v1/partner/context`
- `GET /api/v1/partner/locations`
- `GET /api/v1/partner/members`

### Authorization rules

- Customer is the authenticated base principal only when the account has no active Partner membership and no active privileged platform-role assignment. The current live `roles` table does not contain a dedicated `customer` role, so the base Customer role is derived server-side rather than inferred from a frontend mode.
- Partner tenant identity is resolved from active `partner_members` records, not trusted from a request body or client-side mode.
- Partner organization must be active.
- Partner owner/admin can list members; location manager/staff are restricted to their assigned location; analyst is read-only.
- A caller with multiple partner tenants must explicitly select a tenant.
- Existing generic conversation, agent-run, and artifact routes now use the same Customer-principal dependency, preventing Partner principals from bypassing the dedicated route groups.
- Run-event responses expose only UI-safe checkpoint fields. Tool arguments, raw observations, and internal provider details are not returned through SSE/event APIs.

### Frontend wiring

- Customer Chat now creates conversations, queues messages, polls run status, and streams run events through the Customer API route group.
- Partner Portal now loads authorized tenant choices, tenant context, and locations from FastAPI.
- Multi-tenant Partner users can select only a tenant returned by their active membership.
- Demo partner locations, fabricated usage metrics, simulated QR issuance, and hardcoded package/analytics claims were removed from the integrated Partner view. QR, package, analytics, and registration workflows show an unavailable state until their server contracts exist.
- Existing visual structure was preserved; no broad UI redesign was performed.

## 4. Provider fallback and metering

- `ModelRouter.resolve_candidates()` returns ordered primary and configured fallback models, de-duplicated by provider/model identity.
- `MeteredGateway.complete()` and `stream()` reserve against the maximum estimate across candidate routes, then settle against the provider that actually completed the request.
- Failover is restricted to explicit retryable provider availability/transport errors.
- Streaming may switch provider only before any response delta is emitted. Once a delta is visible, the stream is not restarted on another provider to avoid duplicate or contradictory output.
- If provider activity has already occurred and subsequent accounting persistence fails, the reservation is retained rather than released as though no provider usage occurred.
- Provider API keys remain server-side and real-key testing remains deferred as instructed.

## 5. Isolated sandbox adapter and activation gate

### Implemented

- Added a worker-to-sandbox adapter for Python and Bash with a required run/user/tool approval callback. The adapter denies execution when no approval checker or approval is present.
- Hardened the Docker runner:
  - immutable `image@sha256:<64-hex>` requirement;
  - `--network=none`;
  - read-only container filesystem and read-only source mount;
  - non-root UID/GID;
  - all Linux capabilities dropped;
  - no-new-privileges and default seccomp;
  - bounded PID, memory, CPU, wall time, source size, and stdout/stderr;
  - disposable temporary workspace and process-group termination on timeout/output overflow.
- Added tests for approval gating and the actual Docker invocation security flags.

### Deliberately not activated

The production worker registry does **not** register Bash/Python/browser/editor/process tools yet. The current repository does not have a completed approval service/approval persistence contract and deployed sandbox supervisor evidence. This respects `AGENTS.md` default-deny rules. The adapter is implemented and independently testable, but it is not represented as production-ready tool availability.

Browser isolation, browser DNS/SSRF supervisor, approval UI/API, and artifact handoff remain follow-up work.

## 6. Supabase reconciliation

Live schema inspection confirmed the existing columns needed for this increment:

- `agent_run_checkpoints`: `run_id`, `checkpoint_key`, `state jsonb`, `created_at`.
- `conversation_messages`: `conversation_id`, `user_id`, `role`, `content`, `run_id`, `token_input`, `token_output`, `metadata jsonb`.
- `partner_members`: `partner_id`, `user_id`, `role_key`, `location_id`, `status`.
- `partner_organizations`: `id`, `legal_name`, `display_name`, `status`.
- `partner_locations`: `partner_id`, `name`, `address jsonb`, `status`.

No database migration or destructive schema change was needed for this increment. The worker continues to use the existing server-only service-role boundary; frontend code does not receive a service-role credential.

## 7. Verification evidence

### Phase 04 regression run

[Phase 04 Sandbox Security Tests — run 42965739026](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739026)

| Job | Result |
|---|---:|
| Sandbox policy | 7 passed |
| Engine policy/runtime | 26 passed |
| Worker recovery/contracts | 15 passed |
| FastAPI auth/tenant contracts | 16 passed |

All four jobs passed.

### Frontend baseline

[Phase 00 Baseline Verification — run 42965739011](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739011) passed after the Partner tenant loading lint correction.

| Baseline gate | Result |
|---|---|
| ESLint | PASS — 0 errors, 3 existing `<img>` warnings |
| Frontend build | PASS |
| Server startup | PASS |
| Browser smoke | PASS at 360, 390, 768, 1024 and 1440 px; no page errors |
| API tests | PASS |
| Worker tests | PASS |

The previous lint defect was corrected in commit `b550329d9c9d1705b68cb2a7943c344e132d59d7`. Phase 00 UI/build revalidation for this increment is complete.

### Explicitly not tested

- Real LLM provider calls/API keys.
- Authenticated production user → worker → provider → Supabase E2E.
- Actual Docker container execution on a production worker host.
- Browser sandbox and browser network isolation.
- Production deployment or worker activation.

## 8. Remaining gates and next work

1. Finish Phase 04 upstream parity for the remaining agent/flow/tool domains, plus a durable approval/audit contract.
2. Complete Phase 06 API contract coverage for the remaining domains and OpenAPI review.
3. Complete Phase 07 outbox/event lifecycle, lease fencing, cancellation and crash-recovery proof under concurrent workers.
4. Complete Phase 08 provider routing, streaming, retry classification, tool metering and settlement for all supported provider adapters.
5. Complete Phase 09 remaining frontend journeys only where the corresponding server APIs are implemented; keep unsupported actions unavailable rather than simulated.
6. Phase 10 authenticated E2E remains blocked until the product owner authorizes real provider credentials and a safe integration environment.
7. Phase 11 release gate remains not started.

**Next execution target:** continue Phase 04 by completing the server-side tool approval/audit path and upstream tool/domain parity, then finish Phase 06–09 contracts. Do not enable production sandbox tools or worker execution until the corresponding gates pass.
