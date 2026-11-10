# AGENTS.md — MoreAI Engineering Rules

## 1. Canonical repositories and boundaries
- Main implementation repository: https://github.com/fadliansyah36/More-AI-Portal-Indihome
- Backend reference only: https://github.com/YunQiAI/OpenManusWeb
- Canonical Supabase project ref: uunfgimtokhucegqbpce (https://uunfgimtokhucegqbpce.supabase.co).
- The main repository is the canonical product, frontend, integration and deployment target.
- OpenManusWeb is the **authoritative source codebase for MoreAI's backend capabilities**. We must copy and integrate its complete backend/system implementation: architecture, domain logic, agents, engines, tools, workflows, orchestration, LLM layer, API/server logic, configuration and supporting runtime code. The only product layer not adopted from upstream is its user-facing frontend/UI, because the main repository already owns that surface. Do not downgrade this mandate to selective inspiration or a partial port.
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
- vendor/openmanusweb: complete pristine upstream source snapshot, including files not directly deployed in production, for provenance and reproducibility
- supabase/migrations and supabase/tests
- infrastructure/ and docs/

- The existing repository root may remain the Next.js web application until a safe, tested workspace transition is planned. Do not move app/, components/, hooks/, lib/, types/, public/ or root build configuration without a dedicated migration plan and approval.
- Keep vendor/openmanusweb pristine. Adapted production code belongs in engine/ or apps/api.
- Keep Python and JS/TS dependencies independently reproducible and document commands.
- Maintain a typed TypeScript API client from FastAPI OpenAPI where feasible.
- Do not create a second canonical business database. Supabase PostgreSQL is the source of truth.

## 5. Mandatory full-backend-copy and integration-first phase gate
No additional PRD feature/domain implementation may begin until phases 00–11 below pass, or a written exception is approved by the product owner.

0. Phase 00 — Repository Baseline & UI Freeze: inventory routes/components/API/schema/RLS/config; record build/test baseline and UI screenshots; identify protected paths.
1. Phase 01 — Upstream Source Pin & Provenance: inspect license, exact commit SHA, full tree, dependencies and security risks; produce manifest, hashes, notices and a file-by-file classification (backend/runtime, frontend/UI, docs/examples/assets, build/config).
2. Phase 02 — Monorepo Backend Workspace Foundation: add isolated API/worker/engine/package workspaces without breaking frontend paths; preserve upstream package/module boundaries where practical.
3. Phase 03 — Complete Upstream Source Copy: copy the entire pinned upstream repository into vendor/openmanusweb (including backend, system, architecture, domain logic, agent/engine, tools, workflow, orchestration, LLM, API/server, configs, dependency/build files, docs, examples, assets and license notices). This is a mandatory full repository snapshot, not a selective code sample. Prove completeness with source-to-destination path, size and hash comparison. Keep upstream frontend/UI source in the archival snapshot for provenance if present, but do not mount, deploy, merge or use it as MoreAI's product frontend. Document any exclusions only for secrets, generated caches, VCS internals or legally/security-prohibited material, with exact path and reason.
4. Phase 04 — Full Backend Integration & Security Hardening: integrate all upstream backend capabilities and their dependency graph into MoreAI's backend workspaces. Preserve behavior and domain coverage; adapt only interfaces needed for FastAPI, Supabase, multi-tenant authorization, durable workers and MoreAI policies. Remove unsafe global process state; persist durable runs; isolate browser/Python execution and enforce SSRF/network/resource/secret boundaries. No backend domain/engine/workflow may be silently omitted.
5. Phase 05 — Supabase Schema Reconciliation: inspect existing tables, migrations, constraints, indexes, RLS, functions, triggers and storage policies. Map to existing schema first. Add only necessary forward-only, idempotent migrations. Never reset or destructively recreate the project.
6. Phase 06 — FastAPI Core & OpenAPI Contract: versioned endpoints, Pydantic schemas, auth/tenant context, consistent errors, pagination, idempotency, correlation IDs, health/readiness and generated OpenAPI.
7. Phase 07 — Worker, Durable Runs & Event Lifecycle: integrate upstream workflow/agent execution lifecycle end-to-end, with queue/outbox, persisted run/step/event/checkpoint state, retry, cancellation, timeout and recovery. Long-running work must not depend on an HTTP request staying open.
8. Phase 08 — Complete LLM, Tool, Workflow & Orchestration Integration: connect the upstream LLM stack, model/provider clients, prompt/schema contracts, agent types, planner, flow/orchestration, tool registry and all supported tools. Add MoreAI gateway/routing/metering/entitlement controls without deleting upstream capability. Isolated tools require policy/approval.
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

## 7. Mandatory complete upstream source-copy and backend parity
- Pin a specific upstream commit SHA before copying. Pinned source snapshot used for Phase 01–03: branch `dev_web_app`, commit `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`, tree `41258ca11d4299beab17e4172fbcf8303eac1a6b` (111 tracked files; recursive tree untruncated). Upstream `main` at audit was `8d6dda9c27043ab0d3d5c7ae18062eae56763fe5` with 63 tracked files and lacks the `app/web` server layer; it was not selected. Future source updates require a new explicit pin and manifest.
- Preserve upstream license, copyright and attribution notices.
- Copy the complete upstream repository tree to vendor/openmanusweb as an immutable source snapshot. Keep it separate from adapted production code. Produce a manifest with every source path, blob SHA/hash, size, source commit, destination path and status (copied, excluded with reason, adapted/ported to production module). The pinned `dev_web_app` execution commit contains 111 tracked files (tree `41258ca11d4299beab17e4172fbcf8303eac1a6b`); 111/111 files are now copied and destination Git blob SHAs match source. See `docs/implementation/openmanusweb-source-manifest.json`.
- Backend parity is mandatory: inventory and integrate every backend-capable module, domain, agent type, planner, flow, prompt, schema, LLM feature, tool, API/server function, runtime/configuration and workflow. If a capability cannot be used in production, document the technical/security blocker and provide an equivalent safe implementation or an explicit product-owner exception.
- Frontend exclusion means exclude upstream user-facing web pages/templates/client assets from the active MoreAI product UI. It does not mean omit backend/server APIs, session handling, streaming, event endpoints or service-layer logic merely because they were originally hosted by an upstream web server. Re-express those server capabilities through FastAPI and the existing MoreAI frontend.
- Preserve docs, examples, configuration templates, tests and assets in the source snapshot. Promote relevant backend tests/fixtures and configuration into the integrated system as appropriate.
- Document every excluded file and reason (secrets, generated artifacts, caches, irrelevant UI, binaries, unsafe code or license issue).
- Do not blindly trust upstream security claims or copy unsafe patterns into production. The source snapshot must still preserve upstream code faithfully; hardening belongs in separate adapted production modules/patches, not silent edits to the pristine vendor copy.
- Review and replace in-memory-only sessions/plans/logs, process-global CWD/environment mutation and unsafe execution patterns.
- Python execution requires isolated container/microVM boundaries, non-root identity, resource/time limits, process-tree termination, no host mounts/secrets and network disabled by default.
- Browser automation requires isolated contexts, domain controls, SSRF/private-IP protections, download controls and approvals for high-impact actions.
- Keep upstream source references and adapted-file mapping current after every port. Track backend capability parity by feature/module, not only by file count.

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
Always follow: READ → UNDERSTAND → INSPECT UPSTREAM FULL TREE → CLASSIFY FRONTEND VS BACKEND → PIN SOURCE → COPY COMPLETE SOURCE → RECONCILE REPO + SUPABASE → PORT/INTEGRATE ALL BACKEND CAPABILITIES → IMPLEMENT FASTAPI/WORKER/API CONTRACTS → CONNECT EXISTING FRONTEND → MIGRATE → TEST → SECURITY REVIEW → UI REGRESSION REVIEW → REPORT.
Do not skip inspection, overwrite user work, silently change scope, or begin post-integration features before mandatory Phase 11 passes.


## Frontend ↔ FastAPI ↔ Supabase Access Boundary (Mandatory)

- The browser may connect directly to Supabase **Auth only**: sign-in, sign-up, OAuth, session retrieval/refresh, sign-out, password recovery and MFA flows.
- The browser must not call Supabase PostgREST/table CRUD, Storage, RPC, Realtime, Edge Functions or database subscriptions directly.
- All business/application data and actions must use the existing frontend API client and the FastAPI service: conversations, agent definitions/runs/events, tools, artifacts, wallet/ledger, credits, quota, entitlements, partners, network verification, admin operations and analytics.
- FastAPI validates the Supabase access token, resolves the authenticated principal and performs tenant/ownership/RBAC/ABAC checks before repository access. Privileged server operations must use the existing server-only repository boundary and explicit user/workspace/partner filters.
- The Supabase service-role key and all LLM/provider credentials are server-only. Never expose them through `NEXT_PUBLIC_*`, browser bundles, client components, source maps, logs or build artifacts.
- Use `NEXT_PUBLIC_SUPABASE_URL` and a publishable/anon key only for Supabase Auth. Use `NEXT_PUBLIC_MOREAI_API_URL` for FastAPI.
- Do not add a new direct Supabase data client to a UI component. Reuse `lib/api/client.ts`; add or extend typed FastAPI contracts instead.
- API and worker execution remain fail-closed until provider routing, entitlements, quota policies, credit wallets, secret references and worker health are verified. Do not enqueue jobs that cannot be processed.
- Any exception to this boundary requires an explicit PRD/ADR update and security review before implementation.
