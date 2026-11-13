# Phase 09 — Customer Dashboard Integration Acceptance Matrix

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
PRD authority: `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md` sections 6.1, 16, 17.1, 18.1, 21.5, 22 and 34.  
Scope: source-level Customer UI → FastAPI → worker/engine → Supabase integration reconciliation. This is not runtime acceptance.

## Status definitions

- **CONNECTED (source):** existing UI action uses a typed FastAPI contract and the backend has an owner-scoped durable implementation.
- **PARTIAL / GATED:** some read or execution paths exist, but provider, supervisor, consent, policy, or lifecycle prerequisites are incomplete.
- **UNAVAILABLE / FAIL-CLOSED:** no verified backend/provider contract exists; UI must not simulate success, fabricate data, or create financial/session side effects.
- **NOT VERIFIED:** no real browser, API, worker, provider, or end-to-end verification was run under the product owner's instruction.

## Customer navigation and journey matrix

| PRD surface / journey | Existing UI surface | Backend contract / source integration | Source status | Runtime acceptance |
|---|---|---|---|---|
| Home / Workspace | `home-view.tsx` | Customer context, profile, recent conversations/runs, wallet, entitlements, usage analytics | CONNECTED (source) | NOT VERIFIED |
| Chat history / conversation detail | `chat-view.tsx` | Owner-scoped conversations/messages, workspace context, durable session recovery, event cursor replay | CONNECTED (source) | NOT VERIFIED |
| New conversation / message enqueue | `chat-view.tsx` | Idempotent FastAPI enqueue RPC, agent key, attachment IDs, workspace permission preflight | CONNECTED (source) | NOT VERIFIED |
| Chat streaming / activity timeline | `chat-view.tsx` | Authenticated SSE, Last-Event-ID replay, safe activity projection, agent/planning/tool/approval/resume lifecycle | CONNECTED (source) | NOT VERIFIED |
| Chat stop/cancel | `chat-view.tsx` | Owner-scoped durable cancel RPC and terminal status reconciliation | CONNECTED (source) | NOT VERIFIED |
| Chat retry / regenerate | Existing Chat action surface | No safe customer manual-retry contract; worker auto-retry remains server policy | UNAVAILABLE / FAIL-CLOSED | NOT VERIFIED |
| Chat citations/source display | `chat-view.tsx` | RAG retrieval marker → final response → Agent Run output → owner-scoped conversation history/page → Chat restore | CONNECTED (source) | NOT VERIFIED |
| Agent catalog / Agent Studio | `agent-studio-view.tsx` | Authenticated catalog exposes enabled definitions backed by registered runtime adapters only | CONNECTED (source) | NOT VERIFIED |
| Agent detail / start agent task | `agent-studio-view.tsx`, `chat-view.tsx` | Supported agent key routes through durable Agent Run enqueue and worker dispatcher | CONNECTED (source) | NOT VERIFIED |
| Model selector / provider routing | Existing Chat and catalog surfaces | Server-side Model Router/provider capability policy; browser does not select or call provider directly | PARTIAL / GATED | NOT VERIFIED |
| Tools directory | `tools-catalog-view.tsx` | Authenticated tool catalog; unsafe tools remain unavailable until isolated adapter and policy gates pass | PARTIAL / GATED | NOT VERIFIED |
| Connector authorization/revoke | No verified Customer connector lifecycle surface/API | No verified OAuth connector authorization/revocation contract available | UNAVAILABLE / FAIL-CLOSED | NOT VERIFIED |
| Risky tool confirmation | Chat/Workflow approval surface | Durable owner-scoped approval, pause/resume, single-use consume, transactionally emitted decision/resume events | CONNECTED (source + migration applied) | NOT VERIFIED |
| Tool execution history/output | Chat, Workflow, Tasks | Safe durable activity/step/log projections; raw tool arguments and observations excluded | CONNECTED (source) | NOT VERIFIED |
| Tasks queue / run history | `tasks-view.tsx` | Keyset-paged owner-scoped Agent Runs, status and artifact linkage | CONNECTED (source) | NOT VERIFIED |
| Task detail / progress / steps | `tasks-view.tsx`, `workflow-progress-view.tsx` | Owner-scoped run, safe steps, logs, thinking, progress and replayable events | CONNECTED (source) | NOT VERIFIED |
| Task pause/cancel | Tasks/Workflow/Chat | Durable cancellation and approval pause/resume state machine | CONNECTED (source) | NOT VERIFIED |
| Task retry from checkpoint | Existing Tasks surface | No customer manual retry endpoint; no UI retry is claimed | UNAVAILABLE / FAIL-CLOSED | NOT VERIFIED |
| Task artifacts / download | Tasks, Results, Research, Workflow | Owner-scoped artifact pages, signed download, run relationship | CONNECTED (source) | NOT VERIFIED |
| Workspace files / upload / preview | `files-view.tsx` | Workspace owner/member authorization, private storage, CAS upload, immutable version history, soft delete/restore | CONNECTED (source) | NOT VERIFIED |
| Generated artifacts | `artifacts-result-view.tsx`, Files, Tasks | Private artifact storage, metadata owner checks, signed URL | CONNECTED (source) | NOT VERIFIED |
| Analyse / Knowledge Library | `analyse-view.tsx`, `knowledge-library-view.tsx` | Owner-scoped upload, ingestion, keyset chunk pages, selected-document retrieval and provenance | CONNECTED (source) | NOT VERIFIED |
| Research | `research-view.tsx` | Keyset Agent Run/artifact pages and signed download | CONNECTED (source) | NOT VERIFIED |
| Code Assistant | `code-view.tsx` | Analysis through durable Agent Run; code snapshots/artifacts | PARTIAL / GATED | NOT VERIFIED |
| Python/browser/SWE execution | Tools/Code surfaces | Supervisor isolation, provider, approval and policy gates required; not advertised as active when gates are closed | PARTIAL / GATED | NOT VERIFIED |
| Memory summary / consent / correction / deletion | No dedicated Customer Memory screen | Runtime conversation memory exists; no complete customer memory review/consent/correction/deletion API contract is available | UNAVAILABLE / FAIL-CLOSED | NOT VERIFIED |
| Wallet / credit balance | `benefit-credit-view.tsx`, Home | Owner-scoped wallet, entitlement and quota read APIs | CONNECTED (read-only) | NOT VERIFIED |
| Credit ledger / usage | `token-ledger-view.tsx`, Analytics | Owner-scoped keyset ledger/usage and aggregate analytics | CONNECTED (read-only) | NOT VERIFIED |
| Credit package / top-up / checkout | Account upgrade surface | No verified payment intent, checkout, webhook settlement or credit mutation provider contract | UNAVAILABLE / FAIL-CLOSED | NOT VERIFIED |
| Plans / subscription management | Account upgrade surface | No verified subscription/checkout mutation contract | UNAVAILABLE / FAIL-CLOSED | NOT VERIFIED |
| Partner Wi-Fi access discovery | Partner access banner, Wi-Fi/session views | Eligibility/read-only session history and client-to-API speed test | PARTIAL / GATED | NOT VERIFIED |
| Partner consent / OTP / gateway activation | Captive portal / OTP views | Complete provider-backed consent, OTP, gateway session lifecycle and revalidation contracts are not yet verified | PARTIAL / GATED | NOT VERIFIED |
| Notifications | `notifications-view.tsx` | Owner-scoped list, preferences, mark-read and mark-all-read | CONNECTED (source) | NOT VERIFIED |
| Profile / settings | `profile-settings-view.tsx` | Authenticated profile read/update, password and MFA Auth flows | CONNECTED (source) | NOT VERIFIED |
| Device/session inventory | Devices/security views | Limited device/security data; complete server-side session inventory/revoke lifecycle remains unavailable | PARTIAL / GATED | NOT VERIFIED |
| Help / support | `help-faq-view.tsx` | FAQ/help content exists; no complete support ticket provider/workflow contract | PARTIAL / GATED | NOT VERIFIED |

