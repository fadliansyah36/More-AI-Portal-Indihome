# Phase 09 — Motion Skills aggregator source reconciliation

Date: 2026-11-16  
Target branch: `main`  
Purpose: reconcile the additional product-owner reference `iart-ai/motion-skills` with the existing pinned Motion child-pack ingestion model.

## Reviewed immutable source

| Field | Evidence |
|---|---|
| Repository | https://github.com/iart-ai/motion-skills |
| Default branch | `master` |
| Reviewed commit | `9b9ce041932da787cc856d4cdf23afb6cd13d4bf` |
| Commit tree | `95b0c640e73965da9d21fe37fad7014218f0c3cb` |
| Root license | MIT, Copyright (c) 2026 iart.ai |
| Root LICENSE blob | `a61b911146037f2ef312f67e9b45de6c99b7f870` |
| Root README blob | `3c2554af383b23c66625b81b9b3ad3c2d153d4db` |
| Recursive tree | 12 entries, not truncated |
| Skill entrypoints in this repository | 0 `SKILL.md` files |

## Repository role and integration decision

The `motion-skills` repository is an **aggregator/catalogue**, not itself an installable skill pack. Its README enumerates 19 separately installable repositories containing 56 skill entrypoints. Its root tree contains the README, MIT license, showcase media/HTML, and verification scripts; it contains no `SKILL.md` entrypoint.

Therefore:

1. Keep this repository as a pinned source-catalogue and provenance reference; do not import the aggregator as a runnable skill.
2. Continue importing individual skill entrypoints from the 19 child repositories through the existing MoreAI Skill Registry, with each child repository pinned to its own reviewed immutable commit.
3. Preserve the root MIT notice when copying any substantial content from this aggregator.
4. Do not infer that the aggregator's MIT license automatically covers every external asset, provider, model, package, or third-party item referenced by the child packs.
5. Keep the current fail-closed publication and execution gates. A successful source import or static inventory does not grant publication, installation, tool permissions, or runtime execution.
6. The aggregator's MCP service reference is not authorization to connect to iArt or to use its API. Any future provider connection requires a separate provider adapter, credential, pricing, entitlement, wallet, and security review.

## Existing MoreAI implementation alignment

The current `apps/api/app/routers/skills.py` already models Motion as 19 individually pinned `iart-ai/*-skills` child repositories. The Customer Skills Library already exposes a sequential Motion ingestion action for the 56 child-pack entrypoints. This is the correct execution model; no second Motion registry, media worker, job ledger, provider router, or Create Studio surface should be introduced.

The current source catalog has the following explicit boundaries:
- Pinned child repository and commit allowlist.
- Entry point restricted to `skills/*/SKILL.md`.
- Recursive ingestion at the pinned commit with Git blob and SHA-256 verification.
- Static dependency/license/SBOM review.
- Publication remains blocked until required evidence and reviewer approval exist.

The 56-skill batch has not been executed in this engineering context. It requires an authenticated Customer session and must remain a user-owned import through FastAPI. No package rows should be seeded with a service account or fabricated owner.

## Outstanding source-governance work

- Complete recursive per-child-repository inventories for all 19 packs.
- Close exact dependency graph resolution and package license metadata; unresolved coordinates remain blockers.
- Review nested LICENSE/NOTICE files, binary asset rights, attribution, trademark references and script safety.
- Reconcile all 56 entrypoints against the pinned child commits and the MoreAI catalog result.
- Record copy/adapt/archive/exclude decisions per file before any bulk source copy.
- Obtain human review for any license, asset, dependency or provider rights ambiguity.

## Execution boundary

No source code from this aggregator was imported. No dependency was installed, no script was executed, no external provider was called, and no Customer data, Supabase schema/data, staging environment, or deployment was changed. No tests, builds, lint, type-check, browser/API/worker runtime verification were run.

This report is source-governance evidence only. It does not mark Phase 09, Phase 10, Phase 11, or the broader P1 source-governance work as complete.
