# Phase 09 — Customer Workspace CAS Upload & Chat Resume

**Date:** 2026-11-13  
**Execution branch:** `main`  
**Baseline commit:** `73bcd2ee13f92ec53b442f2567e51acb552071a3`  
**Latest implementation commit at report time:** `8cc375696a733c131a4d998395ca43c21be2e91c`  
**Status:** IN PROGRESS — this increment does not complete Phase 09.

## Scope delivered

### 1. Customer workspace upload contract

- Added forward-only migration draft `20261113001500_moreai_customer_workspace_upload_cas.sql`.
- Added server-only `customer_workspace_upload_idempotency` table with RLS deny policies for `anon` and `authenticated`; table access and RPC execution are restricted to `service_role`.
- Added `moreai_customer_workspace_commit_upload` RPC. It validates active workspace membership (owner or active member), exact version-addressed Storage path, SHA-256, 1-byte–2-MB size, idempotency key reuse, and expected-version compare-and-swap.
- Successful commit advances `agent_workspace_files.version` and relies on the existing immutable version-history trigger to archive the previous committed object metadata.
- Storage objects are uploaded to the configured private `MOREAI_WORKSPACE_BUCKET` (default `moreai-artifacts`) with upsert disabled. Existing objects are reused only after byte-length and SHA-256 equality checks.
- Added authenticated `POST /api/v1/customer/workspaces/{workspace_id}/files` with `X-Workspace-Path`, `If-Match` expected version and `Idempotency-Key` headers. Browser requests still pass through the typed FastAPI client; no direct browser Storage or PostgREST access was introduced.
- Ambiguous database commit responses do not trigger destructive object deletion. Immutable object cleanup is deliberately separate from the upload request path.

### 2. Customer Files UI

- Added typed `workspaceApi.uploadFile` to `lib/api/client.ts`.
- Existing Files screen now allows selecting an accessible workspace and uploading a file to that workspace.
- Re-uploading an existing path sends the last observed version as the CAS precondition; successful uploads refresh that workspace's versioned file list.
- Existing artifact upload, workspace history, and signed-download flows remain separate and retain their own semantics.

### 3. Agent Chat conversation resume

- Chat entry without an initial prompt now loads the most recent active persisted conversation (or most recent conversation when none is active) through Customer FastAPI APIs.
- Existing user/assistant messages are restored from server-persisted message records, and subsequent messages continue in that conversation.
- Composer interaction is held while restoration is in progress. Failed history restoration does not fabricate messages and leaves a fresh conversation available.
- This is conversation resume only; attachment ingestion, attachment-to-message/run references and worker-side attachment context are not yet integrated.

## Files changed

- `supabase/migrations/20261113001500_moreai_customer_workspace_upload_cas.sql` — new migration draft
- `apps/api/app/routers/workspaces.py` — customer upload endpoint, path validation, private Storage handling and CAS RPC handoff
- `lib/api/client.ts` — typed workspace upload contract
- `components/views/files-view.tsx` — workspace selection and upload action
- `components/views/chat-view.tsx` — persisted conversation resume

## Safety and data-flow notes

```text
Customer Files UI
  -> typed Customer API client + Supabase Auth bearer token
  -> FastAPI workspace authorization
  -> private Supabase Storage immutable object path
  -> service-role-only CAS RPC
  -> agent_workspace_files + immutable version-history trigger
```

- No service-role key is exposed to the browser.
- No direct browser Supabase Storage/PostgREST access was added.
- No production Supabase schema change was applied. The migration is committed as source only.
- No seed or mock business data was added.
- Workspace membership is checked by FastAPI and rechecked inside the privileged RPC.
- The RPC uses expected-version CAS to reject stale writes and records idempotent commit results.

## Verification and release status

Per product-owner instruction, **no tests, lint, typecheck, build, browser checks, screenshots, staging, API probes, Supabase live writes, or migration apply were run** in this increment. GitHub source readback was used only to confirm the committed source contents; it is not runtime verification.

Production deployment was **not performed**. The Vercel project-list request for the More AI team returned HTTP 403 (not authorized), so project/deployment identity could not be independently confirmed through the connected Vercel account. Separately, `AGENTS.md` requires Phase 11 release gates to pass before production deployment. The same repository tracker records Phase 11 as BLOCKED, with full backend parity, deployed worker/sandbox, real-provider E2E, live RLS/cross-tenant proof, OpenAPI compatibility and release security evidence outstanding. The requested no-test constraint means those release gates cannot be demonstrated for this increment; deploying it would violate the repository's controlling release rule.

## Remaining Phase 09 work

1. Chat attachments: private upload, durable message/run attachment references, safe parsing/limits and worker-side context loading.
2. Agent lifecycle convergence: durable artifact/result linking across Chat, Research, Create, Analyse, Code, Tasks and Workflow; restore prior work and navigate between related runs/artifacts.
3. Captive Gateway: real signed network context, tenant/network verification adapter, consent persistence, OTP provider, and gateway session create/refresh/revoke lifecycle. Keep fail-closed until actual provider configuration exists.
4. Complete customer action inventory and route-to-OpenAPI contract mapping; close unsupported actions without mock success.
5. EduTech course catalog and video delivery API.
6. Image/video generation providers and durable output artifacts.
7. Payment checkout, payment webhook settlement, top-up and subscription entitlement activation. Business pricing/payment policy decisions remain unapproved in the Master PRD.
8. Official customer support channel and ticket lifecycle.
9. Reconcile Analytics with validated historical aggregate endpoints and ensure every Customer dashboard action has a real contract.

## Next dependency-ordered work

Continue Phase 09: implement Chat attachment contracts and worker-side attachment consumption, then unify persisted Agent Run/Artifact relationships across the existing Customer screens. Keep Captive Gateway, payment and provider-backed generation fail-closed until the required external integrations and product decisions exist. Phase 09 must remain IN PROGRESS until the full Customer screen/action inventory is reconciled and the remaining integrations have real contracts and evidence.
