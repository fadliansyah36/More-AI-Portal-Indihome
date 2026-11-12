# Phase 04 / 06 / 09 — Session, Workspace Atomicity & Customer Dashboard Integration (2026-11-13)

## Scope

- Repository: fadliansyah36/More-AI-Portal-Indihome
- Branch: main
- Target: strengthen OpenManus session lifecycle, make workspace snapshot write-back atomic, and connect existing Customer task/home surfaces to persisted FastAPI data without redesign.

## Phase 04 — Session lifecycle and workspace consistency

- Added conversation-scoped cancellation at `POST /api/v1/conversations/{conversation_id}/sessions/{run_id}/cancel`. It verifies both conversation and run ownership before invoking the durable worker cancellation RPC.
- Bounded WebSocket/SSE replay cursors to non-negative PostgreSQL bigint values; malformed and out-of-range values are rejected. Event `after` query parameters use the same upper bound.
- Added `20261113120000_moreai_workspace_atomic_execution_commit.sql`: server-only idempotency ledger plus `moreai_workspace_commit_execution_snapshot`. It validates worker lease, run/user/workspace binding, active workspace membership, private Storage bucket, safe unique paths, expected versions, object existence, SHA-256 and size limits. All changed/new file metadata and soft deletes commit in one PostgreSQL transaction.
- Workspace worker uploads immutable version objects before the transaction and sends the complete changes/deletes set under a deterministic SHA-256 operation key. Repeated requests return the previously committed result.
- Existing workspace version-history trigger is preserved; delete version metadata is recorded inside the same transaction.
- Limitation: a failed metadata transaction may leave unreferenced uploaded Storage objects. Garbage collection is still outstanding. Migration is committed but not applied to Supabase.

## Phase 06 — Customer API history contract

- Customer agent-run history now supports stable keyset cursor pagination ordered by `created_at DESC, id DESC`, returning the existing array payload and exposing `X-Next-Cursor` / `X-Pagination-Mode` headers.
- Legacy `before` timestamp cursor remains supported for existing clients; callers may use either `cursor` or `before`, not both.

## Phase 09 — Existing Customer dashboard

- Existing Tasks view now consumes the cursor-paginated Customer Agent Run history API.
- Task titles use the persisted run prompt where present, falling back to the run ID only when prompt metadata is unavailable.
- Added a load-previous-tasks action that appends subsequent pages while deduplicating run IDs. Existing page structure and styling are retained.
- Existing Home dashboard now loads recent Agent Runs, wallet balance and active Partner entitlement through authenticated Customer API calls.
- Removed the fabricated “100K Poin AI” figure and hardcoded “Strategi Marketing Coffee Shop / 4 dari 6 langkah / 67%” task. Home now reflects actual account data and shows an empty state when no runs exist.
- Removed unsupported static claims about five fixed specialist agents, 100 Mbps / five connected devices, and simulated captive login; copy now describes backend-backed capabilities without fabricated metrics.
- UI scope was limited to data wiring and truthful content; no layout, navigation or styling redesign was performed.
- Screenshot evidence was not captured because the owner explicitly prohibited browser/runtime testing in this implementation cycle. The UI gate therefore has no screenshot-based regression evidence yet.

## Changed files

- `apps/api/app/routers/agent_runs.py`
- `apps/api/app/routers/conversations.py`
- `apps/api/app/routers/customer.py`
- `apps/worker/app/client.py`
- `engine/tools/workspace.py`
- `supabase/migrations/20261113120000_moreai_workspace_atomic_execution_commit.sql`
- `lib/api/client.ts`
- `components/views/tasks-view.tsx`
- `components/views/home-view.tsx`
- `apps/sandbox/README.md`
- `docs/implementation/PHASE-TRACKER.md`
- `docs/implementation/openmanus-backend-capability-map.json`

## Source commits

- `59c70b792f458fa07e06d0ef2c4fc55a3e954f4b` — conversation-scoped session cancellation
- `3678ff6d39c2a7890e84242e747de3d02924719a` — strict WebSocket/SSE replay cursor
- `cb0181fe1cb7032caf52250c8d7a8aba273978d5` — bigint bounds for run event query
- `eaae18f24fc0ccd0db5481e96d7f6bdd309050b8` — bigint bounds for conversation session event query
- `7a49e3eaa8e1ee6fb58e9bb2adf3be838a993dba` — atomic workspace commit migration
- `b8a4b68e326a2f8e3da6462b1faf9bbc1955ee66` — worker RPC client
- `62721184ae397280a060a6ebaa45e6015b0b55b5` — atomic workspace write-back adapter
- `4b7983d2a73829be9893f62b09ad710263f658ee` — reject null batch arrays
- `2f3048317bdc21ff7f55b7846b23d6f4e4eb3091` — keyset pagination for Customer agent-run history
- `4ff60e24e371d2a5cf79ec5ca9132d97d3292c7e` — typed client page helper for Customer runs
- `2b9b4221e2483f4f8749e0de8237dc846120e330` — Tasks view persisted prompt and pagination
- `4bc6460c981b0d9f0ef8ef6a099bdbf1d185f111` — Home view real run/wallet/entitlement data

## Verification restrictions

Per instruction, no tests, lint, typecheck, build, browser/API probes, Docker build, provider calls, staging, deployment, Supabase migration or live database mutation were performed. All changes are committed source code only; runtime success is not claimed.

## Remaining work and next phase

1. Phase 04 remains IN PROGRESS: complete remaining upstream server/session parity, persistent session log/thinking compatibility, browser download scanning/quarantine, supervisor deployment contract, and Storage orphan-object cleanup.
2. Phase 06 remains IN PROGRESS: route-wide Pydantic response models, consistent authorization and error contracts, idempotency for all side-effecting mutations, cursor pagination across remaining route families, and OpenAPI parity.
3. Phase 07 remains IN PROGRESS: recovery/retry/cancellation/heartbeat/checkpoint/outbox lifecycle coverage and durable state reconciliation.
4. Phase 08 remains IN PROGRESS: all upstream agent types, provider/model routing, tool adapters, orchestration, memory and RAG.
5. Phase 09 remains IN PROGRESS: integrate remaining Customer dashboard screens and actions to real API contracts, preserving the existing UI. Prioritize account, profile, notifications, artifacts/workspace, benefits/wallet, network sessions and the remaining agent actions.
6. Phase 10/11 remain blocked by the explicit no-testing/no-staging constraint and are not claimed complete.

- Follow-up UI truthfulness fix: Home distinguishes an unavailable Agent Run API response from a successfully loaded empty history, rather than presenting an API failure as “no runs”. Commit: `9b5f59c10dafdeffdb16d95d11892ef9459bfe4b`.
