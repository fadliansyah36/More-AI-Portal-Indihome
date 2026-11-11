# Phase 04 — Full Backend Integration & Security Hardening (Continuation)

**Date:** 11 November 2026  
**Branch:** `phase-04/full-backend-parity-hardening`  
**Base:** `main` at `19679b46595d4add98196600a6f91cdae73e02d6`  
**Upstream:** `YunQiAI/OpenManusWeb`, pinned `dev_web_app@3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`  
**Supabase:** `uunfgimtokhucegqbpce`  
**Status:** IN PROGRESS — no phase sign-off, no production deployment, no worker/provider enablement.

## 1. Scope and non-negotiable behavior

This continuation follows root `AGENTS.md`, Master PRD and the existing Phase 04 report. It does not replace the upstream engine with a simple Manus prompt loop. The complete upstream source remains immutable under `vendor/openmanusweb`; production adapters belong in `engine/`, `apps/api/`, `apps/worker/` and `apps/sandbox/`.

The required execution path remains:

```text
Existing MoreAI frontend
  -> authenticated FastAPI
  -> OpenManus-compatible agent / ReAct / SWE / ToolCall / Flow / Planning / Memory
  -> policy-enforced tool dispatcher and durable worker
  -> FastAPI repository / data services
  -> Supabase PostgreSQL / Auth / Storage / Realtime
```

All client business data must go through FastAPI. Supabase browser access remains Auth lifecycle only. No real provider/API-key test was initiated.

## 2. Current verified baseline

GitHub Actions run [42949687249](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42949687249) was inspected at job/step level:
- API tests: PASS.
- Worker tests: PASS.
- Next production build: PASS.
- Next server startup: PASS.
- Browser smoke: PASS at 360, 390, 768, 1024 and 1440 px; no page errors reported.
- Frontend lint: FAIL, one error in `components/views/files-view.tsx:56` because `setLoading(true)` was called synchronously inside a mount effect. The same file initializes loading state to true, so this redundant update was removed on this branch. The 3 image optimization warnings remain non-blocking.
- The previous Chat TSX parse issue is not the cause of this latest run.

Branch CI must rerun before calling the frontend baseline green.

## 3. Code changes in this continuation

### 3.1 FilesView lint correction
- Removed the redundant synchronous `setLoading(true)` call from the initial data-loading effect.
- Kept initial loading state true, API fetch, cancellation guard, error handling, and real empty state unchanged.
- No layout, colors, typography, or interaction changes.

### 3.2 High-risk tool policy hardening
Updated `engine/tools/policy.py`:
- Tool must first be explicitly enabled.
- Bash, Python execution, and browser automation require a registered isolated-runtime capability.
- High-risk tools also require explicit approval.
- Approval alone cannot bypass isolation readiness.
- Non-high-risk tools remain disabled until explicitly enabled and approved.
- No tool is enabled by default.

Added tests covering:
- Approval without isolated runtime is denied.
- Isolated runtime without approval is denied.
- Only both gates together can pass.

Updated Phase 04 workflow to run `engine/tests` alongside sandbox security tests and to trigger on engine changes as well as sandbox changes.

These are policy/test improvements only. They do not claim that a production sandbox or browser supervisor is deployed or wired to the dispatcher.

## 4. Backend parity — remaining work (not complete)

| Capability | Current state | Required production proof |
|---|---|---|
| Manus | Adapted text runtime | Tool-aware runtime and durable context lifecycle |
| ReAct | Upstream source preserved; production adapter incomplete | Thought/action/observation lifecycle using safe public progress only |
| ToolCall | Source and catalog preserved; dispatcher wiring incomplete | Provider tool-call parsing, validated arguments, approval, handler invocation, tool result round-trip |
| SWE | Not registered | Workspace-bound agent with sandboxed tools and checkpoints |
| Planning | Adapted durable Planning runtime | Full FlowFactory/PlanningFlow semantics, recovery and dependency replay |
| Other Flow types | Factory contract only / incomplete | Every upstream flow mapped to an implementation or approved blocker |
| LLM wrapper | Metered OpenAI-compatible adapter | Tool-call, multimodal/capability parity, retry/fallback and provider tests |
| Prompts/schemas | Initial MoreAI prompts and catalog schemas | File-by-file upstream prompt/schema comparison and tests |
| Short-term memory | In-process `AgentMemory` model exists; durable session integration incomplete | Persist and restore context by owner/workspace/run with retention policy |
| Long-term memory | Not production integrated | User-consented PostgreSQL/pgvector retrieval, ownership, tenant isolation, deletion/export controls |
| Session/log lifecycle | Durable runs/checkpoints/SSE foundation | Session lifecycle, replay, log redaction, terminal states and accepted ADR parity |
| Bash/Python | Docker isolation primitives, not wired to worker | Deployed digest-pinned runner, non-root, no network, resource limits, kill/reap tests |
| Browser | URL/DNS/download policy primitives only | Isolated browser supervisor and network-level DNS pinning for redirects/requests |
| File saver/editor | Catalog only / no released handler | Owner-scoped workspace and Storage, traversal defense, checksum, approval |
| Google search | Catalog only / provider unavailable | Approved provider adapter, source attribution, bounded egress |
| Terminate | Cancellation API/worker lifecycle exists | Tool call bound only to current run, audited and idempotent |

