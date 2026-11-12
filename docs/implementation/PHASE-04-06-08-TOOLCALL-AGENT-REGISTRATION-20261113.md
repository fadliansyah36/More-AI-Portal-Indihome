# Phase 04 / 06 / 08 — OpenManus ToolCall Agent Registration Increment

Date: 2026-11-13
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main
Scope: expose the concrete upstream OpenManus ToolCallAgent through the durable MoreAI runtime without enabling abstract ReActAgent or bypassing tool policy.

## Source inspection
- Read repository AGENTS.md and Master PRD v1.2.
- Inspected upstream snapshot classes `Manus`, `ReActAgent`, `ToolCallAgent`, `SWEAgent`, and `PlanningAgent`.
- ReActAgent is abstract; ToolCallAgent is a concrete base implementation. The existing production registry had Manus and Planning, plus gated SWE, but did not register ToolCall.
- Existing durable runtime already owns policy-enforced tool invocation, approval, checkpoints, memory, metering and event publication. This increment reuses that boundary rather than instantiating upstream process-local tool objects.

## Implemented on main
1. `apps/worker/app/registry_factory.py`
   - Registers `toolcall` as a separate durable runtime using the adapted upstream ToolCall system prompt.
   - Shares only the configured, policy-enforced MoreAI adapters and durable services; does not expose upstream unisolated Bash/Python/browser tools.
2. `apps/api/app/routers/conversations.py`
   - Adds `toolcall` to the typed `agent_key` request contract.
3. `apps/api/app/routers/catalog.py`
   - Includes `toolcall` in the set of production runtime keys that may be advertised when a matching enabled agent definition exists.
4. `supabase/migrations/20261113100000_moreai_enable_toolcall_agent.sql`
   - Replaces the enqueue RPC definition with the same ownership/idempotency contract while allowing `toolcall` as an agent key.
   - Preserves service-role-only execution grants.
   - Migration is committed but NOT applied to Supabase.

## Commits
- Worker registry: `caf9808916ffc2d6d8792057b62eb8bb1d980a00`
- API contract: `da1381b964826df23cc0ebec500b9db9946bc989`
- Catalog: `53a658ec0026ec09c64989ca6a0038a65bcb3a07`
- Migration: `ac369092d63a284a9b3fed25820ff01e34849d7e`
- Capability map: `1d72c3c27373137d79c64128d20841b1744c5410`.

## Safety / limitations
- No live database mutation, migration apply, provider calls, worker activation, staging, deployment, tests, lint, typecheck, build or browser/API runtime probes were performed.
- Until the migration is applied through the approved schema workflow, API requests selecting `toolcall` may be rejected by the deployed enqueue RPC. Do not advertise this as production-ready.
- ToolCallAgent is now wired as a distinct prompt/runtime mode, but upstream per-agent defaults and every upstream tool are not fully reproduced. Unsafe upstream tools remain unavailable unless implemented through the isolated, approval-gated MoreAI adapters.
- SWE remains separately gated on isolated sandbox activation. ReActAgent itself is abstract and is not exposed as a selectable agent.

## Phase status
- Phase 04: IN PROGRESS.
- Phase 06: IN PROGRESS.
- Phase 07: IN PROGRESS.
- Phase 08: IN PROGRESS.
- Phase 09: IN PROGRESS.
- No phase acceptance is claimed.
