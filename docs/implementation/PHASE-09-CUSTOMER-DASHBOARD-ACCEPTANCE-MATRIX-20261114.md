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
| Chat retry / regenerate | `chat-view.tsx` | Owner-scoped idempotent safe-replay endpoint; creates a new Agent Run only when original failed before side-effecting tool activity; preserves attachments and immutable saved Agent config snapshot | CONNECTED (source; new-run replay only) | NOT VERIFIED |
| Chat citations/source display | `chat-view.tsx` | RAG retrieval marker → final response → Agent Run output → owner-scoped conversation history/page → Chat restore | CONNECTED (source) | NOT VERIFIED |
| Agent catalog / Agent Studio | `agent-studio-view.tsx` | Authenticated runtime catalog plus owner-scoped Agent configuration CRUD, versioned config snapshot, user-role instructions, live worker heartbeat and tool allowlist | CONNECTED (source) | NOT VERIFIED |
| Dynamic Agent/tool capability | Agent Studio | Worker heartbeat snapshots expose healthy runtime/tool registrations; API fails closed when no healthy worker advertises requested runtime | CONNECTED (source) | NOT VERIFIED |
| Agent detail / start agent task | `agent-studio-view.tsx`, `chat-view.tsx` | Supported agent key routes through durable Agent Run enqueue and worker dispatcher | CONNECTED (source) | NOT VERIFIED |
| Model selector / provider routing | Existing Chat and catalog surfaces | Server-side Model Router/provider capability policy; browser does not select or call provider directly | PARTIAL / GATED | NOT VERIFIED |
| Tools directory | `tools-catalog-view.tsx` | Authenticated tool catalog; unsafe tools remain unavailable until isolated adapter and policy gates pass | PARTIAL / GATED | NOT VERIFIED |
| Connector authorization/revoke | No verified Customer connector lifecycle surface/API | No verified OAuth connector authorization/revocation contract available | UNAVAILABLE / FAIL-CLOSED | NOT VERIFIED |
| Risky tool confirmation | Chat/Workflow approval surface | Durable owner-scoped approval, pause/resume, single-use consume, transactionally emitted decision/resume events | CONNECTED (source + migration applied) | NOT VERIFIED |
| Tool execution history/output | Chat, Workflow, Tasks | Safe durable activity/step/log projections; raw tool arguments and observations excluded | CONNECTED (source) | NOT VERIFIED |
| Tasks queue / run history | `tasks-view.tsx` | Keyset-paged owner-scoped Agent Runs, status and artifact linkage | CONNECTED (source) | NOT VERIFIED |
| Task detail / progress / steps | `tasks-view.tsx`, `workflow-progress-view.tsx` | Typed owner-scoped run progress snapshot, safe step/dependency projection, logs, activity, durable SSE replay and artifact relationship | CONNECTED (source) | NOT VERIFIED |
| Task pause/cancel | Tasks/Workflow/Chat | Durable cancellation and approval pause/resume state machine | CONNECTED (source) | NOT VERIFIED |
| Task retry / replay | `tasks-view.tsx` | Idempotent manual retry creates a new run only for safe replayable failed/timed-out/expired source runs; it is not an in-place checkpoint resume. Automatic worker retry and approval continuation resume the existing durable run/checkpoints | CONNECTED (source; new-run replay + server checkpoint recovery) | NOT VERIFIED |
| Task artifacts / download | Tasks, Results, Research, Workflow | Owner-scoped artifact pages, signed download, run relationship | CONNECTED (source) | NOT VERIFIED |
| Workspace files / upload / preview | `files-view.tsx` | Workspace owner/member authorization, private storage, CAS upload, immutable version history, soft delete/restore | CONNECTED (source) | NOT VERIFIED |
| Generated artifacts | `artifacts-result-view.tsx`, Files, Tasks | Private artifact storage, metadata owner checks, signed URL | CONNECTED (source) | NOT VERIFIED |
| Analyse / Knowledge Library | `analyse-view.tsx`, `knowledge-library-view.tsx` | Owner-scoped upload, ingestion, keyset chunk pages, selected-document retrieval and provenance | CONNECTED (source) | NOT VERIFIED |
| EduTech AI learning sessions | `edutech-view.tsx` → existing ChatView | Student topic/level/goal and four study modes hand off to durable Planning Agent Run through authenticated Customer conversation enqueue; conversation/run/progress appear in Chat, Tasks and Workflow | CONNECTED (source; AI learning session) / PARTIAL (structured LMS records and lesson progress) | NOT VERIFIED |
| Research | `research-view.tsx` | Keyset Agent Run/artifact pages and signed download | CONNECTED (source) | NOT VERIFIED |
| Code Assistant | `code-view.tsx` | Analysis through durable Agent Run; code snapshots/artifacts | PARTIAL / GATED | NOT VERIFIED |
| Create Studio file output | `create-view.tsx` | Manus `file_saver` artifact path, gated by live worker adapter capability | PARTIAL / GATED | NOT VERIFIED |
| Create Studio image output | `create-view.tsx` | Metered OpenAI Images API adapter (`gpt-image-2`) and private binary artifact path are implemented; worker registers only with API key, explicit per-image price map, media entitlement, quota and wallet config | PARTIAL / GATED — no credentials/config supplied, so not live | NOT VERIFIED |
| Create Studio rendered video | `create-view.tsx` | Durable, metered Runway Dev text-to-video adapter with task-ID checkpoint recovery, provider task polling and private MP4 artifact storage; worker registers only when Runway secret, per-model/duration/ratio price cap, provider-credit conversion, media entitlement/quota and output-host allowlist are configured | PARTIAL / GATED — no credentials/pricing/host config supplied, so not live | NOT VERIFIED |
| Python/browser/SWE execution | Tools/Code surfaces | Supervisor isolation, provider, approval and policy gates required; not advertised as active when gates are closed | PARTIAL / GATED | NOT VERIFIED |
| Personal Memory / consent / correction / retention / deletion | `profile-settings-view.tsx` | Owner-scoped FastAPI consent, list, create, update, item delete and clear-all; worker reads only explicitly consented personal records; scheduled expiry purge | CONNECTED (source) | NOT VERIFIED |
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
1. Continue the Customer API action-to-screen contract audit, including complete pagination, response/error/idempotency parity and any remaining UI actions without a real backend contract.
2. Complete workflow/task lifecycle edge cases: durable step dependencies, artifact linkage and result projection, approval pause/resume, cancellation and safe retry semantics. Manual retry is explicitly a new run; no same-run manual checkpoint rewind is exposed.
3. Memory privacy lifecycle is implemented at source level; runtime consent, retention purge and deletion still require later authorized verification.
4. Complete connector OAuth lifecycle, payment/subscription settlement and partner OTP/gateway lifecycle only with real provider contracts and credentials.
5. Runtime acceptance remains intentionally unperformed. Phase 10 End-to-End Integration Verification and Phase 11 Integration Release Gate are dependency-next and not performed.


