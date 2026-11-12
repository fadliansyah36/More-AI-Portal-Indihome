# Phase 08 → 06 → 09 Continuation — 2026-11-12

## Execution target
- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Branch: `main`
- Implementation follows root `AGENTS.md` and `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md`.
- Existing Customer UI layout is preserved; UI changes replace simulated data/actions with real API-backed behavior.

## Phase 08 — additional implementation

### Durable knowledge ingestion
- PDF pages with less than 30 characters of embedded text are rendered selectively using pinned `pypdfium2==4.30.0`, then OCRed through Tesseract.
- English and Indonesian OCR language packages are installed in the worker image.
- PDF page rendering is bounded by a 40-million-pixel ceiling; images are dimension-checked before RGB allocation and capped at 40 million pixels.
- OCR page metadata is retained in each indexed chunk; citations preserve page number and normalized page-local character offsets.
- Worker ingestion leases now renew every 45 seconds with a compare-and-swap filter on document ID, owner, status and previous lease expiry. A stale worker is cancelled rather than allowed to finalize.
- Retryable failures use the durable bounded backoff and maximum-attempt policy from the ingestion migration. Owner-scoped retry API resets attempt count and requeues the existing private source object.
- Repeated identical file bytes for the same owner/workspace reuse the existing processing/ready/failed document by SHA-256 rather than creating duplicate ingestion rows.
- Upload response reloads and returns the persisted queued metadata, not the initial pre-upload row.
- The upload endpoint fails closed if the server-side Storage service credential is absent; idempotent upload response distinguishes processing/ready/failed and the Analyse screen reports the real existing ingestion state.

### Provider, agent, Flow and tool integration
- Authenticated `GET /api/v1/models/capabilities` exposes enabled provider/model capability metadata only; no provider config or secret values are returned.
- Customer agent catalog only advertises runtime-backed agent keys. SWE is exposed only when sandbox enablement, independent release gate and digest-pinned image are configured.
- Durable runtime now supports a dedicated SWE system contract and conditionally registers the SWE runtime behind sandbox gates.
- OpenManus `run` nested dispatch now reuses schema validation, tenant/workspace scope, policy checks, approval gates and tool deadlines; recursive run/terminate dispatch is denied.
- OpenManus `terminate` schema now matches upstream success/failure status and persists a terminal checkpoint instead of continuing another LLM round.
- Upstream Flow inventory contains only PlanningFlow in this pinned source. MoreAI keeps the durable PlanningFlow adapter in the allowlisted FlowFactory; other flow types are not fabricated.

### Remaining Phase 08 parity gaps
- Full upstream SWE/browser supervisor deployment and security acceptance remain gated.
- Additional upstream exception taxonomy, logging/monitoring, web session and tracker behavior still need parity work.
- Provider retry/circuit-breaker and real provider E2E acceptance remain open.
- No claim is made that every upstream tool handler is production-enabled; unavailable/high-risk tools remain fail-closed.

## Phase 06 — API contract increment
- OpenAPI now declares bearer JWT security for versioned API operations and documents optional `X-Correlation-ID`.
- FastAPI continues to generate request/response Pydantic schemas, including multipart request body for knowledge upload.
- Customer conversations and agent-run history now accept bounded `limit` and timezone-aware `before` filters.
- Authenticated network speed-test routes provide bounded 4 MiB upload / 8 MiB download and ping measurements for the device-to-API path.
- Customer network speed test has authenticated ping, bounded 4 MiB upload and bounded 8 MiB download endpoints; all responses are no-store.
- Workspace upload/retry authorization now requires an active workspace and owner or active member access.
- Existing principal resolution remains server-side from Supabase Auth and server-managed membership/role assignments.

### Remaining Phase 06 gaps
- Full route-by-route audit and response-model standardization across every Partner/Admin/Customer route remain open.
- Idempotency coverage for all mutation endpoints, cursor pagination for every list, WebSocket contract parity and OpenAPI compatibility acceptance remain open.
- No live RLS or cross-tenant denial proof was run.

## Phase 09 — Customer Dashboard source integration
- Speedtest screen no longer shows simulated ISP metrics. It measures real device ↔ MoreAI API round-trip, download and upload; labels explicitly state this is not ONT/gateway optical telemetry.
- The Analyse flow now reports idempotent duplicate-upload outcomes accurately instead of always claiming a new job was queued.
- Analyse screen now uploads the selected local PDF/image through the existing multipart FastAPI Knowledge ingestion path; fake sample documents and fabricated KPI/AI analysis output were removed.
- Research screen now reads the authenticated user's persisted Agent Run history. Fabricated popular topics are replaced by an explicit unavailable state until an official public research source is connected.
- Tools Catalog now reads the live OpenManus tool registry through FastAPI; static invented tools/actions were removed and runtime default policy is shown.
- Account Upgrade now reads active Customer entitlements from FastAPI; fabricated prices, storage promises and simulated successful checkout were removed because no payment/subscription checkout contract is currently available.
- Existing Knowledge Library file picker and Chat page-aware citations remain in place.
- Existing Customer UI structure and design tokens were not broadly restyled.

