# Phase 09 — Real Provider Onboarding & Customer Domain Contract Gate

Date: 2026-11-13  
Branch: `main`  
Baseline source HEAD inspected: `b92d69816c733ec33673e3f7006e7b5782620353`  
Canonical Supabase project: `uunfgimtokhucegqbpce`

## Execution constraints

This increment follows the product owner's instruction to work directly on `main` and not run real tests or staging. No test, lint, typecheck, build, browser, API, worker, provider, staging or E2E execution is authorized in this increment. No production business records or provider credentials are fabricated.

## Current production evidence

Read-only schema/catalog inspection confirms the following objects already exist:

- Gateway/provider registry: `network_providers`, `provider_partnerships`, `partner_networks`, `network_verification_configs`, `network_verification_method_catalog`.
- Verification evidence/lifecycle primitives: `network_verification_attempts`, `network_verification_evidence`, `network_verification_sessions`, `network_gateway_nonces`.
- Access lifecycle: `network_sessions`, `network_session_events`, `partner_access_codes`, `partner_access_code_redemptions`.
- Monetization primitives: `wallet_accounts`, `credit_ledger`, `user_entitlements`, `quota_policies`, `quota_usage`.
- Customer learning progress exists, but no authoritative course catalog, enrollment, lesson, protected-video entitlement or delivery contract was identified.
- No support ticket schema/provider lifecycle was identified.
- Payment wallet/ledger primitives exist, but no checkout intent, payment provider transaction, signed settlement webhook, refund/reversal or subscription purchase contract was identified.

All listed network lifecycle tables are RLS-enabled. Their existence is not proof that the API lifecycle, provider integration, or Customer UI flow is complete.

Production inventory readback previously recorded zero rows in `network_providers`, `partner_networks`, `network_verification_configs`, and `network_sessions`. The five catalog methods (gateway, GPS, ISP API, MikroTik Hotspot and RADIUS) are all `adapter_ready=false`. Partner configuration code already rejects enabling a method whose adapter is not ready.

## Captive Gateway — what is and is not complete

Existing Partner API source includes tenant-scoped network registration, verification-config CRUD, adapter readiness gating and access-code issuance/revocation. Customer API source includes owner-scoped network session history and access-code redemption requiring a verification-session ID.

The current implementation does **not** establish a real gateway trust chain. In particular, the inspected production schema does not expose a consent record/table, OTP challenge/delivery record, or provider-specific callback contract. Existing verification evidence/session/nonce tables are useful persistence primitives, but cannot safely substitute for the missing external protocol and consent proof.

Do not mark any method ready or activate a network until all of the following are supplied and reviewed:

1. **Provider identity and deployment ownership** — legal/provider name, product, technical contact, environment, network/partner owner, and who operates the gateway.
2. **Exact integration method** — MikroTik RouterOS/HotSpot version and API mode, RADIUS protocol and accounting model, ISP REST API specification, or gateway vendor/version. A generic label such as "MikroTik" is not enough.
3. **Protocol contract** — endpoint/host, TLS requirements, request/response examples, authentication scheme, signed callback fields, timestamp tolerance, nonce/idempotency semantics, retry policy, rate limits, error codes, and lifecycle callbacks (login, heartbeat/accounting, logout/CoA if applicable).
4. **Secret management** — secret-vault product and secret reference format; credentials must be provisioned through the approved secret manager and never pasted into source, PRD, chat logs, public config or Supabase `config_public`.
5. **Network binding** — partner organization, location, network ID, gateway network reference, provider ID, SSID/captive redirect configuration and allowed callback source ranges where appropriate.
6. **Consent/legal policy** — exact consent text/version, purposes, required disclosures, retention period, lawful basis/owner approval, withdrawal semantics and evidence to persist (version, timestamp, user/session, policy hash, locale, source).
7. **OTP provider** — SMS/WhatsApp/email provider and account ownership, sender identity/template approval, delivery API, verification API, expiry, attempt limits, resend throttling, abuse controls and delivery status callbacks. Supabase Auth phone OTP may only be selected if its phone provider is actually configured and the guest/customer identity flow is compatible.
8. **Session policy** — authoritative source of online/offline state, heartbeat/accounting interval, maximum session duration, idle timeout, refresh/revocation behavior, duplicate-session policy, disconnect behavior and entitlement expiry.
9. **Operational acceptance** — provider-side test tenant/network, callback allowlisting, support escalation, incident contacts and explicit authorization to activate production traffic.

### Required secure lifecycle once the provider is onboarded

