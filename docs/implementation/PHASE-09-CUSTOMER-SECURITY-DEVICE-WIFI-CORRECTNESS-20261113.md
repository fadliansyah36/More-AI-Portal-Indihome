# Phase 09 Customer Dashboard Integration — Security, Device and Wi-Fi Truthfulness

Date: 2026-11-13
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main
Execution mode: direct-main source implementation only; no staging, production deployment, runtime probes, provider calls, database writes or test execution.

## Scope implemented

### Security settings — real Supabase Auth TOTP management
- Replaced the local-only 2FA toggle and fabricated success toast with the Supabase Auth MFA client flow.
- Loads actual enrolled factors through `auth.mfa.listFactors()`.
- Starts TOTP enrollment through `auth.mfa.enroll()`, presents the returned QR code and manual secret, creates a challenge, and verifies the user-entered code.
- Supports cancelling an unverified enrollment and removing a verified factor through `auth.mfa.unenroll()`.
- Refreshes the Auth session after factor removal and reloads the factor inventory.
- Password update remains on the existing Supabase Auth password flow.
- Global sign-out action is labeled accurately as signing out all sessions.
- Session inventory remains explicitly unavailable; no fake device/session records are shown.

### Device access control — removed fabricated router/device state
- Removed four hardcoded example devices and locally simulated pause/resume and parental-filter state from the customer screen.
- The screen now presents an explicit unavailable state until a real authenticated partner/gateway device contract is available.
- No device control action is presented as successful without a backend operation.

### Wi-Fi session and quota — removed simulated live metrics
- Removed the hardcoded session countdown, venue/table identity, upload/download Mbps values and AI quota figures.
- Removed local-only session extension and disconnect success actions.
- The existing screen now shows an explicit unavailable state for session telemetry and disables unsupported controls.
- Upgrade navigation remains available; it does not claim a credit or quota mutation.

## UI preservation
- Existing customer routes and component locations were preserved.
- Existing page hierarchy, brand styling and card layout were retained; changes are limited to behavior, state provenance and unavailable-state copy.
- No broad redesign, global CSS, token or navigation changes were made.

## Files changed
- `components/views/security-settings-view.tsx`
- `components/views/device-access-control-view.tsx`
- `components/views/wifi-session-view.tsx`

## Commits on main
- `083bef75ed03330089565764af497fca1de6705c` — connect security settings to Supabase Auth MFA
- `0a0675c26d5044621d79472678837fd1d81406bf` — trim security settings imports
- `b0b54e37075e43a42d156c264a7db0827733b00c` — remove fabricated device controls
- `477f590e759caad9362b77cdd91c92320f9ecbe1` — remove simulated Wi-Fi session and quota state
- `55138bc0fb8aa9328ddc0c27170815e9edba87c6` — remove unused Wi-Fi session icons
- `d7f7cd6fa736c94628568aee9346b8f054471f78` — stabilize Auth factor loading lifecycle

## Supabase/database
- No schema change or migration was needed for this increment. MFA enrollment/verification uses Supabase Auth APIs; no business table, RLS policy or Storage access was changed.
- No Supabase project mutation was performed.

## Verification and limitations
- Per the explicit instruction, no tests, lint, typecheck, build, browser/API runtime checks, screenshots, staging or deployment were run.
- Therefore this increment is source-committed but not runtime-verified.
- TOTP factor management is implemented in the security settings view, but login-time AAL2 challenge routing and enforcement across the customer API are still not complete.
- Complete session/device inventory is not exposed by the current customer-facing Auth contract.
- Device access control and captive Wi-Fi session lifecycle remain unavailable until a real partner/gateway API, credentials, ownership contract and durable backend operations exist. This report intentionally does not fabricate those capabilities.
- Phase 09 remains IN PROGRESS; this is not phase acceptance.

## Next dependency-ordered work
1. Phase 04: finish upstream server/session, exception/logger/tracker parity, sandbox supervisor integration, browser isolation and workspace lifecycle.
2. Phase 06: complete customer/partner/admin REST and WebSocket contracts, route-wide response models, authorization, pagination and idempotency.
3. Phase 07: finish durable event/lease/recovery behavior and crash-safe worker lifecycle.
4. Phase 08: close complete OpenManus agent/tool/provider/orchestration parity, distributed provider health state, memory/RAG and metering.
5. Phase 09: add login-time MFA challenge enforcement, real customer device/session and Wi-Fi gateway contracts, then finish remaining Customer screens/actions.
6. Phase 10 and 11 remain blocked until the product owner authorizes the verification/release work; no deployment is authorized by this increment.

## Additional Phase 04 / Phase 06 API error-contract increment

- `apps/api/app/main.py` now classifies upstream HTTP client timeouts as HTTP 504 / `upstream_timeout` and other HTTP transport failures as HTTP 503 / `upstream_unavailable`.
- Unhandled API exceptions now emit correlation ID, path, method and exception class through the API logger. Exception messages and tracebacks are intentionally omitted to avoid leaking prompts, credentials, provider payloads or user data.
- Error responses retain the existing stable `error.code`, `error.message` and `error.correlation_id` contract.
- Capability map updated to mark only this transport-level portion partial; upstream domain exception taxonomy and durable engine/worker log projections remain open.
- Commit: `e76f7ccebeca21ee6b4ac0a57488eef547c8ceea`; capability map commit: `7ac60192b8e32d11f2a060edc1d62382a61801fd`.
