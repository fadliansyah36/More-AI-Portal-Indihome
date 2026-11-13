# Phase 09 — Customer Workspace, Chat Attachments & Run Artifact Integration

**Date:** 2026-11-13  
**Execution branch:** `main`  
**Baseline commit:** `dc514ded8711a59c248b1d657d871be832114225`  
**Latest source commit at report time:** `575e193fd7f1a38310b4b6ca63da44446b9e0fde`  
**Status:** IN PROGRESS — Phase 09 is not complete.

## Scope delivered in this continuation

### 1. Customer workspace immutable upload

- Added `20261113001500_moreai_customer_workspace_upload_cas.sql`.
- Added a server-only idempotency ledger and service-role-only CAS RPC.
- The RPC validates active workspace owner/member access, version-addressed immutable Storage path, SHA-256, file size, idempotency payload consistency, and expected-version compare-and-swap.
- Existing version-history trigger records the previous committed file version.
- Added authenticated FastAPI `POST /api/v1/customer/workspaces/{workspace_id}/files` using `X-Workspace-Path`, `If-Match`, and `Idempotency-Key`.
- Customer Files UI now selects a workspace and uploads to its versioned path through the typed API client. Artifact Storage and workspace versioned Storage remain separate.

### 2. Customer Chat attachment lifecycle

- Added `20261113130000_moreai_chat_attachment_lifecycle.sql`.
- Added private owner-scoped attachment linkage from conversation message → durable Agent Run → artifact metadata, with server-only RLS and a service-role-only atomic enqueue RPC.
- Artifact upload accepts the explicit `chat_attachment` purpose only when the authenticated user owns the target conversation.
- Server enforces a 2-MB per-file limit, MIME allowlist, UTF-8 validation for text, and PDF/JPEG/PNG/WebP signature checks.
- Customer Chat now supports up to 10 attachments and 10 MB total selected bytes. Upload uses the existing private artifact Storage path; no browser service-role access was added.
- Customer message enqueue validates attachment ownership, conversation scope and metadata before persisting message, run and attachment links atomically.
- Replaying the same idempotency key with a different prompt, agent key or attachment set is rejected.
- Conversation history now returns attachment metadata alongside persisted messages.

### 3. Worker-side attachment consumption

- Added `apps/worker/app/attachment_loader.py`.
- Worker resolves attachment links by durable run and user scope, rechecks artifact ownership/purpose/conversation, downloads only from the private artifact bucket, validates byte count and SHA-256, and extracts UTF-8 text, PDF text, or image OCR.
- Per-file extraction is capped at 25,000 characters and total extracted context at 80,000 characters. File content is passed to the agent as explicitly untrusted source material, not trusted instructions.
- Manus, ToolCall and gated SWE runtime registrations receive the attachment loader. Planning uses the same Manus execution runtime.
- Unsupported or unresolved attachments fail closed; worker does not silently omit a requested attachment.

### 4. Agent Run ↔ Artifact lifecycle

- Artifact metadata list now includes its owner-scoped `run_id`.
- Customer Workflow view reads persisted artifacts and renders signed-download actions under the Agent Run that created them.
- This connects worker-generated artifacts with durable run history. It does not yet provide complete cross-screen navigation and linking for every Create/Analyse/Code/Research/Tasks workflow.

### 5. Existing Chat resume and Workspace UI

- Chat restores the most recent active persisted conversation when opened without an initial prompt.
- Customer Files UI provides workspace selection and version-aware upload.
- Existing signed downloads and artifact metadata flows are retained.

## Source files changed

- `supabase/migrations/20261113001500_moreai_customer_workspace_upload_cas.sql`
- `supabase/migrations/20261113130000_moreai_chat_attachment_lifecycle.sql`
- `apps/api/app/routers/workspaces.py`
- `apps/api/app/routers/artifacts.py`
- `apps/api/app/routers/conversations.py`
- `apps/api/app/routers/customer.py`
- `apps/api/app/main.py` — CORS allowlist for workspace CAS and chat attachment headers
- `apps/worker/app/attachment_loader.py`
- `apps/worker/app/registry_factory.py`
- `engine/agents/durable_tool_runtime.py`
- `lib/api/client.ts`
- `components/views/files-view.tsx`
- `components/views/chat-view.tsx`
- `components/views/workflow-progress-view.tsx`

