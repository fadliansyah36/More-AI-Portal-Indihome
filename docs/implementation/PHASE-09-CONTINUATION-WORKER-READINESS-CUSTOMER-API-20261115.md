# Phase 09 Continuation — Worker Readiness & Customer API Corrections

Date: 2026-11-15
Branch: `main`
Repository: `fadliansyah36/More-AI-Portal-Indihome`

## Scope

Source-level continuation of Phase 09. Work was performed directly on `main`. No staging environment or functional tests were used.

## Implemented

- Worker health endpoint now distinguishes liveness (`GET /health`) from readiness (`GET /ready`). Readiness returns 503 until startup gates and the durable event publisher are initialized.
- Worker capability publication now runs in an independent heartbeat task. Long-running Agent Runs no longer suspend capability heartbeats. If capability publication fails, readiness becomes false and the worker pauses claiming new runs until the heartbeat recovers.
- Worker Docker image now has a readiness-based `HEALTHCHECK` on port 8081. Worker README documents the persistent-container deployment contract, no scale-to-zero requirement, private health port, and the boundary between readiness and end-to-end provider acceptance.
- Google OAuth reauthorization now decrypts the prior credential using the ciphertext's embedded key version, preserving the refresh token across key rotations. Connection audit metadata records the active key version instead of a hard-coded v1.
- Removed duplicate registration of `browser_sessions.router` in FastAPI.

## Commits

- `055fff1e30f13ed204b2223b6adbc6ed2a0f09ca` — worker liveness/readiness separation.
- `b38eab3529eb3145a9696a08083546f490c7071d` — persistent worker deployment contract.
- `560f4a7f7877924e5bf6f7bdd155295e80a9a5e2` — Docker readiness healthcheck.
- `b06b7567758bea6563e2db1386b28b8aa957bae8` — independent capability heartbeat and fail-closed run claiming.
- `be8f147d80656e4359b9ed0203e861efbc0a9384` — heartbeat-backed readiness documentation.
- `bde848a366a7befc9d85caf622466ea6759b89d8` — Google credential key-rotation correction.
- `548b25475e8df7a159f8c1e888a0a1982986f33b` — duplicate FastAPI router registration removal.

## Remaining blockers

1. No persistent worker host is connected in this execution context. Vercel is used for the frontend/API request boundary and is not a persistent worker supervisor. The worker has not been deployed.
2. No worker heartbeat rows, enabled provider/model records, provider credentials, model price/credit conversion, or worker secret injection are present in the canonical production configuration. `MOREAI_AGENT_EXECUTION_ENABLED` remains false.
3. Provider routing has a source/database contract mismatch: OpenManus calls task types `chat` and `planning`, while the current admin API schema and `moreai_admin_mutate_llm_route` procedure only accept `general`. This must be corrected in a forward-only migration and API contract before provider onboarding can be considered complete.
4. Provider registry configuration currently has no supported safe path for configuring the OpenAI-compatible `base_url` and worker secret environment-variable reference. Secret values must remain in the persistent worker host's secret manager, never in GitHub, browser code, or ordinary database config.
5. Customer actions that depend on real payment, subscription, support, OTP, or captive-gateway providers remain fail-closed because their external provider contracts and credentials are not supplied.
6. OpenFuse Browser/Computer parity is intentionally not started until worker/provider readiness and the remaining Customer dashboard API contract closure are completed.

## Production and verification boundary

- GitHub source commits above are on `main`.
- No Supabase schema migration was applied in this increment.
- No Vercel deployment was attempted. The latest API production deployment remains behind current `main`; earlier API deployment attempts were canceled after the Vercel daily deployment quota was exhausted. Frontend deployment status is unchanged.
- No tests, lint, typecheck, build, browser/API/worker execution, provider calls, staging, or E2E verification were performed, per owner instruction.
- These changes do not complete Phase 09 and do not constitute Phase 10/11 acceptance.

## Next work package

Continue **Phase 09 — Durable Worker & Provider Readiness + Customer Dashboard API Closure**:
1. Correct the `chat`/`planning` route contract with a forward-only Supabase migration and matching FastAPI contract.
2. Add safe provider configuration/secret-reference lifecycle and worker-side provider readiness reporting.
3. Connect a persistent container host, inject secrets securely, and deploy the worker without enabling execution until all readiness gates pass.
4. Continue action-to-FastAPI closure for the remaining Customer dashboard surfaces.

Only after these are complete should work proceed to **OpenFuse Browser/Computer parity and the remaining dashboard action closure**. Phase 10 verification and Phase 11 release gate remain unaccepted and require separate authorization.
