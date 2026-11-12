# Phase 09 — Customer Profile & Wi-Fi Session API Integration (2026-11-13)

## Scope

- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Branch: `main`
- Focus: connect existing Customer profile settings and Wi-Fi session screen to authenticated FastAPI contracts without redesigning the existing UI.
- Supabase project: `uunfgimtokhucegqbpce`

## Implemented source changes

### Profile & account settings

- The existing **Informasi Akun** action now opens an edit form instead of only showing a toast.
- Display name is persisted through the existing `PATCH /api/v1/me/profile` contract via the typed `profileApi.update` client.
- Language selection now persists `locale` through the same FastAPI profile contract rather than changing only local component state.
- Email remains read-only and is sourced from the authenticated identity.
- Save failures are surfaced to the user; local profile state changes only after the API responds successfully.
- Existing page layout, menu structure and navigation are retained.

### Wi-Fi session & quota screen

- The existing Wi-Fi session screen now loads the customer's network sessions, wallets and quota policies from:
  - `GET /api/v1/customer/network-sessions`
  - `GET /api/v1/customer/wallet`
  - `GET /api/v1/customer/quotas`
- Active session status and expiry countdown are derived from the persisted network session's `status` and `expires_at`.
- Wallet balance and available quota usage are displayed only when returned by the APIs.
- API errors are surfaced; unavailable gateway telemetry (live throughput, device controls, session extension/disconnection) remains unavailable and is not fabricated.
- Existing visual hierarchy and disabled actions are preserved.

### Agent Code Assistant and captive portal truthfulness

- Code Assistant no longer fabricates Python execution output or reports a successful local run. It sends the edited code to the existing Customer Chat handoff for Agent review; actual Python/Bash execution remains disabled until the supervisor, approval and sandbox release gates are met.
- The Projects panel no longer claims automatic persistence when no workspace persistence action is wired.
- Captive OTP no longer includes demo auto-fill, fabricated OTP resend success, or a fake successful verification transition. Inputs and verification remain disabled until a gateway OTP contract is available.
- Captive success screen now reads Customer network sessions, wallet balances and Partner entitlement from FastAPI. It reports an active session only when an unexpired active network session exists; static SSID, speed, duration and bonus-credit claims were removed.
- Captive Portal preview now labels gateway activation as unconnected and removes fabricated 100 Mbps / 100,000 AI credit claims.

## Commits

- `a7282fa7fd774d8dc4a78d66ed07fa8aa363122f` — profile editor and server-persisted language preference.
- `4bd3ca15a7951b1b3bc7027450e7f934285efdd7` — remove unused locale state.
- `2d74e9d0e8f1f28e99f45d79093d8ff369142daa` — bind Wi-Fi session screen to customer APIs.
- `cb2058502d47d1e9171df582d5660bda021eeb7b`, `7d1d599be9aa40c1619e91b7abec58a57c922547` — route code review to Customer Agent Chat and remove simulated code execution.
- `e5b558bfa9ce4f1b08ec218655df415643f12ddc`, `a0c9770bb817681bf56d9670f40bd0cc7adad7de`, `61493b3ccb59008aa5395862029aeb22e9615ea3` — disable simulated captive OTP verification.
- `26465c54f62d747d0e29f5ccd1190538f80f7f32`, `11cdde9f52b8ab156d9ae5c85b02b79a17d0a009` — read captive success state from Customer APIs and remove static access/credit claims.

## Files changed

- `components/views/profile-settings-view.tsx`
- `components/views/wifi-session-view.tsx`
- `components/views/code-view.tsx`
- `components/views/captive-otp-view.tsx`
- `components/views/captive-success-view.tsx`
- `components/views/captive-portal-view.tsx`
- `app/page.tsx`

## Verification and operational restrictions

Per explicit product-owner instruction, no tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment, provider calls, Supabase migration application or live database mutation were performed. This report records source changes only; it does not claim runtime success or phase acceptance.

No Supabase schema or migration changes were made. No worker or sandbox activation was performed.

## Remaining work

Phase 09 remains IN PROGRESS. Remaining Customer integration includes captive portal and network verification flows, full account/security lifecycle, notifications/preferences parity, creative generation actions, remaining agent workflows, and any customer screens still displaying non-backed state.

Phase 04, 06, 07 and 08 remain IN PROGRESS. Phase 10 remains unaccepted and Phase 11 remains blocked by the no-verification/no-staging instruction.

## Next implementation increment

Continue Phase 09 across the remaining Customer screens, prioritizing captive/network verification and agent execution UX only where matching FastAPI contracts and schema are already present. Reconcile schema before adding any new persistence contract. Preserve the UI and fail closed for unavailable gateway/provider capabilities.
