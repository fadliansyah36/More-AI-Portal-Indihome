# Direct-main Integration Report — Durable Planning & Workflow API
Date: 2026-11-11

## Scope and execution constraints
- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Target: existing `main` branch. No branch was created.
- Existing Customer and Partner UI hierarchy, navigation, styling and routes were not changed in this increment.
- The product owner requested skipping real/live testing. No tests, lint, typecheck, build, browser automation, provider calls, database writes/migrations, deployment or worker activation were performed for this increment.
- Consequently, this report records committed source changes only. It does not claim runtime correctness, security certification, Phase completion or production availability.

## Baseline and source inspection
- Re-read `AGENTS.md` before editing.
- Inspected current `engine/agents/durable_tool_runtime.py`, `engine/tools/registry.py`, `engine/tools/catalog.py`, `engine/tools/policy.py`, `apps/worker/app/registry_factory.py`, `apps/worker/app/plan_store.py`, `apps/api/app/routers/customer.py`, `lib/api/client.ts`, and the capability map.
- Confirmed the worker's Manus runtime previously registered chat completion and optional gated Bash/Python only. Planning was implemented as a separate agent runtime and durable plan store, but the OpenManus planning tool was not exposed through the central tool registry.
- Confirmed Browser remains default-deny because no socket-level egress enforcement is deployed. Storage bucket/path configuration is not established, so artifact save/download is not enabled.

## Changes committed directly to main
1. `284001641d963a2213c653e4ac6477c58ab2ac9b` — `DurableOpenManusRuntime` now accepts a durable plan store, enables the planning tool only when that store is injected, and registers create/get/mark_step through `PolicyEnforcedToolRegistry`.
2. `e373ef1258e9cff80812b9009916eac7d73f1222` — worker registry factory injects its existing `SupabasePlanStore` into the Manus runtime.
3. `b207f30eb987e802135fe7b7720a86fe1da48a32` — provider tool-call parsing now fails closed for malformed shapes, invalid/duplicate IDs, invalid tool names, oversized/non-JSON arguments and non-object argument payloads; malformed calls are no longer silently dropped.
4. `19d14df45cced74d8ed36b64fb94be082f71ea86` — added `GET /api/v1/customer/agent-runs/{run_id}/steps`; parent run ownership is verified before reading persisted step records.
5. `32fd349cc8952a469d09586cec45064cb0080fdf` — added typed `CustomerWorkflowStep` and `customerApi.getRunSteps` to the existing API client.
6. `92e4373b0fcd74008fbc0b77178079d764c621d4` — updated source-to-target OpenManus capability map with the implemented planning tool and strict parser state.
7. `ab0daa44c7e6a3337caa00a14b0c1c7a744dc76f` — updated Phase Tracker to record the durable planning tool and workflow step API while retaining phases as IN PROGRESS.

## Data flow added
- Customer sends a message through the existing typed FastAPI client.
- Existing enqueue RPC creates the durable agent run.
- Worker claims the run and builds the AgentRegistry.
- Manus runtime receives the same SupabasePlanStore used by PlanningAgentRuntime.
- Model tool definitions are derived from the policy-enforced registry; planning is exposed only when the durable store is configured.
- Planning create/get/mark_step commands operate on the current run ID and persist through the existing `agent_run_steps` store.
- Customer workflow-step API first resolves the authenticated Customer principal and verifies ownership of the parent `agent_runs` record, then returns only that run's step records.
- Existing frontend API client now has a typed method for consuming that endpoint. No UI was changed to consume it yet.

## Security and correctness boundaries
- Planning tool does not receive a caller-supplied run ID; it is bound to the active worker run ID.
- Planning commands continue through the common registry, schema validation, policy and handler timeout.
- Provider-generated tool calls are rejected if malformed rather than silently converted into a no-tool response.
- Browser, Bash/Python and external network tools remain disabled unless their explicit runtime and security gates are configured.
- No service-role secret, provider credential or storage secret was added to source.
- No Supabase schema changes were made.

## Remaining work — not complete
### OpenManus backend parity
- Port complete upstream Flow lifecycle and FlowFactory semantics into durable run-scoped orchestration.
- Complete upstream server/session/stream/WebSocket behavior using FastAPI/SSE where appropriate.
- Finish structured tenant-safe logging, log parser/monitor and tracker parity.
- Implement safe Search provider adapter with secret references, source attribution and outbound egress policy.
- Implement artifact storage adapter only after canonical bucket/path and Storage policies are provisioned.
- Implement workspace file editor and SWE agent only with isolated per-run workspace and path traversal protection.
- Browser automation remains blocked until isolated browser supervisor and socket-level DNS/IP/egress enforcement exist.
- Bash/Python remain disabled until supervisor deployment and security release gate.

### Customer frontend/API
- Bind workflow step endpoint into the existing Workflow screen only after UI change gate (baseline screenshots and after screenshots) is satisfied.
- Complete account/profile mutations, notification center/preferences, file upload/download, artifact lifecycle, search history, and additional PRD domains.
- Preserve empty/error states; do not substitute demo data.

### Partner frontend/API
- Complete network/Wi-Fi provisioning, captive portal configuration, voucher/package management, campaign mutation, reward settlement, analytics and member lifecycle with tenant/location scope and idempotency.
- Unsupported operations must remain visibly unavailable, not simulated.

### Super Admin governance
- Implement permission-specific mutations only after exact role/permission schema and audit log schema are inspected.
- Add immutable audit records and idempotency to every privileged mutation.
- Current read-only workspace is not a completed governance surface.

### Release
- Phase 10 and Phase 11 remain open.
- Vercel quota, production deployment, real provider calls and production worker activation remain deferred by user instruction.
- No claim of production readiness or live integration is made.

## Next implementation phase
Continue Phase 04/08: complete durable Flow orchestration and upstream backend parity, then implement isolated workspace and artifact storage contracts. In parallel, continue Phase 06/09 API domain coverage, then connect the existing UI with minimal typed-client adapters. Do not advance Phase 10/11 or declare Phase 04/06/07/08/09 complete until their evidence gates are explicitly authorized and satisfied.