- Discover network from a trusted gateway-signed context; never trust client-supplied SSID, BSSID, IP, gateway ID or network ID as proof.
- Create a verification attempt bound to the authenticated user (or an explicitly designed guest principal), network, method and correlation ID.
- Record versioned consent before any optional personal-data/OTP processing.
- Issue and verify OTP through the configured provider with hashed challenge material, short expiry, single-use consumption, attempt/resend throttles and audit events.
- Verify gateway/provider signature and timestamp, consume a one-time nonce atomically, validate issuer/network binding and persist only hashed/minimized evidence.
- Create a verification session and Customer network session only after all policy checks pass; derive expiry from server policy/provider state.
- Support authenticated refresh/heartbeat and revoke/logout; expire stale sessions and remove Partner Free entitlement on termination.
- Enforce idempotency, replay protection, rate limiting, audit logging, RLS and cross-tenant ownership checks throughout.
- Fail closed on missing configuration, invalid signature, stale timestamp, replay, OTP mismatch, provider timeout or inconsistent session state.

No generic HMAC/webhook endpoint should be invented before the provider's signed message format and secret resolver are selected. Doing so would create an unreviewed protocol and could falsely mark an untrusted client as a sponsored network user.

## EduTech / Payment / Support — provider contract gates

### EduTech

Required before implementation can be completed: authoritative content owner/provider; catalog/course/lesson IDs and metadata; enrollment/eligibility API; video host/CDN; signed playback/token contract; DRM/watermark requirements if any; progress/completion callbacks; refund/cancellation behavior; content license and access duration. Existing learning progress is only progress state, not a course catalog or video delivery service.

### Payment

Required before implementation can be completed: selected Indonesian payment provider and merchant account; product/price/SKU and tax/fee decisions; checkout/session API; supported methods; signed webhook specification and signing key reference; idempotency and event ordering; settlement, expiry, refund/chargeback behavior; reconciliation source; subscription renewal/cancellation rules; credit issuance mapping. Wallet/ledger must only change from verified server-side settlement/reversal events.

### Support

Required before implementation can be completed: official channel/provider (ticketing SaaS, CRM, or owned support backend); tenant/user identity mapping; create/list/detail/reply/status/assignment/SLA contracts; attachment handling and retention; escalation and notification rules; privacy and retention policy. FAQ/help content is not a ticket submission channel.

## Next implementation sequence (Phase 09 remains open)

1. Onboard one real gateway/ISP/RADIUS provider and provision its server-side secret reference and partner/network mapping.
2. Implement that provider's exact adapter and signed callback verification against the existing verification/evidence/nonce/session primitives.
3. Add versioned consent persistence and the selected OTP provider challenge/verification lifecycle.
4. Complete session create/heartbeat/refresh/revoke and entitlement coupling.
5. Select the actual EduTech, payment and support providers and implement their verified contracts in dependency order.
6. Finish the remaining Customer screen/action-to-FastAPI/OpenAPI reconciliation.
7. Deploy only when the existing production release constraints are resolved; no deployment or runtime acceptance is claimed here.

## Current blocker requiring product/provider input

The repository and production database do not identify a configured live gateway, OTP provider, EduTech provider, payment provider or support system. The product owner must supply the provider's name and official technical integration documents, or authorize a named vendor selection process. Until then, Phase 09 remains **IN PROGRESS** and all unavailable external actions must remain explicitly unavailable/fail-closed.

## Verification and deployment status

- Source review and read-only Supabase schema/catalog inspection only.
- No real tests, staging, runtime API/provider calls, worker execution, browser checks, lint, typecheck, build or E2E were run.
- No production migration or provider activation was performed in this increment.
- No production deployment was performed; prior deployment quota limitation remains as previously reported.


## Reconciliation update — 2026-11-14

- Re-read the controlling `AGENTS.md`, current Customer Dashboard Acceptance Matrix, Customer API inventory, current provider onboarding report, FastAPI Customer router and typed frontend API client on `main`.
- Confirmed the current Customer UI actions with real source contracts remain the supported integration surface: Chat/message enqueue and durable session events, Agent Runs/steps/activity/cancel, tool/model capability catalog, workspace files/version history, artifacts, knowledge/RAG citations, wallet/ledger/usage reads, learning progress, notifications, profile and network-session history/access-code redemption.
- Confirmed the Customer browser boundary remains Supabase Auth only; business actions continue through typed FastAPI API client. No direct browser PostgREST, Storage, RPC or Realtime data path was added.
- Provider/domain inventory remains unchanged: production schema has no identified payment checkout/settlement or subscription contract, no authoritative EduTech catalog/enrollment/video delivery provider, no support ticket lifecycle, no provisioned gateway/OTP adapter or signed provider callback contract, and no complete customer Memory privacy lifecycle. Existing wallet/ledger and learning-progress tables do not establish those missing provider services.
- These are external contract prerequisites, not missing UI widgets that can safely be completed with invented APIs. The existing dashboard must remain fail-closed for these actions until the provider identity, official API/webhook specs, secret references, lifecycle policy and tenant ownership are available.
- No provider credentials were supplied in this increment; no vendor account was provisioned, no payment/OTP/gateway/support/learning provider was selected, and no production schema was altered.
- No tests, lint, typecheck, build, browser/API/worker runtime checks, provider calls, staging, deployment or E2E verification were run. Phase 10 and Phase 11 therefore cannot be marked accepted under the explicit `AGENTS.md` gates.

