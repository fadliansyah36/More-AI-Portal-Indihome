# Customer Workspace API Production Recovery — 2026-11-12

## Scope

Focused only on restoring and completing the existing Customer frontend integration with FastAPI, OpenManus Engine/Worker and Supabase. Existing Customer UI/UX is protected. Browser, gateway, network and unrelated features are out of scope for this increment.

## Production evidence

- Customer screenshot shows Tasks & Workflow with `Failed to fetch`.
- Frontend Vercel project has `NEXT_PUBLIC_MOREAI_API_URL=https://more-ai-api-more-ai.vercel.app`; the API origin is configured rather than empty.
- Frontend CORS origin list includes `https://moreai.web.id` and `https://www.moreai.web.id`.
- Live API checks to `/health` and `/ready` on the configured API origin both returned HTTP 500 `FUNCTION_INVOCATION_FAILED`. This is the primary confirmed reason the Customer UI cannot fetch run data.
- API Vercel deployment `dpl_B9jdfxtavvR3ySqqssdoZuqpWe6L` is marked READY at build/deployment level, but the runtime function fails when invoked.
- Vercel build events show the API project building from the monorepo root (`entrypoint: .`) while Python metadata is discovered at `apps/api/pyproject.toml`. The Python entrypoint is nested at `apps/api/api/index.py`, and imports `app.main` plus root-level `engine` modules. The function entrypoint now resolves API and repository roots explicitly before importing FastAPI.
- The Vercel project root directory was aligned to `apps/api` with outside-root source inclusion enabled, so the API project builds from its actual Python workspace while retaining the root-level engine dependency.
- The backend feature flag `MOREAI_AGENT_EXECUTION_ENABLED=false` remains intentionally disabled. Do not enable it until a live worker, provider route, quota/credit policy and durable run acceptance are proven. A working HTTP API alone is not evidence that agent jobs execute.

## Changes

- Updated `apps/api/api/index.py` to locate the API workspace and monorepo engine root before importing `app.main`, independent of whether the Vercel runtime preserves the monorepo path or uses the API workspace as root.
- Vercel API project settings updated: root directory `apps/api`, framework `fastapi`, and source files outside root enabled.
- Fixed Customer run API contract drift: the client now lists/gets/streams/reads steps through `/api/v1/customer/agent-runs/*`; added owner-authenticated customer cancellation endpoint and aligned the client path. Added an API route-registration contract test for the full customer run lifecycle.
- Wired the existing Tasks “Tambah Tugas” action to the existing authenticated Chat → FastAPI → durable Agent Run flow. No local-only task or fake record is created; the existing screen and visual design are preserved.
- No frontend visual redesign. Tasks & Workflow continues to display persisted Agent Run records from FastAPI/Supabase.

## Verification

- GitHub Actions API unit tests passed on commit `b9426254f8fb8b143696edec36a46d0666e6b920`.
- Worker unit tests passed on the same run.
- Frontend lint and build passed on that run; browser smoke was still running when this report was authored.
- Latest API code commit: `17453150da788481500b36c0683e4e7db750aab6`.
- Production re-deployment attempt for the API was rejected by Vercel with HTTP 402 `api-deployments-free-per-day` (100/day limit). Therefore the new entrypoint fix has NOT yet been deployed or verified against live `/health`.

## Remaining acceptance gates (do not mark complete)

1. Deploy the API project from the latest main commit after Vercel's deployment quota resets or an authorized Git deployment trigger becomes available.
2. Verify `/health` returns 200 and `/ready` reports the expected Supabase Auth/Data readiness without exposing secrets.
3. Verify authenticated Customer calls: context, conversations, agent runs, run details, steps, logs, thinking, progress, SSE replay, cancellation, approvals, workspace list/files/version/download, artifacts and knowledge.
4. Run an authenticated Customer browser journey on the production frontend and prove API requests return real Supabase-backed records.
5. Deploy/activate the durable worker and configured provider route only after their prerequisites are satisfied; then run Customer chat -> queued run -> worker -> engine -> provider/tool -> Supabase persistence -> event stream -> UI E2E.
6. Keep Phase 09 IN PROGRESS and Phase 10/11 NOT ACCEPTED until all evidence above exists.

## Next execution

Continue Phase 09 Customer integration from the API boundary outward: first restore live FastAPI runtime, then verify every Customer screen against its actual endpoint contract, fix route/schema mismatches and data loading behavior without redesigning screens. Only after API health is restored proceed to authenticated full Customer workflow E2E.
