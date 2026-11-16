# Phase 09 — Customer Skill Registry source continuation

Date: 2026-11-16  
Branch: `main`  
Source baseline: `bed0cebc7f05be5e3f70047636a334cb5959758a`  
Current source head: `a22a35ce444d5c920eed4828d47a91b4c2eb1bc9`

## Source changes committed

1. `fca8d53b04cd56f627285b74c863614219dd3c48` — Customer Skill Registry list now loads up to 500 packages and installs, rather than 100. The pinned catalog contains 230 entrypoints across Motion (56), Scenario (172) and Visual (2); the smaller list bound could hide pre-imported packages from the sequential batch reconciler and cause duplicate-import conflicts after the first 100 entries.
2. `ba72739770e4b3ed3d1cfddd4baca2ed82077cb0` — FastAPI `POST /api/v1/customer/skills/{skill_id}/validate` was attached to the wrong function. The route decorator sat above the internal synchronous `_source_review_inventory(files)` helper, while the intended authenticated async `validate_skill(skill_id, request, user)` handler was not registered. The decorator now targets `validate_skill`, which performs owner scoping, source inventory, SBOM generation and validation reporting.
3. `a22a35ce444d5c920eed4828d47a91b4c2eb1bc9` — SPDX SBOM generation now includes `DEPENDS_ON` relationships for dependency edges whose source and target resolve to exact package coordinates already present in the inventory. Unresolved, range-only or ambiguous edges are not guessed into the graph; they remain in source inventory review findings.

No customer UI files or visual styles were changed in this continuation.

## Canonical Supabase read-only snapshot

- The aggregate query against `moreai_skill_packages`, grouped by source repository, returned no rows. There is currently no database evidence that any Customer has imported or ingested Motion, Visual or Scenario packages.
- The latest readiness query returned zero rows for `llm_providers`, `llm_models`, `moreai_worker_capability_snapshots`, `moreai_browser_sessions` and `moreai_browser_capacity_leases`.
- Migration history contains 114 applied versions, including the 14 Phase 09D migrations through `20261116084745`. No migration was applied in this continuation.

## Operational actions not performed

- The OpenFuse/ClamAV Compose stack has not been started on an authorized host. The host-specific ClamAV digest, private network attachment, secret injection, encrypted persistent volume and backup/restore attestation are not available in the connected repository/database interfaces.
- The 56 Motion package batch has not been executed. It requires an authenticated Customer session so package rows are created under the correct owner. The batch UI uses the authenticated Customer API; no Customer access token/session is available in this engineering execution context.
- Visual (2) and Scenario (172) catalog entries can be imported individually using the existing pinned catalog flow, but the current batch button only covers Motion. A dedicated bulk batch action for Visual and Scenario has not yet been implemented. Their recursive source ingestion and validation have not run.
- No provider/model/secret/pricing/entitlement/quota/wallet policy or always-on worker has been provisioned. No fake provider, heartbeat or package records were seeded.
- Strix was deliberately not used, per the product owner's instruction.

## Verification constraints and release state

No tests, build, lint, typecheck, API/browser/worker runtime, provider call, browser screenshot, staging, migration apply or deployment was run. This follows the explicit instruction not to run real testing or staging. The changes are committed source only; route behavior and SBOM output remain unverified at runtime.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED** and Phase 11 remains **BLOCKED**. This source continuation does not claim that any pinned skills are ingested, approved, installed or executable.

## Remaining work in requested order

1. Provision OpenFuse and ClamAV on an authorized always-on host, with immutable image digest, secrets, exact egress allowlist, private network attachment and encrypted persistent profile volume/backup evidence.
2. From an authenticated Customer session, execute the 56 Motion import → recursive ingestion → validation batch. Reconcile dependency closure, exact-version SBOM, dependency graph, nested LICENSE/NOTICE, binary asset provenance and human review; keep the repository with missing root license (`generative-illustration-skills`) blocked.
3. Add and execute resumable Visual and Scenario batch ingestion, then complete exact-version dependency, license, asset and human review evidence. Do not publish/install/enable permissions automatically.
4. Provision real providers and server-side secrets, exact model pricing, routing, wallet conversion/ledger, quota/entitlement policy, then deploy the always-on worker and establish fresh capability heartbeats.
5. Continue Customer dashboard action-to-FastAPI acceptance and security review without direct browser Supabase data access. Phase 10/11 remain gated by the owner's no-test/no-staging instruction and missing release evidence.
