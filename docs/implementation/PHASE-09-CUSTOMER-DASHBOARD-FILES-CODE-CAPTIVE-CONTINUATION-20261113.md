# Phase 09 — Customer Dashboard Files, Code and Captive Flow Continuation

**Date:** 2026-11-13  
**Repository:** `fadliansyah36/More-AI-Portal-Indihome`  
**Branch:** `main`  
**Status:** Source implementation increment; Phase 09 remains IN PROGRESS.

## 1. Engineering baseline

Re-read the repository `AGENTS.md`, Phase Tracker, current continuation reports and Master PRD baseline before changing source. The current implementation preserves the existing MoreAI UI and uses the existing FastAPI/Supabase boundaries. OpenManusWeb remains the authoritative backend capability source; this increment does not introduce a second engine or frontend.

No Supabase live writes, migrations, staging or deployment were performed.

## 2. Implemented source changes

### Files, artifacts and persistence

- Connected the existing Files screen to the typed `artifactApi.list()` and `artifactApi.upload()` methods.
- Added file upload to the existing Files screen using the already implemented private `POST /api/v1/artifacts` endpoint.
- Enforced the API's current 2,000,000-byte size ceiling and accepted filename character contract before upload. Server-side validation remains authoritative.
- Reloads persisted artifact metadata after upload and displays upload/error state. Upload fails visibly if private Artifact Storage is not configured; no local-only success is shown.
- Kept the existing signed artifact download flow and workspace file download/version history flow.
- Changed workspace file aggregation to `Promise.allSettled`: one inaccessible workspace no longer suppresses file results from other accessible workspaces. Partial failures are reported to the user.
- Added signed download action to the existing Artifact Results screen.

### Code Assistant

- Connected the existing Code Assistant's Save action to private artifact persistence using `artifactApi.upload()`.
- Added a persisted snapshot list backed by `artifactApi.list()` and signed downloads through `artifactApi.signedDownload()`.
- Snapshot writes are bounded to the same 2 MB artifact limit.
- Snapshot storage is explicitly described as private artifact storage, not a Git repository or versioned workspace.
- Python execution remains disabled. The existing analysis handoff to Customer Chat remains the only enabled agent action; no local or simulated execution was introduced.

### Captive Portal, gateway and consent truthfulness

- Captive Portal step 2 now distinguishes preview from authentication. Registration is disabled until the gateway/auth adapter exists.
- Captive terms copy no longer promises fixed 100 Mbps, 3-hour sessions, 100,000 AI credits, end-to-end encryption or universal third-party restrictions without backend/policy evidence.
- Consent checkboxes start unchecked and the action reports that consent is not persisted. It does not navigate into OTP or claim consent was recorded.
- Captive Portal's access-status screen no longer claims a successful Wi-Fi connection. It shows gateway-not-connected / not-verified states.
- Customer portal preview no longer claims a verified partner benefit or 100K credit balance.
- Captive OTP remains disabled and no session is created without a real gateway contract.

### Remaining Customer-facing demo/fallback cleanup

- Welcome success no longer claims a 100,000-credit grant or a ready 100 Mbps connection. Account creation remains tied to the actual Auth flow.
- Onboarding partner-benefit copy now conditions benefit on a verified network and active entitlement; illustrative profile label was neutralized.
- FAQ no longer promises a universal 100,000-credit grant or 24/7 partner support. The support action reports that no official contact channel is configured.
- Partner access banner now reflects pending gateway verification and active entitlement rather than a fabricated venue, speed or credit grant.
- Device Access Control no longer contains local-only pause/resume or Safe Browsing mutations with success toasts. It explains that device inventory and gateway controls are unavailable.
- Task creation modal now says the prompt is handed off to authenticated Agent Chat to create a durable Agent Run; it no longer labels this as a scheduled task save.
- Benefit history empty state now accurately reports when no Wi-Fi session is recorded.

## 3. Customer screen/action audit — source-level inventory

The Customer-facing screen set was reviewed across authentication, account, AI workflows, workspace/files, credits, Wi-Fi/captive, learning and help. The matrix below records the current contract boundary; it is not runtime acceptance.