### Phase status
Phase 09 remains **IN PROGRESS**. Source integration for available Customer contracts is present; remaining PRD gaps are provider/domain gated and cannot be represented as complete. Phase 10 remains NOT STARTED/BLOCKED; Phase 11 remains BLOCKED.

### Required provider inputs to close the gates
1. Captive gateway/ISP/RADIUS: vendor/product, exact API/protocol version, signed callback contract, partner/network mapping and secret-vault reference.
2. OTP: selected SMS/WhatsApp/email provider, merchant account, delivery/verification APIs, sender/template approval and rate-limit/expiry policy.
3. Payment/subscription: Indonesian payment provider and merchant account, checkout/webhook signatures, settlement/refund/chargeback/subscription contracts and SKU/credit mapping.
4. EduTech: content owner/provider, course/enrollment API, protected media/CDN token contract, license and progress callbacks.
5. Support: official ticketing/CRM backend and create/list/detail/reply/status/SLA/attachment contracts.
6. Memory privacy: approved consent/retention/deletion policy and a server-side customer API backed by canonical persistence.


## 2026-11-14 correction — Customer Memory and media provider status

- The earlier statement that Customer Memory privacy lifecycle was unavailable is superseded by the Phase 09 implementation on 2026-11-14. Owner-scoped consent, list/create/update/delete/clear APIs, profile settings UI, worker consent filtering and scheduled expiry purge are now present in source, with their Supabase migrations applied. Runtime acceptance remains NOT VERIFIED.
- OpenAI Image API has supported generation models and a server-side Images API. The MoreAI worker still does not register an image adapter, and no API key or media-specific entitlement/credit reservation/metering policy has been provisioned. It therefore remains unavailable/fail-closed in Customer Create Studio.
- OpenAI's Sora 2 models and Videos API were removed on 2026-09-24 with no one-to-one replacement. Do not implement an OpenAI Sora adapter as though it were a live API. A supported external video provider may be selected; Runway Dev documents asynchronous task creation and task polling, but selecting that provider, configuring a server-side secret and approving its pricing/credit policy are still product-owner decisions. Official references: [OpenAI Image Generation](https://developers.openai.com/api/docs/guides/image-generation), [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations), [Runway Dev API](https://docs.dev.runwayml.com/api/).
- The Master PRD file currently committed in this repository is `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md`. A v1.2 Master PRD was not found in the repository or current Project file search during this continuation. Exact v1.2 conformance cannot be claimed until that source is supplied or committed.
- No tests, runtime calls, provider activation, staging or deployment were performed.


### OpenAI Image adapter source integration — 2026-11-14

- The previous note that the MoreAI worker had no image adapter is superseded. A metered `gpt-image-2` adapter is now present in `engine/tools/media.py`, registered through the OpenManus tool catalog and worker registry only when the server-side API key, media entitlement/quota, wallet conversion and explicit per-size/quality USD price map are configured.
- The adapter uses the official Images API generation endpoint, saves binary output to private Supabase Storage, and returns an artifact reference. It reserves wallet/quota before the provider request and retains reservations on ambiguous provider outcomes.
- No API key was created/read, no pricing configuration was supplied, no provider call was made and the adapter is not claimed active in the current deployment.
- The official current model used by source defaults is `gpt-image-2`; OpenAI documentation says organization verification may be required. Official cost examples currently list 1024×1024 at $0.006 low / $0.053 medium / $0.211 high. Those values are examples only and must be reviewed against current provider pricing before configuration.
- Sora Video API remains removed. Runway Dev is one technically documented candidate for an asynchronous video adapter, but it has not been selected or connected. A product-owner decision and secret/pricing configuration are still required.


### Runway Dev video adapter source integration — 2026-11-14

- Runway Dev is now the selected video provider adapter. The worker uses the official `POST /v1/text_to_video` and `GET /v1/tasks/{id}` contract, with API version `2024-11-06`.
- Durable checkpoint states preserve provider task IDs and prevent duplicate submission after ambiguous network outcomes. The result is stored as a private MP4 artifact and MoreAI usage is reserved/settled against configured provider credit conversion and max-price policy.
- Required configuration is documented in [Agent Configuration & Create Studio report](./PHASE-09-AGENT-CONFIGURATION-CAPABILITY-REGISTRY-CREATE-STUDIO-20261114.md). No Runway API key or pricing values were supplied, no provider request was made and the adapter is not live until the full configuration gate passes.
- Official docs: [Runway Dev API Reference](https://docs.dev.runwayml.com/api/).
