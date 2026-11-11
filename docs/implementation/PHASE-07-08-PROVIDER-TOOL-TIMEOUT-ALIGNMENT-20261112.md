# MoreAI — Provider and Durable Tool Timeout Alignment

Date: 2026-11-12  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Scope: Phase 07/08 source implementation; no runtime or release verification.

## Changes

### Durable tool deadline accuracy

`engine/agents/durable_tool_runtime.py` now computes the effective deadline as the lower of:
- `MOREAI_TOOL_TIMEOUT_SECONDS` (worker-wide safety ceiling, default 120 seconds, 1–1800 accepted); and
- the canonical OpenManus tool catalog's per-tool timeout (for example, Search 30s, Browser 60s, metered completion 90s).

The effective deadline is applied to the outer cancellation/deadline race and is persisted in the timeout observation. This avoids reporting the worker-wide ceiling when the stricter catalog deadline actually expired.

Commit: `26b0ae6b7795f08c7312e5439de4ea211a0169a7`.

### Provider adapter timeout

`engine/llm/providers/openai_compatible.py` now reads `MOREAI_PROVIDER_TIMEOUT_SECONDS` for both non-streaming completion and streaming requests. Default: 90 seconds; valid range: 1–600 seconds. Invalid configuration fails closed. HTTP transport/timeouts continue to be classified as retryable provider availability errors, allowing route fallback under the gateway's existing rule (stream fallback only before any delta has been emitted).

Commit: `1468c202be284c8d02e51dd9de1e600bdba515d8`.

Environment documentation commit: `2b3084455cd6d59acaacb4edcc5930dfd9cda301`.

Phase tracker commit: `5352552b8920659c9f6963dd9069333838f049b8`.

## Not completed by this increment

- Full upstream Flow lifecycle and OpenManus server/session/WebSocket parity remain open.
- Approval pause/resume exists in the durable run path but has not been runtime-verified for approval/denial/expiry/recovery races.
- Lease fencing, outbox replay and client event gap recovery still require acceptance evidence.
- Provider fallback has not been exercised against real providers; retry/backoff/circuit-breaker parity remains incomplete.
- Memory/RAG and the full upstream tool catalog/handlers remain incomplete; high-risk browser/Bash/Python remain gated.
- Phase 05/06 schema and FastAPI contracts, Phase 09 customer/partner/admin integration remain open.
- Phase 10 E2E verification remains blocked and Phase 11 release gate has not started.

## Verification and safety boundary

No tests, lint, typecheck, build, live provider call, worker execution, Supabase migration apply, browser QA, staging, production operation or deployment were performed. No passing test, runtime readiness or release acceptance is claimed. High-risk tool activation remains disabled until its isolated supervisor, network controls, approval path and release gate are proven.
