# MoreAI Implementation Phase Tracker

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 00 | Repository baseline & UI freeze | REVALIDATED — current UI build/lint/server/browser smoke PASS | [Phase 00 run 42965739011](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739011): lint 0 errors, build/server/browser PASS at 360/390/768/1024/1440 px; 3 existing image optimization warnings |
| 01 | Upstream source pin & provenance | COMPLETE | `dev_web_app` @ `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` |
| 02 | Monorepo backend workspace foundation | COMPLETE — foundation | `apps/api`, `apps/worker`, `engine`, `packages` |
| 03 | Complete upstream source copy | COMPLETE — hash verified | 111/111 matching Git blob SHA in `vendor/openmanusweb/` |
| 04 | Full backend integration & security hardening | IN PROGRESS — durable transcript/checkpoint recovery and restart resume implemented; upstream parity and approval/sandbox activation remain | [Phase 04 run 42965739026](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739026): sandbox 7, engine 26, worker 15, API 16 tests all PASS |
| 05 | Supabase schema reconciliation | COMPLETE — existing schema only; no reset/destructive DDL | Live columns verified for checkpoints, conversation messages, partner membership, organizations and locations; no migration needed |
| 06 | FastAPI core & OpenAPI contract | IN PROGRESS — Customer and Partner route groups now separated with server-side role/tenant enforcement | Customer context/conversation/run/SSE; Partner tenants/context/locations/members; legacy customer routes protected; API contract tests PASS |
| 07 | Worker & durable run lifecycle | IN PROGRESS — checkpoint restoration, run-scoped transcript persistence and restart replay implemented | `WorkerRpcClient.list_checkpoints`, `SupabaseConversationMemoryStore.load_run`, durable per-tool settled observation and restart recovery tests PASS |
| 08 | LLM/tool/workflow/orchestration integration | IN PROGRESS — configured provider fallback and metered reservation/settlement implemented; only approved existing chat-completion tool active | Ordered primary/fallback candidates; stream fallback only before first delta; engine tests PASS |
| 09 | Existing Frontend API Integration | IN PROGRESS — Customer Chat uses Customer API; Partner Portal uses live tenant context/locations and explicit tenant selection | Typed `customerApi`/`partnerApi`; demo partner data and fabricated analytics/QR/package claims removed; frontend baseline rerun pending |
| 10 | End-to-end integration verification | BLOCKED | No real-provider authenticated browser → worker → provider E2E; real keys intentionally deferred |
| 11 | Integration release gate | NOT STARTED | No production worker/sandbox activation or release until full parity and acceptance evidence |

## Direct-main execution policy

Implementation is being performed directly on `main` as explicitly requested by the product owner. No new branch is created and the existing historical Phase 04 branch/PR is not used as the work target. Changes are committed in small, reviewable commits; production deployment and worker activation remain prohibited until Phase 11 passes.

## Current Phase 04 next work

1. Wire the existing durable worker dispatcher to a policy-enforced OpenManus tool-call runtime (currently the worker factory still uses text-only `GatewayManusRuntime`).
2. Implement real adapters for catalog tools only where the required provider, storage, sandbox, approval and audit dependencies exist. Keep unavailable tools hidden and default-denied.
3. Implement short-term conversation/run memory persistence with owner/workspace isolation and restart recovery using verified existing Supabase schema; add long-term retrieval only after its consent, retention and deletion model is implemented.
4. Complete upstream agent/flow parity and connect isolated Bash/Python/browser/editor tools to actual sandbox supervisors with resource/network/secret boundaries.
5. Add integration, recovery, tenant-isolation and security tests, then update the capability map from test evidence.

Latest direct-main commits:
- `13f7353d1ed6252f1313f3d47a6ede159b7ed0b3` — hardened tool-call runtime and agent lifecycle.
- `2eda22e07efc38398080dba2c512eb5cef167bf0` — explicit cancelled/exhausted states.
- `11e724242c69d76b152fca7d96441e5ede2d2759` — tool-call runtime tests.
- `59acb70953c6cb6ca5e35cb641e403e4a41248f3` — pinned engine test dependencies.
- `e2eb64c147f2f4a8d5ad92d152c20a4d76e5b6ca` — Phase 04 engine tests in CI.

These commits are implementation increments, not Phase 04 acceptance. CI must pass and remaining integration gaps must be closed before this phase can be signed off.


## 2026-11-11 continuation notes

