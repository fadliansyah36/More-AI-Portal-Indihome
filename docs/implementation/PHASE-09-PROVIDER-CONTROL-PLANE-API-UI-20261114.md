# Phase 09 — Customer Integration & Super Admin Provider Control Plane Increment

Date: 2026-11-14  
Branch: `main`  
PRD: Master PRD v1.2  
Baseline HEAD: `e1167b28808472fc3b7fd1ab4710c513fe10a0dc`

## Scope and architecture reconciliation

The repository's controlling `AGENTS.md` requires preserving the current root Next.js Customer UI and adding backend workspaces alongside it. The Master PRD v1.2 target is a single monorepo with independently deployable application roots (`apps/web`, `apps/admin`, `apps/partner-portal`, `apps/api`, `apps/worker`, and later `apps/captive-portal`), shared `engine/` and `packages/`, and one canonical Supabase project. "Independent" means independently owned/built/deployed applications inside this repository, not separate Git repositories or separate business databases. Existing root app paths must not be moved without a dedicated tested migration.

## Implemented in this increment

- Extended `apps/api/app/routers/admin.py` with permission-gated provider/model/routing endpoints:
  - `GET /api/v1/admin/providers` returns provider metadata, model catalog/pricing/capabilities, and platform routing policies.
  - `POST /api/v1/admin/providers` creates/updates the existing supported LLM provider registry using the existing audited database RPC. Credential readiness is forced to `false`; the endpoint cannot activate a provider by asserting credentials exist.
  - `POST /api/v1/admin/models` creates/updates model metadata using the existing audited RPC.
  - `POST /api/v1/admin/routing-policies` creates/updates platform routing policy using the existing audited RPC.
- Reads require `platform.models.read`; mutations require `platform.models.manage`. The latter is assigned to `super_admin` in the canonical permission matrix.
- Added Pydantic input validation and reused existing database RPCs; no parallel provider engine or direct table mutation path was introduced.
- Updated `components/views/super-admin-view.tsx` with a Provider & Model tab showing registry, model pricing/capabilities, and platform routing. The browser receives metadata only; provider config and credential material are never selected or serialized.
- UI changes are additive within the existing Super Admin view. No existing Customer page, navigation, theme, global tokens, or layout was redesigned.

## Supabase findings

Read-only inspection of canonical project `uunfgimtokhucegqbpce` confirms existing `llm_providers`, `llm_models`, `llm_routing_policies`, `admin_mutation_requests`, and `admin_audit_logs` tables. Existing database RPCs `moreai_admin_mutate_llm_provider`, `moreai_admin_mutate_llm_model`, and `moreai_admin_mutate_llm_route` perform server-side permission checks and append audit records. The provider mutation RPC currently supports Google, OpenAI and Anthropic only. It stores an empty config on create and requires an explicit credentials-ready gate to enable a provider. The new API intentionally always passes `false` for that gate. No migration or production database mutation was made in this increment.

## Customer integration status

Phase 09 remains open. Existing source contracts already cover chat enqueue/stream/replay/cancel, Agent Runs, supported agent/tool/model catalogs, workflow/run lifecycle, task progress, approvals, artifacts, workspace files, Knowledge/RAG, usage/ledger reads, notifications, learning and profile. The acceptance matrix still records gated/unavailable actions including manual retry/regenerate, connector OAuth, Memory consent/correction/deletion, payment/subscription settlement, partner OTP/gateway lifecycle, and complete device/session revoke. These must remain fail-closed until the relevant contracts and provider inputs exist. This increment did not claim full Customer integration completion.

## Vercel and monorepo services

Read-only Vercel inspection found two existing projects attached to the MoreAI team:
- `more-ai-portal-indihome` — existing Next.js Customer application.
- `more-ai-api` — existing FastAPI service.

Both already have Git-connected project identities. The latest deployment records at inspection time were `QUEUED`; they are not treated as READY or release evidence. No Vercel project was created for Admin or Partner Portal because their independent deployable app roots are not yet present as complete applications. Creating projects against missing roots would produce broken deployments. No Vercel settings, environment secrets, aliases, domains, or deployments were changed. The next implementation increment must establish the independent app roots and their authentication/API contracts before creating separate Vercel projects for them.

## Verification and release boundary

Per owner instruction, no tests, lint, typecheck, build, browser/API/worker execution, provider connection, staging, or deployment was run. This is source implementation only and is not Phase 10/11 acceptance. The Vercel deployment queue state is not verification.

## Commits

- API provider/model/routing endpoints: `804c97197487450f7e739be45cebf2371c1d198a`
- Super Admin Provider & Model UI: `ca52ea1537a2feaabbb889cf5aa2959e4e032f56`

## Next phase

Continue **Phase 09 — Customer Integration Completion**: reconcile and connect every remaining Customer action to the actual FastAPI/worker lifecycle; prioritize safe task retry-from-checkpoint contract only after the database/worker idempotency semantics are defined, then Memory privacy lifecycle and remaining partner/payment/OTP contracts. In parallel, complete Super Admin provider secret-reference and non-LLM provider category foundations without claiming vendor activation. Establish independently deployable Admin and Partner Portal app roots within this monorepo, then configure their separate Vercel projects. Phase 10 and Phase 11 remain blocked until explicitly authorized verification and acceptance.
