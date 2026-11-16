# Phase 09 — Worker Skill snapshot completeness (2026-11-16)

## Scope

Target branch: main  
Worker source commit: 7de3ace815ec296e263a375b650999e4d583b5da  
Changed file: apps/worker/app/skill_resolver.py

This increment closes the source-side mismatch between the Customer/API/Supabase 64-file ingestion limit and the persistent worker's previous 40-file query limit. It also ensures that an approved/published Agent Skill is resolved from the exact file inventory that passed validation.

## Changes

1. The worker source-file query now uses MAX_SKILL_SOURCE_FILES = 64, matching FastAPI and the applied Supabase ingestion RPC.
2. The owner-scoped Skill package query now includes the persisted validation_report.
3. Before loading skill instructions into an Agent Run, the resolver requires a non-empty SPDX file inventory with at most 64 entries.
4. Each SPDX file path must be unique, relative, and have a well-formed SHA-256 checksum.
5. The worker's stored file paths/count must exactly equal the SPDX inventory path set/count. Missing files, extra files, duplicate entries, malformed checksums or path mismatches fail closed.
6. Each source file is re-hashed by the worker and must match both its stored source SHA and the SHA-256 recorded in the validation SBOM. Existing Git blob SHA-1 and root entrypoint provenance checks remain.
7. Existing owner scoping, validated status, approved licence, published status, installed state, permission approval and execution_enabled=true gates remain unchanged.

The result prevents an Agent Run from receiving only a truncated subset of a published Skill package and prevents incomplete or changed source files from being silently used as procedural context.

## Architecture and data flow

Customer approval → canonical FastAPI/Supabase Skill registry → immutable source-file records and validated SPDX file inventory → worker resolver owner/permission/provenance checks → bounded untrusted instruction snapshot → OpenManus Agent Run.

The worker still treats Skill instructions as untrusted user context. The skill cannot grant tools or permissions; the runtime tool registry and server-side grants remain authoritative.

## Supabase and frontend

- No migration was required; the previous two applied migrations align ingestion persistence at 64 files and keep packages pending until explicit SBOM validation.
- No Supabase data, provider, entitlement, permission grant or Skill package was changed.
- No Customer frontend file or visual component was changed.
- Existing Skills Library UI and design system remain intact.

## Verification and limitations

- No tests, lint, type-check, build, runtime, worker execution, provider request, browser/customer session, staging or deployment was performed, per instruction.
- The source commit is present on main, but the persistent worker host has not been provisioned and this resolver change is not confirmed running in production.
- The API's idempotent ingestion recovery commit is also not yet present in the latest observed Vercel API deployment. Do not begin the Customer batch until the approved API deployment and secure GitHub token configuration are complete.
- The 230 pinned entrypoints remain un-ingested. No Skills are published, installed or execution-enabled.

## Phase decision

Phase 09 remains IN PROGRESS. Phase 10 is NOT ACCEPTED and Phase 11 is BLOCKED.

Next: complete OpenFuse host/secret setup, configure the GitHub token in Vercel, deploy the approved API source through the normal release process, run the 230-entry Customer batch, finish remaining SBOM/licence/asset review, configure approved providers and billing, provision the persistent worker and complete the Customer action-level integration audit.