The upstream capability map must remain the source of truth for all 111 preserved source files and backend modules. Catalog entries and schemas are not evidence of runnable handlers.

## 5. Frontend integration — remaining work

The Chat UI and Files metadata view are the only identified real-data integration surfaces at this checkpoint. Upload/download/share are not claimed complete.

The following modules still require exact schema/API mapping and live-data integration:
- Dashboard and Analytics
- Agent Studio
- Research
- Code / sandbox
- Tasks / workflow
- Wallet, credit ledger, packages and entitlements
- Partner Portal and network access
- Super Admin, audit and configuration
- Remaining customer/profile/settings screens

Do not seed fake records to make empty states look populated. Preserve existing UI and use truthful loading, empty, error and unavailable states. UI edits require baseline and after screenshots.

## 6. Supabase security advisor review

Read-only advisors on 11 November 2026 reported:
- Four RLS-enabled public tables without policies: `network_gateway_nonces`, `network_verification_method_catalog`, `partner_access_code_redemptions`, `partner_access_codes`. They remain client-default-deny; do not add broad policies without reviewing each ownership and server-only access contract.
- Leaked password protection is disabled in Auth settings. This is a dashboard configuration item and was not changed.
- 52 unindexed foreign-key findings were returned by performance advisor. Index changes require workload/EXPLAIN review; no DDL was applied.
- No Supabase schema changes were made in this continuation.

## 7. Safety / release gates

- Worker and agent execution remain disabled.
- No provider secrets or fake provider/model/wallet/entitlement data were added.
- No real LLM call, production tool execution, browser automation, or sandbox Docker execution was performed.
- No destructive SQL, RLS relaxation, migration, deployment, or main-branch write was performed.
- A full authenticated E2E requires a real approved test principal and owner-approved provider/billing configuration. These are prerequisites, not permission to bypass fail-closed controls.

## 8. Next execution sequence

1. Obtain branch CI results for FilesView lint correction and engine policy tests.
2. Integrate OpenManus ReAct/ToolCall/SWE against the actual metered LLM tool-call contract; do not invent a second orchestration loop.
3. Wire tool registry -> dispatcher -> sandbox/browser supervisor -> durable worker with approval/audit and result persistence.
4. Complete upstream FlowFactory/PlanningFlow and session/memory/log lifecycle parity.
5. Implement durable short-term and consent-based long-term memory adapters using verified schema and pgvector.
6. Implement real API endpoints and existing frontend adapters for every listed module; remove demo/hardcoded/simulated data without changing UI.
7. Add API contract, tenant isolation, RLS, sandbox, approval, replay, cancellation, retry and artifact tests.
8. Only after the above, run authenticated E2E with approved provider configuration and submit the full Phase 04 sign-off evidence.

**Phase 04 remains IN PROGRESS.** This continuation is not a declaration of full parity.

## 9. Memory schema discovery (read-only, 11 November 2026)

A direct read-only query against the canonical Supabase project confirmed:
- `pgcrypto` is installed.
- The `vector` extension is not currently installed in the queried project.
- No public table named for memory, embeddings or knowledge was found.
- Existing durable structures include `conversations`, `conversation_messages`, `agent_runs`, `agent_run_steps`, `agent_run_checkpoints`, `agent_run_events` and `artifacts`.

Therefore, current in-process `AgentMemory` and run checkpoints are not a long-term memory service. Semantic memory cannot be claimed implemented until an approved forward-only migration enables the required vector capability, introduces owner/workspace/consent-scoped memory records and indexes, and tests retrieval/retention/deletion boundaries. No extension, table, or policy was changed during this inspection.

## 10. CI results after policy and lint fixes

- [Phase 04 CI run 42952996506](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42952996506): PASS — both `engine-policy` and `sandbox-policy` jobs completed successfully on the latest code commit `9e383bd369bd55529de7f93bf884620a9c81f847`.
- [Phase 00 baseline run 42952996532](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42952996532): queued at last inspection. The earlier run on parent commit showed lint PASS after the FilesView fix, but build was cancelled when a newer PR commit superseded it. Wait for the latest SHA baseline run before sign-off.
- API and Worker jobs passed on the preceding PR commit; latest SHA baseline will rerun them as well.

This verifies only the policy tests and current baseline pipeline. It does not verify full upstream agent/tool/memory parity.
