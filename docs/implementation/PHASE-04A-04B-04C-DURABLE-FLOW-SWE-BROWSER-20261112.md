# Phase 04A / 04B / 04C — Durable Flow, SWE Workspace Lifecycle, Browser Isolation

Date: 2026-11-12  
Branch: `main`  
Latest source HEAD at report creation: `23eb15e6cd4019af9c4d2a5b9562e6d391a0462c`

## Phase 04A — Flow Engine, server/session, events, logs, thinking and WebSocket

Implemented:
- PlanningFlow dependency outputs are passed to dependent steps, with a bounded 20 KB serialized dependency context.
- Planning manifests persist the validated step definitions and can recover both crash windows: manifest exists but only some step rows were written; or durable rows exist but the worker's recovered checkpoint set lacks the manifest.
- Planning steps now carry an explicit allowlisted `agent_key`; disabled agent keys fail closed before the plan is persisted. Worker registry currently exposes the real `manus` executor and the `planning` flow; this does not fabricate additional agent runtimes.
- FastAPI now exposes owner-scoped run activity endpoints: `/{run_id}/logs`, `/{run_id}/thinking`, and `/{run_id}/progress`. The projections are built from durable run events and step rows, not process-global trackers.
- Authenticated WebSocket `/{run_id}/ws` validates Customer principal and run ownership, replays persisted activity and emits status/log/thinking/progress/result envelopes. Prompt text, raw tool arguments and observations are excluded from the activity projection.
- Durable checkpoint events such as `planning.step.N.started/completed` are translated into owner-visible thinking activity.

Limitations:
- The upstream legacy log parser and in-memory tracker are intentionally not copied. Structured persisted events are the source of truth; complete legacy route/session semantics and actual deployed WebSocket reconnect acceptance remain open.
- Flow execution is sequential and dependency-aware; production multi-agent routing still depends on additional real registered agent runtimes. Unknown agent keys are rejected.

## Phase 04B — SWE workspace lifecycle

Implemented:
- `str_replace_editor` now supports `create`, `edit`, `delete`, `rename`, and `restore_deleted` in addition to the existing version restore path.
- Delete is a soft tombstone, not a destructive Storage object deletion. It writes/retains immutable version metadata and sets `deleted_at`.
- Rename is a lease-fenced metadata operation with expected-version compare-and-swap and version increment; the existing Storage object remains immutable and its object path is retained.
- Restore-deleted clears the tombstone and increments the version. Version restore is blocked on tombstoned files until explicit restore-deleted is performed.
- File listing hides deleted files by default and accepts `include_deleted=true` for recovery workflows.
- Approval summaries now identify the requested action and file path without exposing file contents.
- RPCs validate active run ownership, worker lease owner and expiry, workspace membership, path traversal, expected version and pending-write state.

Supabase:
- Applied migration `20261112073357_moreai_workspace_delete_rename_lease_fencing` to canonical project `uunfgimtokhucegqbpce`.
- Applied migration `20261112073831_moreai_workspace_restore_deleted_file`.
- Verified `deleted_at` exists; delete/rename/restore/get-file RPCs use invoker security and are executable by `service_role`; `authenticated` cannot execute the restore RPC.
- Security advisor did not report a new issue caused by these migrations. Existing project advisor findings are tracked separately.

Limitations:
- No physical Storage object purge is performed by delete; retention is deliberate so versions remain recoverable.
- Workspace membership currently follows the existing active-member authorization semantics; finer per-role edit/delete policy is a separate contract gap.
- No live Customer UI end-to-end exercise of create/upload/rename/delete/restore has been completed.

## Phase 04C — Private worker/supervisor connectivity and browser egress

Implemented:
- Browser proxy image imports are container-local and no longer depend on the monorepo `apps.*` import path.
- Browser runtime base image is pinned by digest; Playwright browser binaries are readable by the non-root supervisor user.
- Worker-side BrowserSupervisor supports HTTPS by default and a narrowly scoped private Compose HTTP exception only for `http://browser-supervisor:8080`, root path, no credentials/query/fragment, and explicit `MOREAI_BROWSER_PRIVATE_NETWORK_HTTP=true`.
- Browser supervisor `/ready` requires service-token authentication and returns ready only when egress enforcement is configured and the proxy is reachable.
- Worker startup checks the authenticated supervisor readiness contract when browser tools are enabled; startup fails closed if proxy readiness is missing/degraded.
- Browser proxy resolves and pins the current globally routable DNS answers per CONNECT; private/reserved/metadata IPs are rejected before opening the socket. Safe public CDN DNS rotation is not treated as SSRF.
- Browser navigation errors return a sanitized gateway error; internal URLs, credentials and page content are not exposed.
- Downloads remain disabled until a scanner-backed lifecycle exists.

Docker acceptance:
- Added GitHub Actions `browser-docker-acceptance` job that builds and starts the browser/proxy Compose topology, builds the worker image, attaches a worker client container to the isolated network and exercises the private supervisor readiness call.
- The verifier checks browser-only internal network attachment, proxy-only egress bridge, Docker `Internal=true`, direct IPv4/IPv6 denial, authenticated supervisor readiness, positive allowlisted HTTPS via proxy, Playwright navigation, unauthorized redirect denial, download denial, public-to-loopback DNS rebinding rejection, private/metadata/non-allowlisted target rejection, and non-privileged/non-host networking.
- The latest full workflow at report time is [run 43178037719](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43178037719), still running. No Docker acceptance PASS is claimed until its `browser-docker-acceptance` job completes green.

Limitations:
- GitHub-hosted Docker CI proves the container topology and worker-side client contract on that runner; it does not prove connectivity in the target production platform.
- No worker or browser supervisor has been activated in staging/production.
- Download scanning is not implemented; downloads are denied rather than scanned/accepted.

## CI evidence

- Worker contract and engine policy suites passed on prior commits during this increment.
- API contract and sandbox policy suites passed on prior commits during this increment.
- A later Engine Contract run caught a missing `agent_key` field in the executor payload; fixed on `00f45ca3` and a new workflow run is in progress.
- Do not treat the partial passing jobs from earlier commits as full Phase 04 acceptance. Use the latest all-green workflow before closing the phase.

## Remaining gates before Phase 04 acceptance

1. Latest full CI must pass, including Docker acceptance for the actual Playwright navigation/redirect/download probes.
2. Complete upstream server/session route parity, durable session lifecycle and WebSocket reconnect behavior against the actual Customer API client.
3. Finish full SWE workspace role-level lifecycle semantics and live Customer file create/upload/rename/delete/restore journey.
4. Run target-platform network acceptance (worker and browser supervisor private connectivity, proxy egress, DNS/socket pinning, IPv4/IPv6 denial, redirect/subresource behavior). GitHub Docker CI alone is not production acceptance.
5. Complete authenticated Customer → FastAPI → worker → OpenManus → real provider → Supabase E2E and verify no cross-tenant access.

Phase 04 remains IN PROGRESS. Phase 07 must follow only after Phase 04 acceptance; Phase 08 follows Phase 07. Phase 06/09, Phase 10 and Phase 11 remain open. No production deployment or release is authorized by this report.