### Remaining Phase 09 gaps
- Security settings still needs real MFA enrollment/challenge/unenroll UI and session lifecycle; local-only toggles must not be treated as persisted security state.
- Device access control, Wi-Fi session extension/disconnect, EduTech video actions, creative generation, and remaining captive/partner-facing actions require real backend contracts or explicit unavailable states.
- Full route-by-route Customer screen/action coverage is not complete.

## Supabase and runtime safety
- Knowledge Storage/lease migration remains committed but unapplied. The worker uses server-only service-role credentials; no client key was added.
- Migration worker RPCs use invoker rights and explicit service-role execution grants; Storage bucket remains private with direct anon/authenticated object access denied.
- No Supabase schema mutation, migration apply, storage upload, provider call, test, lint, typecheck, build, browser session, staging or deployment was run in this increment.
- Source changes are committed, but production operation is not accepted until authorized migration/deploy/runtime verification.

## Phase status
- Phase 08: IN PROGRESS — substantial ingestion and registry/tool increments; full parity and runtime acceptance pending.
- Phase 06: IN PROGRESS — OpenAPI and selected contract/pagination increments; full route coverage and security acceptance pending.
- Phase 09: IN PROGRESS — multiple fabricated screens replaced with real backend data/operations; full Dashboard coverage pending.
- Phase 10: NOT ACCEPTED / waiting for explicit verification permission.
- Phase 11: BLOCKED / waiting for explicit release permission.

## Next dependency-ordered work
1. Finish Phase 08: remaining upstream exception/logger/web-session/tracker parity, complete tool adapters, provider retries/circuit breaker and capability-based route acceptance.
2. Finish Phase 06: audit every API/WebSocket route, standardize response schemas/pagination/idempotency, document role/tenant boundaries and generate compatibility evidence.
3. Finish Phase 09: integrate security MFA/session, device control, Wi-Fi session, EduTech, creative generation and all remaining Customer actions without mock data.
4. Only after those source phases are accepted, request explicit authorization for Phase 10 verification and Phase 11 release.


## 2026-11-12 direct-main continuation #3 — provider circuit breaker

- Added a provider/model scoped circuit breaker to `engine/llm/router.py` and wired it into both metered completion and streaming candidate selection.
- Retryable provider availability/transport failures increment the breaker; after the configured threshold, the route is skipped during the cooldown. After cooldown, only one half-open probe is admitted. Successful provider response resets the breaker.
- Non-retryable exceptions do not count as provider outages and release a half-open probe rather than silently failing over.
- Configuration: `MOREAI_PROVIDER_BREAKER_THRESHOLD` (default 3) and `MOREAI_PROVIDER_BREAKER_COOLDOWN_SECONDS` (default 30 seconds).
- Failover remains limited to retryable errors. Streaming does not switch providers after any text has been emitted, avoiding mixed provider output.
- This is intentionally process-local protection, not distributed/durable circuit state. Multi-worker consistency and provider health telemetry still require a shared Supabase-backed breaker/health service and acceptance. No retry is attempted against a provider after a non-retryable response.
- Commit: `d55aed3adb5fa0381832c68e6afdd671dab44273`.
- No tests, lint, typecheck, build, API/browser probes, provider calls, DB writes, migration, staging or deployment were run, as instructed.



## 2026-11-12 direct-main continuation #4 — gateway breaker wiring and EduTech progress

- Fixed a source-level integration defect in `MeteredGateway.__init__`: the new `ProviderCircuitBreaker` instance is now constructed and assigned to `self.breaker`, which is required by the completion and streaming paths that consult the breaker. Without this wiring, the first metered provider request would raise an attribute error before reaching the provider. Commit: `78be756a640a163197d244bbfcdd6637ce07b1ec`.
- Connected the existing Customer EduTech lesson checklist to the existing authenticated FastAPI learning-progress contract. The lesson screen now loads persisted progress for module `edu-1`, writes completion changes through `PUT /api/v1/customer/learning/progress`, and only updates local display state after the API confirms persistence. Commit: `bb333d7d8ec8f7bd5c94ce926d0cb199df309694`.
- The lesson video action no longer displays a fabricated “starting video” success; it states that video content is not yet available from the EduTech service.
- This is partial Phase 09 integration, not full EduTech catalog/content delivery. Module/lesson definitions still come from the existing frontend catalog, and video playback/content APIs are not yet implemented.
- No tests, lint, typecheck, build, browser/API probes, provider calls, DB writes, migrations, staging or deployment were run. The provider breaker is still process-local; durable shared state/health telemetry remains open.
