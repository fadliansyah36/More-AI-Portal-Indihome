# Phase 09A — Provider Routing & Secret Readiness

Date: 2026-11-15
Branch: main
Repository: fadliansyah36/More-AI-Portal-Indihome
Supabase: uunfgimtokhucegqbpce

## Owner constraints

- Direct commits to main; no branch or staging.
- No functional tests, browser/API/worker runtime probes, provider calls, builds, lint or typecheck.
- Existing Customer UI and MoreAI design tokens remain protected.

## Implemented at source level

### Routing contract

- FastAPI LlmRouteMutation.task_type now accepts general, chat, and planning.
- The database RPC moreai_admin_mutate_llm_route now accepts the same three task types while preserving platform role permission checks, enabled model/provider checks, fallback checks, and audit records.
- This closes the mismatch between OpenManus runtime defaults (chat) and Planning runtime (planning) versus the old general-only admin/database contract.

### Provider configuration and secret references

- Added moreai_admin_configure_llm_provider RPC. It stores only a public HTTPS base URL and the name of a worker environment variable such as MOREAI_PROVIDER_OPENAI_API_KEY; it never stores an API key value.
- The RPC enforces platform model-management permission, an allowlisted secret variable name, HTTPS URL shape, public host checks, provider-specific hostname allowlist and an audit event.
- Provider configuration is restricted to providers currently implemented by the OpenAI-compatible adapter: OpenAI (api.openai.com) and Google's OpenAI-compatible endpoint (generativelanguage.googleapis.com). Anthropic's native Messages API adapter is not present and is intentionally not offered as a configurable provider.
- Provider catalog returns only whitelisted non-secret metadata: provider name/key, endpoint URL, secret environment-variable reference and configured status. Arbitrary config JSON is never serialized.
- Provider mutation persists the provider disabled first, writes endpoint/secret reference, and only then applies explicit platform-admin activation attestation. The actual API key is never accepted by the browser form or API request.
- Provider activation requires explicit confirmation that the secret has already been installed on the persistent worker host. This is an operator attestation, not a live provider test.

### Worker-side readiness

- Added provider_readiness_snapshot to resolve both chat and planning routes against enabled models/providers and verify that at least one referenced secret environment variable for each task exists in the worker process.
- Worker startup now fails closed if either route cannot resolve or its secret environment variable is missing.
- Readiness metadata is included in the worker capability snapshot. The check does not call provider APIs and is not proof of network reachability, provider account status or model correctness.
- Existing API-level Agent execution flag remains disabled.

### Super Admin UI

- Added provider endpoint and secret-reference configuration form.
- Added model registration form with explicit pricing/token limits and disabled-by-default behavior.
- Added chat/planning/general routing policy form and explicit enable toggles.
- Existing Tailwind visual language, red primary action, white/light surfaces, rounded cards and typography are retained. No customer-facing screen or navigation was redesigned.
- This is a source-only UI change. Before/after browser screenshots were not captured under the no-browser/no-test instruction; visual regression remains NOT VERIFIED.

## Supabase production migration

Applied to the canonical project:

1. moreai_provider_configuration_and_route_types — version 20261115092653
2. moreai_provider_endpoint_allowlist — version 20261115092950

Read-only schema inspection confirms both RPCs exist and the routing function includes chat and planning.

## Source commits

- 8db3992d — routing task types and provider configuration migration.
- 01383176 — FastAPI provider config and route contract.
- bbb3287b — worker provider readiness resolver.
- 05ea0287 — worker startup gate for chat/planning and secret presence.
- dcd5efee — Super Admin provider/model/routing configuration UI.
- 49d9ab6b, 2f78c30c — provider schema and selection corrections.
- bb46f586 — provider endpoint allowlist migration.
- a1fe4a20, 472d7d8f, 4ad7e1f5 — provider allowlist, explicit activation attestation and persist-config-before-enable ordering.
- 635333c3, ddd0af1f, a46c0394 — supported provider list, activation controls and reset of secret attestation when switching provider selection.
- 48f63161, 7ae14733 — worker configuration/readiness documentation.

## Current production blockers

- Read-only Supabase inventory still shows zero rows in llm_providers, llm_models, llm_routing_policies, and moreai_worker_capability_snapshots. No fake provider/model/pricing rows were seeded.
- No provider secret values are present in a worker host because no persistent worker host is connected in this execution context.
- The Railway app integration is not connected/installed in the available tool context. Therefore no worker deployment or host secret injection was performed.
- Provider activation is not performed. Worker secret readiness cannot be established until the operator provisions a persistent host and installs the configured secrets.
- Vercel API production deployment is behind current main; deployment was not attempted because the previous daily deployment quota was exhausted.
- No provider API requests, test prompts, real Agent Runs, browser checks, build, lint or typecheck were executed.

## Phase assessment

- 09A source contract: implemented.
- 09A operational provider readiness: BLOCKED pending real provider setup and persistent worker secret injection.
- 09B persistent worker deployment: BLOCKED pending connected host integration and credentials.
- 09C customer dashboard action closure: remains in progress; only actions with real provider/domain contracts may be activated.
- 09D OpenFuse Browser/Computer parity: not started; remains dependent on 09A–09C.
- Phase 10 verification is NOT ACCEPTED and Phase 11 release gate remains BLOCKED.

## Next actions

1. Provision/connect the persistent worker host and inject SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, billing/quota settings and provider secrets through its secret manager.
2. Configure real provider/model pricing and enable both chat and planning routes through Super Admin.
3. Deploy worker as an always-on container and restore heartbeat/readiness.
4. Continue source-to-screen action closure across Customer Dashboard surfaces, keeping payment, captive gateway, OTP, support and other unavailable vendor integrations fail-closed.
5. After 09C, complete OpenFuse Browser/Computer parity through the isolated supervisor and customer approval controls.
