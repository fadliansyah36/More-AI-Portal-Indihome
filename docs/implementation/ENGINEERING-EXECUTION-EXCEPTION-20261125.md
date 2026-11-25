# Engineering Execution Exception — Full MoreAI Backend Completion

- Date: 2026-11-25
- Target: `main`
- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Canonical Supabase project: `uunfgimtokhucegqbpce`
- Authorization basis: explicit project-owner instruction in the MoreAI implementation conversation dated 2026-11-25.

## Authorization

The project owner explicitly authorizes implementation work to continue directly on `main` for Task 1 and the mandatory integration phases 04–09, notwithstanding the source-only restriction in Master PRD §37.3 and the pre-Phase-11 implementation gate in AGENTS.md §5.

This is a narrow, written engineering exception for completion of the already specified integration scope. It does not authorize new product domains, UI redesign, a second runtime/database, or changes to the canonical architecture.

## Scope and sequence

1. Complete Task 1 PostgreSQL semantic reconciliation.
2. Continue Phase 04 backend integration and security hardening.
3. Complete Phase 05 schema reconciliation.
4. Complete Phase 06 FastAPI contracts.
5. Complete Phase 07 durable worker lifecycle.
6. Complete Phase 08 LLM/tools/orchestration.
7. Complete Phase 09 existing frontend integration.

Phases 10 and 11 remain verification and release gates and must not be represented as complete without evidence. Work must preserve the existing frontend UI/UX, keep OpenManus as the only Agent Runtime, FastAPI as the business API, and Supabase PostgreSQL as the sole canonical business database.

## Restrictions that remain in force

This exception does **not** authorize:
- applying migrations or making production database/data/Auth/Storage mutations;
- external provider calls or credential use;
- staging or production deployment;
- test, build, lint, type-check, or E2E execution while those activities remain prohibited by the governing PRD or explicit operating instruction;
- importing third-party skill packages before per-file provenance, license, dependency, and security review is closed;
- claiming runtime, database activation, security acceptance, or phase completion from source changes alone.

Source implementation, focused regression-source additions, code review, and repository commits are authorized. Each increment must be committed on `main`, and reports must distinguish source implementation from database activation and runtime verification.

## Completion reporting

A module may be called complete only when its implementation and lifecycle are present and its required verification is permitted and evidenced. Otherwise report the exact status as implemented-but-unverified, blocked, or not implemented. Do not downgrade the task to audit-only documentation work.
