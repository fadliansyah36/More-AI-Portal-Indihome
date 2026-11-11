# MoreAI Implementation Phase Tracker

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 00 | Repository baseline & UI freeze | Revalidation required after latest direct-main backend commits | [Phase 00 workflow](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/workflows/phase00-baseline.yml) |
| 01 | Upstream source pin & provenance | COMPLETE | `dev_web_app` @ `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` |
| 02 | Monorepo backend workspace foundation | COMPLETE — foundation | `apps/api`, `apps/worker`, `engine`, `packages` |
| 03 | Complete upstream source copy | COMPLETE — hash verified | 111/111 matching Git blob SHA in `vendor/openmanusweb/` |
| 04 | Full backend integration & security hardening | IN PROGRESS — runtime/dispatcher hardening increment CI PASS; parity incomplete | [Phase 04 run 42959145125](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42959145125): engine-policy and sandbox-policy PASS; [Engine Contract Tests 42959145056](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42959145056): PASS. Full worker tool-call wiring, upstream flows/tools and durable memory pending |
| 05 | Supabase schema reconciliation | COMPLETE — existing migrations only; no reset/destructive DDL | Existing schema and additive migration history |
| 06 | FastAPI core & OpenAPI contract | IN PROGRESS — core domain API | Auth, identity, conversations, enqueue, catalog, run, cancel, events and SSE |
| 07 | Worker & durable run lifecycle | IN PROGRESS — worker dispatcher currently registers Manus text and Planning only | Durable claim/heartbeat/checkpoint/finish; worker disabled pending gates |
| 08 | LLM/tool/workflow/orchestration integration | IN PROGRESS — metering foundation | Gateway/provider contract and accounting; tool-call transport/handlers not fully wired |
| 09 | Existing Frontend API Integration | IN PROGRESS — chat and Files metadata partial | Other product modules pending; Customer/Mitra split not started |
| 10 | End-to-end integration verification | BLOCKED | No authenticated real-user worker E2E or complete runtime proof |
| 11 | Integration release gate | NOT STARTED | No merge/deployment until full parity and acceptance evidence |

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
