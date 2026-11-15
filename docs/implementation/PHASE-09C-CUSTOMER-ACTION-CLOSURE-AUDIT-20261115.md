# Phase 09C — Customer Dashboard Action Closure Audit (2026-11-15)

Branch: `main`
Baseline HEAD: `ed43a936b124dec6e45d632649cd3850933f46ed`
Scope: source-level audit of the existing customer dashboard action inventory and representative UI/API seams. This is not runtime acceptance.

## Owner constraints
- Direct commits to `main`; no staging.
- No functional tests, builds, lint, typecheck, browser automation, API/worker probes or provider calls.
- Preserve existing customer UI and design system.
- No fabricated data or simulated success.

## Audit findings

The current customer action inventory and acceptance matrix were re-read, together with the integration master map, `AGENTS.md`, and the current source for Help/FAQ, Profile Settings, Agent Studio, the typed API client, Connections API and worker startup.

### Source-connected customer actions
The existing source inventory records typed FastAPI contracts for:
- Customer identity/profile, preferences, notifications, wallet/ledger/usage/quota reads.
- Conversations, attachments, SSE replay, cancellation, retry, run detail/steps/events, durable approvals and checkpoint projections.
- Agent catalog/configuration, model capability metadata, Skills Library/Registry, owner-scoped memory/consent/episodic lifecycle.
- Knowledge Library, private artifacts, workspace files/versioning, Research, Code snapshots and generated media artifact projection.
- EduTech paths/lessons/quizzes/assessments/progress and run-linked artifacts.
- Google Connections OAuth lifecycle and Gmail/Calendar action receipts, subject to configured OAuth credentials and encrypted connection keyring.

These are source-level integrations only. They do not establish live API, RLS, provider or worker acceptance.

### Explicitly unavailable / fail-closed actions
- Payment top-up, checkout and subscription mutation: no verified payment intent, settlement webhook or payment provider contract.
- Captive gateway consent/OTP/activation/device control: no verified partner gateway adapter and credential set.
- Support ticket/contact: no verified support workflow/provider or official support contact.
- Browser/Computer customer operation: supervisor client and persistent-session plumbing exist in source, but no deployed isolated supervisor, enforced live egress, scanner service or customer-facing lifecycle/approval workflow has been accepted.
- Extended device/session inventory and revoke: not available as a complete server-side lifecycle.

The Help/FAQ surface currently explicitly tells users the official support channel is not configured and does not create a fake ticket. The Profile screen uses FastAPI for business profile/preferences/wallet data and limits browser Supabase access to Auth identity fallback. Agent Studio lists only installed, approved and execution-enabled skills; discovered/imported packages are not presented as runnable.

### 09C status
**PARTIAL — source-connected actions have broad typed API coverage; unresolved provider-dependent actions remain correctly fail-closed.** It would be unsafe to mark 09C complete while the browser/computer customer lifecycle, full session controls, and unavailable provider workflows remain open. No source changes to these screens were justified by this audit because current behavior already avoids false success and uses the established visual language.

## 09A / 09B dependency status
- 09A provider/model/route forms and server-side routing contracts exist, but the live registry still has no real provider/model/route records and no worker host secret injection.
- 09B worker process includes startup gates, independent capability heartbeat, liveness/readiness and recovery loop source. No persistent container host is connected in this execution context; no worker deployment or heartbeat can be claimed.
- Agent execution must remain disabled until real host, secret, billing/quota, provider and security prerequisites are configured.

## 09D readiness assessment
OpenFuse Browser/Computer parity is not ready for customer activation. Existing worker-side `BrowserSupervisor` client already requires HTTPS or explicitly private Compose HTTP, >=32-character service/internal tokens, enforced egress, a ready proxy, owner/run-bound session acquisition, scanner-clean downloads, private artifact persistence and session-state persistence. However, this source client alone is not the isolated supervisor deployment or a customer-facing control plane. The next source increment must map the actual registered browser tool, FastAPI session routes/RPCs, migration, approval/action receipt contracts and existing customer navigation before adding UI.

## Verification
Per owner instruction: no tests, build, lint, typecheck, browser/API/worker execution, provider calls, staging or deployment. UI screenshots and runtime acceptance remain NOT VERIFIED.

## Next phase
Continue operational 09A/09B only when a real persistent host and secret manager are connected. In parallel, finish 09C source traceability and implement 09D customer-facing browser session lifecycle/approval/download controls behind the existing FastAPI/worker boundary. Keep unsupported payment, OTP/gateway and support actions disabled.


## 09C source implementation follow-up

After the audit, two specific customer-facing gaps were corrected:
- Added typed `customerApi.browserSessions()` and `closeBrowserSession()` methods for the existing owner-scoped FastAPI session list/close endpoints.
- Added a compact Browser Sessions section in Profile Settings with loading, error/retry, empty and success/closing states; it displays only server-returned host/last-used/expiry metadata and lets the authenticated owner close an active session. It does not launch a browser or claim computer-use capability.
- Replaced stale FAQ claims about automatic free-credit top-ups and guaranteed offline task/history availability with backend-governed credit/entitlement and service availability guidance, plus a truthful support-channel statement.

Files changed:
- `lib/api/client.ts`
- `components/views/profile-settings-view.tsx`

Source commits:
- `fcec12188ba42b3da6fc20b827bb819a7a1125c0` — typed browser session API.
- `580273d88c7a73773037d816c5f01cfa0a9d4efc` — Profile Settings session controls and FAQ correction.

This is a source implementation only. No tests, builds, lint, typecheck, browser/API/worker calls, staging, deployment or screenshot capture were run. Browser-session close behavior and visual regression remain NOT VERIFIED. 09C remains PARTIAL pending full source-to-screen traceability and OpenFuse Browser/Computer workflow parity.