## API authorization and response contract audit

- 77 route handlers were source-scanned across ten Customer/shared router modules. All 77 route signatures require `customer_principal`.
- Customer WebSocket handlers validate the bearer token and explicitly resolve `require_customer_context`.
- The Customer principal rejects active Partner memberships and privileged Platform assignments; those identities use Partner/Admin API namespaces.
- Owner/member/permission checks are enforced by route/domain services for conversations, runs, artifacts, approvals, knowledge, notifications, learning, wallet/usage and workspaces.
- JSON routes have explicit response models; the intentional transport exceptions are SSE streams, WebSocket envelopes and binary speed-test download.
- Agent Run logs, thinking, event history, WebSocket and Customer SSE use safe activity projections. Terminal SSE returns only final answer text, validated citations and bounded error code.
- This is source inspection only. Live RLS, owner/member/partner/platform cross-tenant denial and real token verification were not exercised.

## Supabase approval migration

- Migration file: `supabase/migrations/20261113182657_moreai_atomic_approval_decision_events.sql`.
- Canonical project: `uunfgimtokhucegqbpce`.
- Supabase migration history records version `20261113182657`.
- The deployed `moreai_decide_tool_approval` RPC calls `moreai_append_approval_lifecycle_event` and contains the `run.resume_queued` event path; verified by read-only schema inspection.
- No approval request/decision/resume worker flow was executed.

## UI preservation

- Existing UI/UX remains protected per AGENTS.md and Master PRD section 16.9.
- UI changes in this increment are limited to Chat lifecycle labels, safe metadata typing, RAG citation restoration and existing citation display. No route/layout/navigation redesign, global token migration, spacing/color/typography change or new visual shell was introduced.
- Before/after screenshots were not captured because browser verification was explicitly not authorized.

## Acceptance and release boundary

This matrix records source integration status, not release acceptance. No tests, lint, typecheck, build, browser checks, API probes, worker execution, provider calls, staging or deployment were performed. The owner explicitly requested no real tests/staging; therefore every runtime acceptance cell remains NOT VERIFIED.

Phase 09 source integration is substantially reconciled, but the following remain open before declaring the phase fully complete:
1. Complete source-level review of all PRD Customer navigation actions and close remaining unavailable/gated contracts only when official backend/provider contracts exist.
2. Review manual retry/regenerate policy and add a customer endpoint only if a safe idempotent retry-from-checkpoint contract is approved.
3. Complete Memory privacy lifecycle and UI only after its schema, consent, retention and deletion API contract is defined.
4. Complete connector OAuth lifecycle, payment/subscription settlement and partner OTP/gateway lifecycle only with real provider contracts and credentials.
5. Runtime acceptance remains intentionally unperformed. Phase 10 End-to-End Integration Verification and Phase 11 Integration Release Gate are dependency-next and not performed.
