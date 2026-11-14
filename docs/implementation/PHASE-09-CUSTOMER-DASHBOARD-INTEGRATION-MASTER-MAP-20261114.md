# Phase 09 — Customer Dashboard Integration Master Map

Date: 2026-11-14  
Branch: `main`  
Purpose: dependency-ordered implementation map for completing the existing Customer dashboard against the canonical FastAPI/OpenManus/Supabase backend. This is a source inspection artifact, not a completion or runtime acceptance report.

## Non-negotiable boundaries

- Preserve the existing Next.js customer UI and its CSS, typography, colors, buttons, navigation and responsive behavior.
- Browser uses Supabase Auth only. All business reads/writes/streaming go through `lib/api/client.ts` → FastAPI → server-side Supabase repositories/RPC.
- OpenManus is the sole Agent Runtime. OpenFuse capabilities are adapted behind existing FastAPI/worker boundaries; no second runtime, database or frontend.
- Durable Agent Run owns scheduling/workflow execution, progress, approval, cancellation, retry and recovery.
- No mock data, simulated success, fabricated credits, or false availability.
- User restriction for this implementation cycle: no tests, lint, build, browser/API/worker runtime probes, provider calls, staging, deployment or Supabase mutation. Source-only work cannot establish runtime acceptance.

## Existing integration baseline (source inspection)

| Customer surface | Existing integration seam | Current evidence / remaining gap |
|---|---|---|
| Home dashboard | `GET /api/v1/customer/*`, typed Customer API | Recent runs, wallet and entitlement are backend-backed; preserve unavailable vs empty states. |
| Chat | Conversation + enqueue + Agent Run SSE | Live durable chat path exists. Model list is informational; backend router/entitlement/quota remains authoritative. |
| Agent Studio | Agent catalog, tool catalog, saved Agent configuration CRUD | Manus/Planning/ToolCall runtime contracts exist. Additional skills need a distinct governed Skill Registry; tool catalog is not a skill catalog. |
| Tasks | Cursor-paginated Agent Run history, run detail, retry/cancel | Retry creates a new run and is guarded against duplicate side effects. |
| Workflow Progress | Agent Run SSE, steps, activity, approvals, retry | Durable Run is the workflow authority. Do not introduce OpenFuse task/goal persistence as a second engine. |
| Personal Memory | Customer personal-memory APIs + consent/retention CRUD | User-authored memory lifecycle is implemented. This is distinct from conversation, episodic, semantic and procedural runtime memory. |
| Knowledge Library | Tenant/owner-scoped document ingestion, chunking and retrieval | RAG/file ingestion exists; reconcile indexing lifecycle, deletion/re-index and citation traceability before calling it complete. |
| Files / Artifacts | Artifact metadata, upload and signed download APIs | Keep metadata owner-scoped; ensure artifact lifecycle and orphan-object cleanup are addressed. |
| Profile / Account | Supabase Auth + FastAPI profile/preferences | Auth-only browser access remains mandatory. |
| Notifications | Customer notifications and preference APIs | Preserve cursor pagination and owner scope. |
| Wallet / Usage / Quota | Wallet, immutable ledger, usage, entitlement and quota APIs | Do not fabricate top-up/checkout. Payment provider contract and settlement remain gated. |
| Network / Wi-Fi | Network session and access-code APIs | Gateway challenge/verification/activation lifecycle and provider contract remain gated. |
| EduTech | Learning APIs, saved curriculum, lesson reader and assessment | Lesson navigation/persistence has source integration; completion migration and runtime proof remain open. |
| Media / Create Studio | Worker-side media adapters and artifact projection | Provider availability, entitlement, metering and artifact gates must remain fail-closed. |
| Browser / Computer | OpenFuse patterns + isolated supervisor interfaces | Do not advertise as active without deployed supervisor, enforced egress, scanner and explicit approval. |
| Gmail / Calendar | OpenFuse Google OAuth/API patterns | Implement through Connections Center and existing connection persistence; no OpenFuse session/store. |

## OpenFuse capability disposition

