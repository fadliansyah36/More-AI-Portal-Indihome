# AGENTS.md — MoreAI Engineering Rules

## 1. Canonical repositories and boundaries
- Main implementation repository: https://github.com/fadliansyah36/More-AI-Portal-Indihome
- Backend reference only: https://github.com/YunQiAI/OpenManusWeb
- Canonical Supabase project ref: uunfgimtokhucegqbpce (https://uunfgimtokhucegqbpce.supabase.co).
- The main repository is the canonical product, frontend, integration and deployment target.
- OpenManusWeb is an upstream backend/agent-runtime reference, not a replacement frontend, product shell, design system or deployment target.
- Follow public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md as the product and architecture baseline.

## 2. Non-negotiable UI/UX preservation
Existing UI/UX in the main repository is a protected surface. Backend integration must not redesign it.

Agents MUST NOT, unless separately authorized:
- Replace, rewrite, restructure, rename, delete or redesign existing pages, routes, screen components, navigation, layouts or user journeys.
- Change existing spacing, colors, typography, responsive breakpoints, component hierarchy, copy, iconography, animations or interaction patterns.
- Replace the existing Next.js application with upstream OpenManusWeb UI or introduce a second competing frontend shell.
- Perform global CSS, Tailwind, theme, token or component-library migrations as part of backend integration.
- Remove existing frontend functionality because upstream has a different implementation.

Agents MUST:
- Connect existing screens to real services through typed API clients, hooks, server-side adapters or the smallest viable integration seam.
- Keep existing component contracts and user-visible behavior stable.
- Add UI only for a required PRD workflow genuinely absent from the main repository.
- Build missing UI using the approved MoreAI × IndiHome reference image and Master PRD section 16.
- Treat any UI-file change as exceptional and justify it in the implementation report.

UI change gate: Before editing a UI file, identify the exact missing integration behavior and the smallest required code change. Record baseline screen/route. After the change, provide before/after screenshots and explain every visual difference. Revert unrelated visual differences. No broad restyling.

## 3. Design authority and tokens
- Design authority image: .aistudio/artifacts/brain/4d52674d-4fe2-4441-a5bf-48030e74c0e3/.tempmediaStorage/media_1794208413882_ecc68f24.jpg
- Follow Master PRD section 16: clean white/light cool-gray surfaces, MoreAI/IndiHome red brand actions, deep navy typography, restrained blue/cyan/magenta category accents, green verified/success states, subtle borders and soft elevation.
- The previous Playful Neo-Brutalist / Soft Pastel palette is superseded.
- Do not invent alternative brand palettes or recolor official logo assets.
- Keep semantic tokens centralized in packages/design-tokens when introduced. Avoid scattered raw hex values in new components.
- Do not apply a token migration to existing screens during backend integration. New/missing screens only must follow the new tokens.
- Raster reference colors are approximations unless exact official design-source values are supplied. Record later official-value changes through an ADR.

## 4. Monorepo and ownership
Preserve existing frontend paths and entry points. Introduce backend workspaces alongside them; do not force a disruptive directory move just to match a diagram.

Target structure, adapted with documented evidence:
- apps/web: existing Next.js frontend; preserve current UI
- apps/api: FastAPI trusted business API
- apps/worker: durable background task/agent worker
- apps/sandbox: isolated execution boundary where applicable
- engine/agents, orchestration, tools, llm, memory, credits, entitlements, network_partnership
- packages/api-client, types, validation, design-tokens
- vendor/openmanusweb: pristine traceable upstream snapshot
- supabase/migrations and supabase/tests
- infrastructure/ and docs/

- The existing repository root may remain the Next.js web application until a safe, tested workspace transition is planned. Do not move app/, components/, hooks/, lib/, types/, public/ or root build configuration without a dedicated migration plan and approval.
- Keep vendor/openmanusweb pristine. Adapted production code belongs in engine/ or apps/api.
- Keep Python and JS/TS dependencies independently reproducible and document commands.
- Maintain a typed TypeScript API client from FastAPI OpenAPI where feasible.
- Do not create a second canonical business database. Supabase PostgreSQL is the source of truth.

## 5. Mandatory integration-first phase gate
No additional PRD feature/domain implementation may begin until phases 00–11 below pass, or a written exception is approved by the product owner.

0. Phase 00 — Repository Baseline & UI Freeze: inventory routes/components/API/schema/RLS/config; record build/test baseline and UI screenshots; identify protected paths.
1. Phase 01 — Upstream Source Pin & Provenance: inspect license, exact commit SHA, full tree, dependencies and security risks; produce manifest, hashes, notices and mapping.
2. Phase 02 — Monorepo Backend Workspace Foundation: add isolated API/worker/engine/package workspaces without breaking frontend paths.
3. Phase 03 — Complete Backend Source Copy: preserve upstream snapshot under vendor/openmanusweb; prove completeness with manifest/hash comparison; document exclusions.
4. Phase 04 — Backend Adaptation & Security Hardening: adapt agent/planner/executor/LLM/tools; remove unsafe global process state; persist durable runs; isolate browser/Python execution and enforce SSRF/network/resource/secret boundaries.
5. Phase 05 — Supabase Schema Reconciliation: inspect existing tables, migrations, constraints, indexes, RLS, functions, triggers and storage policies. Map to existing schema first. Add only necessary forward-only, idempotent migrations. Never reset or destructively recreate the project.
6. Phase 06 — FastAPI Core & OpenAPI Contract: versioned endpoints, Pydantic schemas, auth/tenant context, consistent errors, pagination, idempotency, correlation IDs, health/readiness and generated OpenAPI.
7. Phase 07 — Worker, Durable Runs & Event Lifecycle: queue/outbox, persisted run/step/event/checkpoint state, retry, cancellation, timeout and recovery. Long-running work must not depend on an HTTP request staying open.
8. Phase 08 — LLM Gateway & Tool Runtime Integration: provider/model routing, streaming/tool-call normalization, metering, retry/circuit breaker and isolated tools with policy/approval.
9. Phase 09 — Existing Frontend API Integration: connect current Next.js screens through typed API client and minimal adapters. Replace demo/fallback responses with real API behavior progressively without changing visual UI.
10. Phase 10 — End-to-End Integration Verification: prove frontend → FastAPI → worker/engine → LLM/tool → Supabase persistence → events/status → frontend. Verify auth, RLS, tenant isolation, streaming, cancellation, retry, idempotency, artifacts, credits and partner session boundaries.
11. Phase 11 — Integration Release Gate: CI/build/lint/type checks, migration validation, API contract tests, RLS/security tests, end-to-end smoke tests, UI regression screenshots and evidence report must pass.

After Phase 11, continue with post-integration product phases in Master PRD section 22. Do not skip or reorder dependencies without a documented reason and acceptance evidence.

## 6. Backend and API architecture
- FastAPI is the trusted business API boundary. Web/mobile/admin/partner/captive clients call backend APIs; clients never call LLM providers directly.
- Route handlers validate transport input and delegate to domain services. Do not put business policy in route handlers or React components.
- Backend owns authorization, tenant scope, entitlements, credit calculations, provider selection, payment state and network verification decisions.
- Supabase PostgreSQL is canonical persistence. Use Auth, Storage, Realtime and pgvector through approved access patterns.
- Never expose Supabase service-role credentials, LLM keys, payment secrets or gateway secrets to browser bundles.
- Enforce authorization in backend and RLS as defense in depth. Never trust client-supplied role, workspace, credit balance, network status or entitlement claims.
- Mutations require idempotency where duplicate delivery can create financial, task or session side effects.
- Use UTC timestamps, stable UUIDs, request/trace correlation IDs, explicit error contracts and cursor pagination.
- Long-running tasks use durable workers and persisted state; expose progress/events through approved realtime or polling contracts.
- Every LLM call records provider/model, usage, latency, status, cost/pricing version and credit/entitlement accounting.
- Keep Wallet, immutable Ledger, Quota and Entitlement distinct.

## 7. Upstream source-copy and adaptation
- Pin a specific upstream commit SHA before copying. A moving branch is not reproducible.
- Preserve upstream license, copyright and attribution notices.
- Keep the original snapshot separate from adapted code. Produce a manifest with path, size/hash, source commit, destination path and adaptation status.
- Document every excluded file and reason (secrets, generated artifacts, caches, irrelevant UI, binaries, unsafe code or license issue).
- Do not blindly trust upstream security claims or copy unsafe patterns into production.
- Review and replace in-memory-only sessions/plans/logs, process-global CWD/environment mutation and unsafe execution patterns.
- Python execution requires isolated container/microVM boundaries, non-root identity, resource/time limits, process-tree termination, no host mounts/secrets and network disabled by default.
- Browser automation requires isolated contexts, domain controls, SSRF/private-IP protections, download controls and approvals for high-impact actions.
- Keep upstream source references and adapted-file mapping current after every port.

## 8. Supabase safety and migrations
- Confirm project ref uunfgimtokhucegqbpce before every schema-affecting operation.
- Inspect actual schema and migration history before planning DDL. Known table names do not prove columns or policies.
- Never drop, truncate, reset or recreate production tables/storage as a shortcut.
- Migrations must be versioned, forward-only, repeatable/idempotent where practical, reviewed, and accompanied by rollback/mitigation notes.
- Add RLS policies and tests for owner, member, partner, admin and cross-tenant denial paths as applicable.
- Never write service-role secrets into source, docs, commits, logs or client environment variables.
- Separate local/test data from production. Never seed fake business activity into production to make a screen look populated.

## 9. No fake integration or completion claims
- Do not use mock data, hardcoded success, local fallback answers, simulated credits, fabricated network status or placeholder endpoints as proof of integration.
- Demo data may exist only in isolated tests/storybooks and must never be presented as live production data.
- A directory, copied file, UI mockup, endpoint stub, green-looking badge or successful compile alone does not mean a feature is complete.
- Report actual tested endpoints, database objects, policies, UI routes, test commands/results, commit SHAs, limitations and unverified items.
- If a connector, credential, external service or test environment is unavailable, state the blocker; never invent success.

## 10. Testing, regression and release
- Establish a baseline before modifications and run the same checks after each integration increment.
- Required checks as applicable: Python lint/type/unit tests, frontend lint/type/build, API schema compatibility, migration apply/validation, RLS tests, worker tests, security tests, contract tests and browser E2E smoke tests.
- Test 360, 390, 768, 1024 and 1440 px for affected existing journeys.
- Capture screenshots for protected UI routes before/after any UI file change.
- Verify loading, empty, error, retry, unauthorized, forbidden, timeout, cancellation and success states.
- Do not deploy production until required checks and release gates pass. Do not deploy intermediate/incomplete work.

## 11. Required implementation report
At the end of each phase, update a repository document under docs/implementation/ (create the directory if absent) containing:
- phase and scope; baseline and target commit SHAs;
- source files copied/adapted and manifest status;
- architecture and data-flow changes;
- Supabase schema/migration/RLS changes;
- FastAPI endpoints and OpenAPI changes;
- frontend routes/components touched and UI-preservation evidence;
- tests run with exact results; security review and limitations;
- deployment status (or explicitly not deployed); next phase and blockers.

## 12. Agent operating sequence
Always follow: READ → UNDERSTAND → INSPECT → RECONCILE REPO + SUPABASE → PLAN → IMPLEMENT → MIGRATE → TEST → SECURITY REVIEW → UI REGRESSION REVIEW → REPORT.
Do not skip inspection, overwrite user work, silently change scope, or begin post-integration features before mandatory Phase 11 passes.