## 2026-11-14 dependency projection and lifecycle reconciliation

- Both Customer and shared Agent Run step endpoints now expose only validated zero-based dependency indexes from private step input; prompts, step input/output/error bodies remain excluded from the response.
- Tasks and Workflow existing detail surfaces display prerequisite step numbers without changing their visual structure.
- PlanningAgentRuntime already persists the plan manifest and step outputs, validates dependency indexes, skips successful persisted steps on recovery, and only executes a step after its prerequisites are complete. This increment connects dependency metadata to the Customer UI rather than replacing that durable runtime.
- Manual Customer retry is a new run for a safely replayable failed source run; automatic worker retry and approval continuation retain the same run/checkpoints. These semantics are intentionally distinguished in UI and API documentation.
- Source commits: `5da2642f`, `474d3146`, `42850aec`, `cc15f03b`, `7360613b`, and `9ee77d08`.
- OpenAI Image API has an available generation endpoint and GPT Image models, but no provider credentials/secret reference or media credit reservation/metering contract is configured in this repository context. OpenAI's Sora Videos API and Sora 2 models were removed on 2026-09-24, with no one-to-one replacement; a real alternative video provider must be selected and onboarded. See official OpenAI docs: [Image Generation](https://developers.openai.com/api/docs/guides/image-generation) and [API deprecations](https://developers.openai.com/api/docs/deprecations).
