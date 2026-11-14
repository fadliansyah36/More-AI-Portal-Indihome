# MoreAI — Customer Integration & Super Admin Control Plane Continuation

Date: 2026-11-14
Branch: `main`
Baseline HEAD: `a8883c96d07970ac9f8327cd33580a50ba97c812`

## Execution constraints

The product owner requested direct-main implementation, no real testing and no staging. This report records source inspection only for this increment. No tests, lint, typecheck, build, browser/API/worker runtime checks, provider calls, staging, migration application or deployment were run.

## Controlling engineering instructions

- `AGENTS.md` confirms OpenManusWeb is the authoritative backend source and requires complete backend capability parity, while the existing MoreAI Next.js UI remains protected.
- Browser business operations must use typed FastAPI contracts. Browser Supabase use remains Auth-only.
- Existing UI must not be redesigned. Missing UI may be added only for required PRD workflows and must use the approved MoreAI design authority and the current PRD design requirements.
- Phase 10/11 verification and release gate cannot be marked accepted without their required evidence. User's no-test/no-staging constraint is preserved.

## Current source findings

### Customer Dashboard

The existing Customer integration already includes source contracts for durable Chat/message enqueue, Agent Runs and event replay, cancellation, catalogues, workspace files/version history, artifacts, Knowledge/RAG citations, wallet/ledger/usage reads, learning progress, notifications, profile and network-session history/access-code redemption.

The Phase 09 inventory remains the source-of-truth checklist for each visible Customer action. Continue reconciling every current screen and action to its real FastAPI contract and OpenManus runtime behavior. Do not substitute mock data, local-only success states, or fabricated external provider APIs.

The following remain explicitly gated where their real provider or business contract is not present: payment checkout/settlement/refund/subscription, EduTech authoritative catalog/enrollment/protected media, support ticket lifecycle, gateway/ISP/RADIUS signed callback lifecycle, OTP delivery/verification, Memory privacy lifecycle, and other isolated execution/connector operations not yet supported by the verified backend contract.

### Super Admin

The current route `app/admin/page.tsx` renders `components/views/super-admin-view.tsx`. The page is currently a read-oriented control center with four tabs: overview, partners, Agent Runs, and audit. It calls the existing FastAPI endpoints `/api/v1/admin/context`, `overview`, `partners`, `agent-runs`, and `audit`.

The current `apps/api/app/routers/admin.py` provides platform context/permission dependencies and those read operations plus partner status mutation. It does not yet expose a Provider Management API or provider lifecycle/configuration endpoints. Thus the earlier statement that missing vendor credentials block all provider work was too broad: the provider registry, configuration UI, metadata, secret-reference lifecycle, adapter catalog, routing policy, health and audit foundations can be built before credentials are supplied.

### Required Super Admin Provider Management scope

Implement a shared provider control plane, not separate ad-hoc vendor forms:
1. Provider registry with category, vendor/adapter key, display metadata, ownership/scope, environment, status and version.
2. Category-specific configuration schemas for LLM/model, payment, OTP/SMS/WhatsApp/email, EduTech, support/CRM, ISP/RADIUS/gateway and other PRD domains.
3. Secret references only; never persist plaintext credentials in ordinary configuration rows, API responses, logs, source or browser state.
4. Model/service catalog and mapping; LLM routing priorities, capability matching, cost/pricing version and fallback policy.
5. Provider validation/activation lifecycle with explicit unavailable-credential states; connection validation must not be simulated.
6. Health/latency/error/usage monitoring and webhook delivery visibility where real telemetry exists.
7. Versioned configuration, immutable audit records, safe disable/rollback and rotation metadata.
8. Platform role/permission checks server-side for every read and mutation; sensitive activation/credential changes require elevated permission and confirmation/approval policy.

No provider is considered operational merely because its registry record exists. Provider activation remains fail-closed until official API/protocol documents, account ownership, credential secret references, lifecycle policy and tenant/network mapping are available.

## Dependency-ordered next implementation

1. Continue Phase 09 Customer screen/action-to-FastAPI reconciliation, prioritizing the core AI path: Chat → enqueue → durable Agent Run → worker/orchestration → provider/tool execution → persisted events/artifacts/usage → Customer UI replay. Preserve current visual UI and add only missing integration affordances.
2. Implement Super Admin Provider Control Plane foundation: data model/migrations, typed Pydantic contracts, platform permissions, FastAPI endpoints, typed admin client and UI tabs/forms using the approved PRD design tokens. Provider setup must support draft/incomplete records and secret-reference status before any vendor is onboarded.
3. Integrate provider adapters into existing LLM gateway/model router and other domain services; avoid a parallel provider execution path.
4. Complete real provider onboarding later through Super Admin when the product owner supplies vendor selection, official protocol/API documentation and secret-manager references.
5. Only after Phase 09 source scope is complete and verification is authorized, proceed to Phase 10 and Phase 11. Under the current no-test/no-staging instruction these gates remain NOT ACCEPTED/BLOCKED.

## Explicit non-claims

This increment did not implement or activate Provider Management. It records the source gap and corrected implementation boundary so subsequent changes can be made against actual code and permissions. No tests or runtime verification were performed. No provider credentials were added. No schema migration was applied. No deployment was performed.