| Capability | Canonical MoreAI owner | Integration rule |
|---|---|---|
| Agent execution | OpenManus durable worker | OpenFuse is not another agent runtime. |
| Task/goal/monitor semantics | Agent Run + Workflow projection | Persist run/step/event/checkpoint in canonical schema. |
| OAuth and Google | FastAPI Connections Center + provider adapters | Bind OAuth state to tenant/subject/connection intent; encrypted server-side credentials; least-privilege scopes. |
| Browser/computer | Isolated sandbox/browser supervisor invoked by OpenManus tools | SSRF, DNS rebinding, redirect/subresource egress, download scanning, session ownership and approvals are mandatory. |
| Search | Existing provider adapter and tool registry | Provider allowlist, bounded response, metering and untrusted-result handling. |
| Vault | Existing server-side secret boundary | Versioned AEAD envelope and tenant/subject/provider/connection AAD; no browser secrets. |
| Durable work | Existing Worker lease/checkpoint/outbox lifecycle | No process-local state as source of truth. |
| Documents/artifacts | Existing Supabase Storage + artifact API | Owner/tenant authorization, immutable versions, signed short-lived access, garbage collection. |

## Skill Intelligence Platform — required target contract

The current tool catalog is not a skill registry. Before exposing Scenario/Visual skills to customers, implement one canonical Skill Registry/Resolver with:

1. Immutable source provenance: source repository/ref/commit/path/blob SHA, license, author attribution, import time and source URL.
2. Immutable version: semantic version or content digest, manifest digest, dependency lock and compatibility metadata.
3. Trust lifecycle: `discovered → imported → validated → approved → published → installed → resolved → executed → deprecated`.
4. Validation: manifest schema, nested references, archive traversal/symlink defenses, file-count/expanded-size limits, license allowlist/manual review, secret scanning, dependency/SBOM evidence and prompt-injection classification.
5. Permission model: declared capabilities, network destinations, filesystem scope, data classes, approval mode, resource/time limits; import never grants execution permission.
6. Runtime resolution: tenant/workspace entitlement and user-granted permissions resolved server-side for each Agent Run; skill content is untrusted input, never policy.
7. Execution: skill is an instruction/asset package consumed by the existing OpenManus runtime and registered safe tools; no new agent runtime.
8. Audit: skill version/hash, resolved permissions, approval, Agent Run ID, execution result and usage are durably recorded.
9. UI: add a Skills surface only if no existing customer route can host the required browse/detail/install/permission workflow; follow existing MoreAI × IndiHome tokens and preserve all existing screens.

## Dependency-ordered implementation sequence

### A. Close backend parity and security blockers (Phase 04 / 07 / 08)
- Complete OpenManus server/session/log/exception/tool behavior parity.
- Complete durable recovery, lease fencing, cancellation, approval resume and outbox semantics.
- Finish safe artifact, search, workspace and remaining tool adapters.
- Keep Bash/Python/browser fail-closed until supervisor deployment and threat-model acceptance are explicitly authorized.
- Reconcile provider routing and configuration without seeding fabricated production records.
- Integrate OpenFuse Google OAuth/Gmail/Calendar through FastAPI Connections Center.
- Complete Memory Coordinator as one service coordinating working, conversation, long-term, episodic, semantic and procedural stores; Personal Memory remains consented user-authored input, not a substitute for all memory types.

### B. Close FastAPI and Supabase contracts (Phase 05 / 06)
- Reconcile each endpoint against Pydantic response/request models, ownership and tenant scope.
- Ensure every side-effecting mutation has idempotency and correlation identifiers.
- Verify migrations, RLS, grants, RPC search paths and storage policies through approved schema workflow.
- No destructive DDL; no browser direct PostgREST/Storage/RPC/Realtime.

### C. Finish customer dashboard integration (Phase 09)
- Inventory every customer navigation destination and every action in each screen.
- For each screen, map loading/empty/error/unauthorized/success states to a real endpoint.
- Remove static/demo fallback data and simulated action success.
- Connect remaining account/profile, notifications, workspace/files, knowledge, wallet/usage, Agent Studio, Workflow, EduTech and media actions to typed API methods.
- Add Skills/Connections/Scheduling UI only where a PRD workflow is genuinely missing; use existing layout and tokens.
- Keep UI changes minimal and document route/component touched and visual baseline evidence limitations.

### D. Acceptance gate (Phase 10 / 11)
- Requires explicit authorization to run integration/security tests and a safe test environment. Until then, Phase 10/11 cannot be marked accepted and production deployment/worker activation remains blocked.

## Current cycle outcome

This map consolidates source findings from the current `main` tree and existing Phase 04/09 reports. It does not change application behavior, does not claim any new feature is implemented, and does not waive AGENTS.md gates. The next code increment should select one complete vertical slice and carry it through API contract, worker/domain behavior, persistence contract, typed client and existing UI before moving to the next slice.