## Supabase production migration status

Canonical project: `MoreAIdb` / `uunfgimtokhucegqbpce` (PostgreSQL 17, ap-southeast-2).

The following nine previously pending source migrations were successfully applied to the production database in dependency order:

1. `moreai_workspace_file_version_history`
2. `moreai_workspace_restore_approval_key`
3. `moreai_customer_learning_progress`
4. `moreai_knowledge_rag_vector`
5. `moreai_durable_knowledge_file_ingestion`
6. `moreai_customer_workspace_upload_cas`
7. `moreai_enable_toolcall_agent`
8. `moreai_workspace_atomic_execution_commit`
9. `moreai_chat_attachment_lifecycle`

Supabase migration history readback records the eight first migrations at versions `20261113002544` through `20261113002624`, and Chat attachment lifecycle at `20261113003132`. This is migration-history confirmation, not application runtime or feature acceptance. No destructive reset/drop/truncate operation was performed.

## Vercel deployment status

Target team: `More AI` / `team_wHMjZ5NapyaF8aYYVs4UUY36`.  
Frontend project: `more-ai-portal-indihome` / `prj_2ge37Xd5uBSUGhn3wPsaHfFcW1UV`.  
Backend project: `more-ai-api` / `prj_L6i6j0ERPcdpZNM1c53hcdPaP9Nn`.

A Production deployment request for the frontend at the then-current `main` commit was rejected by Vercel with HTTP `402 payment_required`, resource `api-deployments-free-per-day`, and `retryAfter=86400`. The API project deployment was not submitted after that quota response. I also attempted the mapped Vercel CLI fallback in a disposable Vercel sandbox: the CLI was not preinstalled, `npx vercel` installed it, but the CLI session was logged out and had no authenticated Vercel credentials. No temporary/preview deployment was substituted for Production. The sandbox was removed. No billing, plan, quota or team settings were changed. The latest attachment/run-artifact commits are therefore not deployed.

## Verification policy and release state

Per the explicit no-real-testing/no-staging instruction, no tests, lint, typecheck, build, browser checks, screenshots, runtime API probes, worker execution, or end-to-end feature checks were run. GitHub source readback and Supabase migration-history readback are not substitutes for runtime verification.

- Phase 09 remains **IN PROGRESS**.
- Phase 10 remains **NOT ACCEPTED** because frontend → FastAPI → worker → provider/tools → Supabase → frontend runtime proof has not been run.
- Phase 11 remains **BLOCKED** because security/RLS/cross-tenant proof, migration validation, API contract acceptance, UI regression evidence, worker/sandbox/provider deployment proof and release evidence are incomplete.
- Production deployment remains blocked by the Vercel daily deployment quota; do not claim that the latest commit is live.

## Remaining Phase 09 scope

1. Full cross-screen Agent Run/Artifact lifecycle: persist and navigate related runs/results across Chat, Research, Create, Analyse, Code, Tasks and Workflow, including artifact-to-run links for all creation flows.
2. Captive Gateway: actual ISP/gateway adapter, signed network context, tenant/network verification, consent persistence, OTP provider and session create/refresh/revoke. Keep unavailable actions fail-closed until the partner gateway integration is configured.
3. Complete Customer screen/action inventory against FastAPI/OpenAPI; remove or explicitly disable any unsupported action without fake success.
4. EduTech catalog, enrollment/lesson contract and protected video delivery.
5. Provider-backed image/video generation with durable run/credit/artifact lifecycle.
6. Payment checkout, verified webhook settlement, top-up and subscription entitlement activation. Pricing/payment product decisions and provider credentials are still prerequisites.
7. Official support channel and ticket lifecycle.
8. Validated historical Analytics aggregation and remaining profile/security/device/Wi-Fi lifecycle parity.

## Next dependency-ordered work

Continue Phase 09. Finish Agent Run/Artifact relationships and the Customer action-to-OpenAPI inventory, then implement the real provider-backed Captive Gateway and other integrations as their contracts/configuration are made available. Phase 10 and Phase 11 cannot be honestly accepted while the requested no-test constraint remains in force.
