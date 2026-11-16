# Phase 09 — SBOM fail-closed reconciliation (2026-11-16)

## Scope

Target branch: `main`  
Baseline commit: `96031a918c38d00c31eddba81208e5297da617c9`  
Source commits:
- `ad24baf339ebbf927bbce718ebb2bb542b15eaf7` — fail closed when dependency package-instance graph endpoints are not fully resolvable.
- `7628d110b1e7ce0b262ab38262ad2cd887a369a2` — scope direct dependency-to-lockfile matching to supported sibling lockfiles.

This continuation changes only the FastAPI AI Skills source inventory/validation implementation. It does not change customer-facing UI, API route paths, Supabase schema, migrations, RLS, stored customer records, provider configuration, worker runtime, OpenFuse deployment or production environment variables.

## Changes

### 1. Complete endpoint identity requirement

The dependency graph now treats an edge as unresolved unless it has:
- a resolved target package locator;
- an exact target version (or an exact version field already emitted by the ecosystem parser); and
- an exact source version for non-root package edges.

Workspace-root/importer edges remain exempt from a source package version because the root is not itself a dependency package node.

This prevents a partial lockfile text parse from being reported as a complete package graph when the SPDX writer cannot map an endpoint to an exact package coordinate.

### 2. Conservative format blockers

The following manifest/lockfile formats remain explicit graph blockers until full ecosystem-aware semantics are implemented:
- Pipfile.lock and Go module files (go.mod, go.sum, go.work);
- Cargo.toml;
- composer.json;
- pnpm-lock.yaml;
- yarn.lock;
- pyproject.toml.

The parser continues to preserve inspectable evidence, but these formats cannot pass the dependency graph completeness gate in this state. This is intentionally conservative; it may require human or future resolver work even when a particular package appears simple.

### 3. Sibling lockfile matching

Direct package declarations are no longer satisfied by a same-named package found anywhere in the recursively ingested skill tree. Matching requires:
- same ecosystem;
- normalized package name;
- same parent directory as the declaring manifest; and
- an explicitly supported lockfile for that ecosystem.

Current supported direct-declaration matching is limited to package.json ↔ package-lock.json/npm-shrinkwrap.json, requirements.txt ↔ a sibling poetry.lock/uv.lock only where the exact package inventory permits it, and Gemfile ↔ Gemfile.lock. pyproject.toml, Cargo.toml, composer.json and their incomplete ecosystems remain blocking; their lockfiles are not promoted to complete direct-dependency proofs.

## Architecture and data flow

No runtime architecture or transport contract changed. Existing flow remains:

Customer authenticated request → FastAPI Customer Skills router → pinned GitHub source inventory/registry metadata lookup → owner-scoped Supabase persistence and validation report.

No browser direct database access was introduced. No client-side credentials or service-role access was added.

## Supabase

- No SQL was executed.
- No migration was added or applied.
- No table, policy, RPC, bucket, trigger, index or customer record was changed.
- The previously read-only canonical snapshot remains: 114 applied migrations; Skill package/source-file counts were zero at the last read-only refresh.

## FastAPI and frontend

- Changed file: `apps/api/app/routers/skills.py`.
- Endpoint paths and Pydantic response contracts were not changed.
- No frontend component or route was modified.
- Existing Customer Skills Library visual styles and workflows are unchanged.
- No screenshots were captured; no UI change was made in this increment.

## Verification, security and limitations

- No tests, parser execution, lint, type-check, build, browser interaction, API runtime call, worker/provider execution, staging or deployment was run, in accordance with the product-owner instruction.
- The source edits were committed to `main`; GitHub confirmed the resulting commits. Runtime behavior is not claimed verified.
- Static dependency inventory and registry license metadata remain evidence, not a legal opinion or proof of asset redistribution rights.
- Nested licenses, NOTICE attribution, scripts, media/model assets, non-registry package sources and complete package-manager graph semantics still require review. The new blockers deliberately prevent incomplete lockfile formats from passing validation.
- The 230 pinned skill entrypoints have not been ingested into the Customer registry. This source change does not trigger or impersonate an authenticated Customer batch.
- OpenFuse/ClamAV host, encrypted Docker data-root, secrets, private worker network, provider credentials, model pricing, entitlement/quota/wallet policy and persistent worker heartbeat remain operational prerequisites.

## Deployment

Not deployed. No Vercel build, deploy, alias promotion, rollback or runtime change was initiated.

## Phase decision and next work

Phase 09 remains **IN PROGRESS**. Phase 10 is **NOT ACCEPTED** and Phase 11 remains **BLOCKED**.

The next operational work remains in the agreed order:
1. Provision OpenFuse/ClamAV on the authorized LUKS-backed Linux host and attach the persistent worker on the private network.
2. Add `MOREAI_GITHUB_TOKEN` as an encrypted/sensitive environment variable to Vercel project `more-ai-api` without sharing the value through chat.
3. Run Motion (56) and Visual + Scenario (174) batch ingestion using a genuine authenticated Customer session.
4. Complete the remaining dependency resolver, license, NOTICE, source provenance, asset and SBOM review; retain `NOASSERTION` where evidence is absent.
5. Provision approved provider secrets, models, exact pricing, credit conversion, wallet currency, quota and entitlements.
6. Start the persistent worker and obtain a fresh readiness/heartbeat record.
7. Complete the Customer action-level API/security review. Only after authorized verification can Phase 10/11 be considered.