| Customer surface | Existing data/action contract | Remaining gap |
|---|---|---|
| Login / Register / Welcome | Supabase Auth sign-in and sign-up; account success follows Auth result | Social OAuth provider availability remains configuration-dependent |
| Home | Authenticated profile, recent Agent Runs, wallet and entitlement state | No fabricated partner status; aggregate feed remains limited to current APIs |
| Agent Studio / Tools Catalog | Agent registry and OpenManus tool catalog from FastAPI | Unsupported/disabled agents and tools remain unavailable until backend runtime gates pass |
| Chat | Persistent conversation creation, idempotent message enqueue, durable run stream and cancellation | Chat attachments remain disabled; no direct conversation-attachment endpoint is currently exposed |
| Workflow Progress / Tasks | Agent Run history, pagination and approval decision API | Task creation is a Chat handoff, not a separate scheduler; no local-only task records |
| Research | Persisted Agent Run history and output | Public/popular research topic catalog is not connected |
| Create | Text-oriented task handoff to Agent Chat | Image/video generation is unavailable in the connected runtime |
| Analyse / Knowledge Library | Private PDF/image upload, ingestion status, list, retry and archive | Ingestion depends on configured private storage and worker processing |
| Code Assistant | Agent-based code review handoff; code snapshots saved/listed/downloaded as private artifacts | Python/Bash execution remains gated; snapshots are not Git/workspace version history |
| Files / Artifact Results | Artifact list/upload/signed download; workspace file list/signed download/version history | Manual upload directly into versioned workspace files has no Customer FastAPI endpoint yet |
| Profile / Preferences | Profile read/update and notification preference persistence | Remaining account lifecycle actions require their own supported backend contracts |
| Security | Supabase TOTP MFA, password re-auth/update, global sign-out | Device inventory/session metadata beyond Auth is not provided by gateway |
| Notifications | FastAPI list, mark-read, mark-all-read and persisted preferences | Notification preference categories remain limited to the available schema |
| Benefits / Token Ledger | Wallet, immutable ledger, usage, quotas, entitlements and network-session records | Top-up, checkout, refund/payment actions remain unavailable until payment adapter is integrated |
| Analytics | Account usage records from FastAPI | Validated historical aggregation endpoint is not yet available |
| Account Upgrade | Entitlement display | Subscription pricing, checkout and activation are not connected |
| Wi-Fi Management / Session / Devices | Authenticated network-session records; API-path speedtest | Gateway diagnostics, actual device inventory, pause/resume/disconnect and session extension are not available |
| Device Access Control | Fail-closed unavailable state | Requires partner gateway inventory and authorized mutation endpoints |
| Captive Portal / Terms / OTP / Success | Preview only; session/benefit success reads real backend state where applicable | Gateway verification, consent persistence and OTP send/verify adapter are not integrated |
| EduTech / Lesson | Existing learning-progress read/write API | Course catalog and video delivery are not connected; lesson copy remains curated static content |
| Help / FAQ | Static help content with explicit unavailable support-channel state | Official support contact integration is not configured |
| Onboarding / Partner Access Banner | Conditional benefit wording; no hardcoded entitlement | Actual benefit appears only when backend returns active entitlement |

## 4. Workspace upload boundary

The repository already has an OpenManus workspace tool that writes versioned files through worker lease/CAS contracts, and the Customer Files screen can list, inspect history and download those files. However, the current Customer FastAPI router does not expose a direct manual workspace-file upload endpoint. The artifact upload API is a separate private artifact store and must not be mislabeled as a versioned workspace write.

A safe Customer workspace upload requires an authenticated, idempotent write contract that preserves immutable Storage objects, expected-version checks, lease/CAS invariants, workspace owner/member authorization and metadata commit atomicity. This increment intentionally does not bypass those invariants with direct service-role table writes.

## 5. UI preservation and verification boundary

- Existing page/component structure and navigation were preserved; UI changes are limited to missing API actions, truthful status text and disabling unsupported mutations.
- No redesign, new frontend shell, global style migration, database schema change or new business database was introduced.
- Source readback only. No tests, lint, typecheck, build, browser/API probes, screenshots, Docker build, provider calls, Supabase migration apply/live writes, staging or deployment were performed, as explicitly instructed.
- Before/after browser screenshots were not captured; UI regression evidence therefore remains an open acceptance item under the repository UI change gate.
- No runtime success, gateway acceptance, provider acceptance or phase completion is claimed.

## 6. Phase 09 remaining work

1. Add a safe Customer workspace file upload/write contract and connect it to the existing immutable version/CAS pipeline; do not bypass worker/database invariants.
2. Complete Chat attachment flow with an explicit conversation/workspace document contract; Knowledge ingestion is available separately but is not represented as a Chat attachment.
3. Complete persisted conversation/session resume and result/artifact linkage across Chat, Research, Create, Analyse, Code, Tasks and Workflow.
4. Finish all remaining Customer screen/action mapping against FastAPI/OpenAPI and remove any residual unsupported demo actions.
5. Integrate the real captive gateway adapter, tenant/network verification, consent persistence, OTP provider and network-session lifecycle. Keep fail-closed behavior until this exists.
6. Integrate verified EduTech catalog/video delivery, payment checkout/top-up and support channels when their backend contracts are ready.

## 7. Dependency order

- **Current focus:** Phase 09 — Full Customer Dashboard remains IN PROGRESS.
- **After Phase 09:** Phase 04 and 06 backend parity/contracts required by any remaining Customer flows.
- **Then:** Phase 07 durable worker lifecycle and Phase 08 complete agent/provider/tool/orchestration/memory/RAG parity.
- **Phase 10/11:** Not accepted / blocked while runtime verification and release gate are not authorized.

## 8. Source commits in this increment

- `ebc2fd6b` — Files screen private artifact upload.
- `6a5d5afc` — Code Assistant artifact snapshots and downloads.
- `dbf60815` — code snapshot size guard.
- `da375eda` — Artifact Results signed download.
- `fb358e25` — partial workspace file aggregation.
- `89c80599`, `cf5073df`, `32ed870d`, `a908baf5` — Captive Portal/terms fail-closed corrections.
- `69f09c27`, `86f6cbc7`, `5e7c21ba`, `0e77f8cb`, `459e0bc6` — customer-facing benefit/help/onboarding copy corrections.
- `29127edc` — remove local-only device control actions.
- `7d2fb99c` — clarify Tasks → Agent Chat handoff.
