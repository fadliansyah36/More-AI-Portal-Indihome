# Public Auth Navigation Isolation & OpenManus Integration Status — 2026-11-11

## Scope
Correct the public/auth shell leakage reported from mobile screenshots and record the current frontend-to-OpenManus/FastAPI integration boundary. This is a focused Phase 09 UI routing increment, not Phase 09 or Phase 11 acceptance.

## Baseline and target
- Repository: `fadliansyah36/More-AI-Portal-Indihome`, branch `main`.
- Baseline commit: `3219109f047f1a58a411970fc1c6071b06debb03` (previous production auth-routing fix).
- UI isolation implementation commit: `aecd134544eecb7c9a361c14ca067bb546bddeb2`.
- Navigation role-switch removal commit: `caa6c853286f9c29c5bf89be5d3907b05654274f`.

## Findings and changes
- The fixed Bottom Navigation Dock was rendered unconditionally, including Splash, Onboarding, Customer Login/Register, Partner Login and registration-success views. It is now gated by a public-entry route state; public/auth pages no longer render the dock.
- Public pages now use compact bottom spacing instead of reserving the private dock's space.
- Removed Customer ↔ Partner mode switch controls from the global desktop/mobile header and bottom dock. Partner access must begin through the Partner authentication entry, where active membership is checked server-side.
- Removed the global gallery and cross-domain drawer triggers from the dashboard header by no longer mounting their callbacks there. The current-role quick navigation remains.
- The MoreAI brand mark now navigates to the active role's own home (Customer home or Partner dashboard), not always to Customer.
- Existing colors, typography, spacing of the existing forms, and view component hierarchy were not redesigned. The UI edits are limited to visibility and navigation behavior.

## Files changed
- `app/page.tsx`
- `components/navigation/app-navbar.tsx`

## Verification
- GitHub Actions Phase 00 Baseline Verification: run [42973885825](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42973885825) — SUCCESS.
- Jobs: baseline/lint/build/browser smoke, worker tests, and API tests all completed successfully.
- Browser smoke and responsive screenshot workflow completed at the repository baseline widths (360, 390, 768, 1024 and 1440 px); evidence artifact: `moreai-phase00-baseline-caa6c853286f9c29c5bf89be5d3907b05654274f` (artifact id `13834487651`).
- Vercel production deployment for commit `aecd134544eecb7c9a361c14ca067bb546bddeb2`: deployment `dpl_4kCc46R8WeYE1eQtbuvNV177AUcN`, status READY; production aliases include `more-ai-portal-indihome.vercel.app`.
- Vercel HTTP fetch returned 200 for `/`, `/onboarding`, `/customer/register`, and `/customer/login`. HTTP reachability does not prove authenticated interaction or role authorization.
- No production login, signup, partner-membership E2E, OpenManus execution, or provider call was performed.

## Backend integration status and blockers
- The frontend already uses the typed API client in `lib/api/client.ts`; Customer Chat, agent runs, workflow progress, artifacts, approvals and Partner tenant/context/location surfaces have partial FastAPI integrations.
- The required architecture remains existing frontend → OpenManus-derived engine/worker via FastAPI → Supabase. Browser Supabase usage is Auth-only; application data and actions must stay behind FastAPI.
- Vercel still has no configured `NEXT_PUBLIC_MOREAI_API_URL`, `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL`, or `NEXT_PUBLIC_MOREAI_PARTNER_API_URL`. The deployed Next.js app does not provide the FastAPI `/api/v1/*` routes. The public FastAPI deployment origin is not present in the repository/project configuration available for this increment; no hostname has been invented.
- Therefore, production end-to-end frontend → FastAPI → OpenManus worker → Supabase persistence/streaming is NOT verified and cannot be claimed complete.
- No Supabase schema, migration, RLS or storage changes were made in this UI-only increment.
- Full upstream behavioral parity, remaining Phase 04 browser/sandbox hardening, remaining Phase 06–09 domain contracts, Phase 10 E2E and Phase 11 release gates remain open as recorded in the phase tracker.

## Next phase / work order
1. Configure the actual deployed FastAPI origin in Vercel Production/Preview/Development (after confirming its public URL and TLS/CORS policy).
2. Verify FastAPI health/readiness and OpenAPI, then verify the Supabase JWT validation and Customer/Partner tenant authorization boundaries.
3. Complete remaining Phase 04 OpenManus parity and sandbox/browser security gates.
4. Finish Phase 06–09 API contracts and connect every existing frontend domain without mock fallbacks.
5. Run authenticated browser E2E proving frontend → FastAPI → worker/engine → Supabase persistence/events → frontend before Phase 10/11 acceptance.

## Release status
- UI navigation isolation increment: implementation and CI baseline verification complete.
- Production Vercel deployment: READY.
- Full OpenManus frontend/backend integration: IN PROGRESS; not a release-gate completion.
