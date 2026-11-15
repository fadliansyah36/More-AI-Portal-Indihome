# Phase 09D — OpenFuse Browser Adapter & Customer Lifecycle (2026-11-15)

Branch: `main`
Pinned OpenFuse reference: `CopilotKit/openfuse@7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`
Scope: source integration of the actual OpenFuse persistent Chromium worker protocol into MoreAI's durable OpenManus/FastAPI/Supabase runtime and customer dashboard. No runtime acceptance is claimed.

## Important protocol correction

The earlier adapter draft targeted a private `/v1/browser/actions` route that is not part of the pinned OpenFuse worker contract. This increment replaced that assumption with the actual worker API documented in the pinned source:
- `GET /health`
- authenticated `GET /sessions`, `POST /sessions`
- `POST /sessions/:id/navigate`, `POST /sessions/:id/input`, `POST /sessions/:id/close`
- `GET /sessions/:id/read`, `GET /sessions/:id/screenshot`, `GET /sessions/:id/downloads`, and `GET /sessions/:id/downloads/:downloadId`

OpenFuse browser profiles are persisted on the browser-worker data volume. The worker enforces public HTTP(S) destination validation and egress proxy policy; MoreAI still requires an explicit deployment attestation and private service URL/token configuration.

## Implemented source changes

### Worker / OpenFuse adapter
- Replaced the unsupported action endpoint with the pinned OpenFuse session API.
- Startup readiness now checks OpenFuse's real `/health` response (`status=ok`) and authenticated `/sessions` response.
- Supports `navigate`, visible-text `extract`, bounded `input` (click/text/key/scroll), `screenshot`, `close`, and `downloads` metadata.
- Uses MoreAI owner/run-bound session IDs; active profiles are reopened by the same UUID.
- Customer-initiated session close is reconciled by a separate worker loop. It waits until the session's last Agent Run is no longer running, closes the OpenFuse Chromium session, then acknowledges the durable close request to FastAPI.
- The adapter does not expose OpenFuse worker credentials to the customer browser.

### Durable action receipts and replay safety
- Added server-only `moreai_browser_action_receipts` table with RLS enabled and no anon/authenticated grants or client policies; service role is the only DB access path.
- Action keys are bound to `run_id + OpenManus tool_call_id`; request hashes prevent reuse of one tool-call ID with changed arguments.
- Receipts record action type, target host only (never the raw URL/query), owner, run, session, status, safe error code and bounded result.
- Ambiguous outcomes are marked `unknown`; duplicate worker delivery does not re-submit the remote action.
- Cancelled tool calls attempt bounded shielded receipt finalization.
- Old `executing` receipts are projected to `unknown` after five minutes for customer display, without altering the persisted row or permitting replay.

### Screenshot artifacts
- Added an internal FastAPI endpoint that accepts only PNG-signature-valid screenshots from the authenticated worker, caps size at 2 MB, verifies run/session ownership, and writes to private Supabase Storage.
- Screenshot artifacts are owner-scoped, run-linked and shown with inline preview in Hasil Pekerjaan.
- Browser download metadata/failures are visible, but downloaded file bytes are deliberately not imported until a real malware scanner is configured. OpenFuse's PDF signature/size validation is not a ClamAV verdict.

### Customer dashboard
- Profile Settings and Hasil Pekerjaan both expose the owner's active Browser Sessions.
- Session close now creates a durable `close_requested` state; UI does not report closed until the persistent worker acknowledges the actual OpenFuse session close.
- Both views support refresh and show the pending worker state.
- Profile Settings exposes durable action history with explicit succeeded/failed/unknown states.
- Hasil Pekerjaan displays private screenshot previews using owner-authorized signed artifact URLs.

### Skills and approvals
- Browser actions remain behind the existing durable owner approval gate.
- Skill permission enforcement is action-aware: `browser.navigate` permits navigation, visible text reads and screenshots; `browser.download` permits download metadata only. Skills cannot use `input` or `close` through these read-only grants.
- No retrieved page text or screenshot content can grant tool permissions.

## Supabase migrations applied
1. `moreai_browser_action_receipts`
2. `moreai_browser_action_receipt_action_types`
3. `moreai_browser_session_close_requests`
4. `moreai_browser_action_receipt_screenshot`

All four migrations were applied to canonical project `uunfgimtokhucegqbpce`. The action receipt table is RLS-enabled and service-role-only.

## Computer parity boundary

This increment integrates OpenFuse's persistent browser worker and browser-input actions. It does **not** claim the optional OpenFuse Linux computer/E2B graphical desktop is integrated. MoreAI's current isolated Bash/Python workspace is a separate execution adapter; there is no connected Docker/E2B computer host, desktop stream, VNC session, or persistent per-customer computer supervisor. Do not expose host shell or desktop access. Full Computer parity remains blocked until a supported persistent isolated host and its owner-scoped control API are connected.

## Operational blockers
- 09A: no actual provider/model/route rows or provider secrets injected into a persistent worker host.
- 09B: no connected persistent container host; no worker deployment/heartbeat can be claimed.
- OpenFuse: no actual browser-worker service URL/token, persistent profile volume or live worker heartbeat is configured in this execution context. Agent execution remains disabled.
- PDF download import remains blocked until a real malware scanner is connected.
- Linux Computer/E2B desktop parity remains blocked as described above.

## Verification constraints
Per owner instruction: no tests, builds, lint, typecheck, browser automation, API/worker runtime probes, provider calls, staging or deployment were performed. Source was inspected; live OpenFuse protocol, screenshot upload, close reconciliation, UI visual regression and runtime behavior remain NOT VERIFIED.

## Next phase
Continue 09A/09B operational setup when a persistent host and secret manager are connected. Then complete the remaining 09D Computer parity only against an explicitly selected isolated computer provider; do not claim desktop or PDF import readiness without actual host/scanner integration. 09C and 09D remain PARTIAL; Phase 10 NOT ACCEPTED; Phase 11 BLOCKED.


## Result payload retention follow-up

- Browser action receipt results (which may include bounded visible-page text) now have a 30-day result retention window.
- Added service-role-only `moreai_worker_purge_expired_browser_action_receipt_results()`; the persistent worker invokes it alongside the existing memory-retention maintenance loop.
- Expired result payloads are cleared while the receipt identity/status remains, so an old tool-call replay is still blocked rather than re-executed.
- Migration `moreai_browser_action_receipt_result_retention` was applied to the canonical Supabase project.
- No tests or runtime probes were performed.
