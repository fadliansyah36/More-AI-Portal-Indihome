# MoreAI — Customer Wi-Fi and Partner Operations UI Integration Increment

Date: 2026-11-11  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Target commit: `1b20d7322224826b855a2483b7add9564733d110`  
Canonical Supabase project: `uunfgimtokhucegqbpce`

## Execution constraints

- Implemented directly on `main`; no branch was created.
- Product-owner instruction: do not run real tests or staging.
- No build, lint, typecheck, unit/integration/E2E test, browser verification, screenshot capture, CI rerun, migration apply, deployment, worker activation or provider call was performed in this increment.
- This report records source changes and schema inspection only. It is not a phase acceptance or production runtime claim.

## Scope completed in this increment

### Customer Wi-Fi session visibility

- Added authenticated `GET /api/v1/customer/network-sessions` in `apps/api/app/routers/customer.py`.
- The endpoint scopes all records to the authenticated Customer principal and returns bounded network session metadata, associated partner network and location metadata.
- Sensitive gateway identifiers, IP addresses, device fingerprints and verification evidence are deliberately excluded.
- Added `CustomerNetworkSession` and `customerApi.networkSessions()` to `lib/api/client.ts`.
- Bound the existing Wi-Fi Management screen to the live session API. The screen now displays actual network/session fields and explicit unavailable states for gateway diagnostics, speed, password, protection and device inventory rather than seeded network values.
- Bound the existing connected-device view to the account's network session history. It explicitly explains that the current API does not provide gateway device inventory, per-device IP/bandwidth or disconnect operations; it does not misrepresent sessions as devices.

### Partner operations

- Replaced seeded voucher records and local fake claim/revoke behavior in `partner-vouchers-view.tsx` with the existing Partner access-code API:
  - list codes;
  - issue a code with expiry and redemption limit;
  - show the plaintext code only in the one-time creation response;
  - revoke active codes through FastAPI;
  - show tenant-scoped metadata and server-returned redemption counts.
- Replaced seeded Partner staff identities with actual `partner_members` records from `GET /api/v1/partner/members`.
- Connected staff invitations to `POST /api/v1/partner/members`. The current backend contract requires a Supabase User UUID; the UI labels this requirement and does not fabricate email/name resolution. Server-side Partner Owner/Admin and location ownership checks remain authoritative.
- Replaced fake promo-material download success toasts and static campaign content with live Partner campaign list/create/update calls:
  - list campaigns;
  - create campaigns as draft;
  - update active/paused status;
  - show persisted campaign dates and budget where present.
- Existing tenant resolution and permission enforcement remain in FastAPI.

### Customer profile and analytics

- Customer profile settings now derive the displayed credit balance from the authenticated wallet API instead of a hardcoded free-credit number.
- Analytics model breakdown is derived from persisted `llm_usage` records by model key and request/token totals. Static illustrative feature percentages were removed.

## Supabase schema reconciliation used

Read-only inspection confirmed the relevant existing objects and columns:
- `network_sessions`: owner, network, verification session, lifecycle timestamps/status;
- `partner_networks` and `partner_locations`: tenant network/location metadata;
- `partner_access_codes`: code hash, lifecycle, expiry and redemption counters;
- `partner_members`: tenant membership, role and location scope;
- `partner_campaigns`: campaign lifecycle and budget;
- `wallet_accounts`: user wallet balance;
- `llm_usage`: persisted model/provider usage and cost/token fields.

No DDL, migration, policy, grant, RPC or production data mutation was performed. The new Customer network-session endpoint reuses the existing schema.

## Source commits

- `3c60eeb7b480b6dc559a89ce897b554bbca75dc9` — Partner voucher screen uses access-code APIs.
- `c436cf1a822cd0a493c7b0f408ae33b336396cbd` — Partner staff screen uses membership APIs.
- `165cab8c12ae11068a312aa881cf04b1b66555e9` — Partner campaign screen uses campaign APIs.
- `eb75e336ad958d946f4b07fdf10375442e61ffce` — owner-scoped Customer network-session endpoint.
- `5521952c1cfd318b4e73133a905ec70c719438aa` — typed Customer network-session API client.
- `120485e63f94144177d89fcf80c692a7eebaa49a` — Wi-Fi Management bound to session data.
- `b5e6d437cd411ad794ebd3d663c2384b65620dbb` — connected-device view removes seeded device data and shows actual session history.
- `18d07ed348a12ab6e277d913397cba1fbe4a7c3d` — Customer profile credit balance uses wallet API.
- `9ad496c7fe57cd267fe1f13187236bfe6b4483cc` — analytics model usage breakdown from persisted records.
- `1b20d7322224826b855a2483b7add9564733d110` — analytics import cleanup.

## Remaining integration gaps — not complete

The following require additional backend/domain work; they must not be represented as live:

1. Captive Portal: gateway discovery/context, verification-attempt creation, OTP/GPS/MikroTik/RADIUS/gateway/ISP adapter execution, verified-session issuance and session lifecycle are not fully exposed as a Customer-facing API.
2. Connected devices: no schema/API currently exposes router device inventory, per-device IP/bandwidth or disconnect controls. `user_devices` is an application-device registry and is not equivalent to Wi-Fi gateway inventory.
3. Customer Wi-Fi settings: no API contract for SSID/password/schedule/QoS/security controls or live speed/optical diagnostics.
4. EduTech: no canonical course/lesson/progress/certificate tables or FastAPI contracts were found in the current public schema inventory.
5. Customer voucher/reward claims: Partner access codes are not the same as discount vouchers or reward claims. Customer reward catalog/claim/redeem APIs remain absent.
6. Partner staff UX: invitation currently requires an existing Supabase User UUID. Email-based user discovery/invitation is not implemented. Membership revocation/suspension UI is also not exposed by the current API contract.
7. Partner promotion assets: no real asset catalog or signed-download contract is wired for poster/social templates; fake download toasts were removed.
8. Security settings: account MFA enrollment/challenge UX and a full session inventory API still need integration.
9. Super Admin: source has existing server-authorized overview/list/status/audit contracts, but complete permission-specific mutation coverage and UI action binding remain open.
10. OpenManus: source-level UI integration remains gated by Phase 04/07/08 runtime and security gaps. Provider/worker execution is not enabled by this increment.

## Phase status

- Phase 09: IN PROGRESS. This increment connects additional Customer Wi-Fi session visibility and Partner campaign/member/access-code screens. It does not complete all Customer/Mitra/Admin screens.
- Phase 04, 06, 07 and 08: IN PROGRESS.
- Phase 10: BLOCKED by the explicit no-real-testing/staging constraint and outstanding runtime integration.
- Phase 11: NOT STARTED.
- No deployment or production activation occurred.

## Next implementation increment

Continue source integration on `main` in dependency order:
1. Define and implement the remaining Customer network verification/session contracts against existing tables and adapter readiness; keep unready methods disabled.
2. Implement Customer reward catalog/claim contracts only after reconciling the reward schema and idempotent claim semantics.
3. Complete Partner network/configuration and staff lifecycle screens using existing APIs; add missing server contracts only where the schema and permission model support them.
4. Complete Super Admin permission-specific actions and audit contracts.
5. Continue OpenManus/worker/API parity without activating browser, Python/Bash or provider execution gates.
6. Keep Phase 10/11 explicitly blocked until the product owner authorizes the required verification policy.