- Confirmed live Supabase columns for `conversations` and `conversation_messages`; both have RLS enabled. `conversation_messages.token_input` and `token_output` are NOT NULL. The worker memory insert was corrected to supply zero usage values for non-metered conversation-memory rows.
- Latest commits: `8bcec7a799ed1dac4587dc1d8fc9d933136820f2` removes the redundant Files loading state update that caused the baseline lint gate to fail; `713109f28705ab3dc28af25dabdf2eed79a87e8f` and `734be31ddd43636ea09d3ed16feac1f511154ac6` reconcile and test the required memory usage columns.
- Previous Phase 00 baseline run `42959465066`: build/server/browser smoke passed; lint failed only on the redundant setState-in-effect in `components/views/files-view.tsx`. The lint defect is fixed on main; a fresh baseline run is in progress.
- Current Phase 04 sandbox CI is re-running after the memory schema correction. Phase 04 and Phase 08 are still not accepted; Phase 09 UI separation has not started because backend foundations and authenticated E2E gates are not yet complete.


## 2026-11-11 durable OpenManus tool-call integration increment

- Added `engine/agents/durable_tool_runtime.py`: bounded OpenManus tool-call loop, structured function arguments, deterministic per-round request keys, durable round/tool intent/settlement checkpoints.
- Worker registry now registers this durable runtime as the Manus implementation; existing worker lease/heartbeat/cancel/checkpoint/finish lifecycle remains the execution owner.
- OpenAI-compatible provider adapter now accepts tool definitions and returns structured tool calls; metered gateway includes tool definitions in request hashing and passes them to the provider. Each model round uses the existing metered `complete` accounting path.
- Only `create_chat_completion` is currently registered in the tool registry. High-risk Bash/Python/browser/editor/process tools remain unavailable and default-denied pending sandbox supervisor + approval/audit wiring.
- Added continuation report `PHASE-04-08-09-INTEGRATION-CONTINUATION-20261111.md`.
- Not complete: provider candidate retry/failover, durable restoration of the full tool-call transcript across process restart, sandbox tool adapters, Customer/Mitra server-side route isolation, and authenticated E2E. Real provider/API-key E2E remains deferred by instruction.


## 2026-11-11 direct-main continuation — durable recovery, tenant isolation and provider failover

- Current implementation report: [PHASE-04-07-08-09-DURABLE-RECOVERY-TENANT-FAILOVER-20261111.md](./PHASE-04-07-08-09-DURABLE-RECOVERY-TENANT-FAILOVER-20261111.md).
- Durable worker restores `agent_run_checkpoints`, restores run-scoped conversation messages, resumes pending tool calls, reuses settled observations, and returns a checkpointed final output after restart.
- Worker process shutdown now leaves an interrupted lease recoverable; explicit user cancellation remains terminal.
- Customer and Partner API groups are separated. Active Partner membership resolves tenant and role on the server. Existing generic conversations, runs and artifacts routes are Customer-principal gated.
- Customer Chat and Partner Portal now use typed API clients. Partner tenant selection is constrained to active server-authorized memberships. Unsupported QR, package, analytics and onboarding actions are not simulated.
- Provider primary/fallback routes share one maximum-estimate reservation and settle against the selected provider. Streaming failover is allowed only before any delta is emitted.
- Python/Bash isolated Docker adapter and hardened runner are implemented, but production registration remains disabled until the approval/audit contract and deployed supervisor pass the AGENTS.md gate.
- Phase 04 CI run 42965739026: sandbox 7/7, engine 26/26, worker 15/15, API 16/16 — all green.
- Phase 00 run 42965739011: all baseline gates passed — lint 0 errors, build/server/browser smoke passed at 360/390/768/1024/1440; three non-blocking image optimization warnings remain.
- Real provider keys, authenticated production E2E and deployment remain deferred. Phases 04 and 06–09 remain in progress; Phase 10 blocked; Phase 11 not started.


### Latest direct-main commits for this increment

- `895253b7176f25ef76f1f0852376612f25c05d0d` — Partner tenant route authentication regression test.
- `2b28f2cd4ff9742be0cee2d9ce7c6f057ca21f32` — retain LLM reservation when streaming provider usage has been received.
- `d81eb1566f17fc90b598e5106bacdebe22700aab` — SSE checkpoint redaction regression test.
- `b3d7a827056c16ae1260acfbab7d9970fe7f51f3` — redact private tool arguments and observations from run events.
- `27253b21d6503bf33b74ae4bb47cc5805acdf80a` — partner portal API data binding and tenant selection.
- `9feb542cf3fc50320093266fb737110706a3d130` — server-authorized Partner tenant discovery route.
- `c4f649c83614824fec75b0097cd618d47ff1c4f4` — Customer Chat moved to dedicated Customer API.
