# MoreAI — Phase 07/08 Bounded Tool Deadline Increment

Date: 2026-11-12  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Execution mode: source changes only; no runtime/test/deployment activity.

## Scope delivered

### Per-tool deadline and cancellation

Updated `engine/agents/durable_tool_runtime.py`:

- `_run_tool_until_cancelled` now races the active adapter task against both the durable run cancellation event and a bounded deadline.
- If the deadline expires, the adapter coroutine is cancelled and awaited before a `TimeoutError` is raised to the tool loop.
- If cancellation wins, existing cancellation propagation remains distinct and raises `CancelledError`.
- Tool timeout is configurable through `tool_timeout_seconds`, validated to the inclusive range 1–1800 seconds.
- Timeout is persisted as a distinct `timed_out` outcome with a bounded observation containing `tool_execution_timed_out`, the deadline and tool key. The settled checkpoint makes retry/recovery reuse the recorded observation rather than rerun the same tool intent.
- Worker registry reads `MOREAI_TOOL_TIMEOUT_SECONDS`; default is 120 seconds. `.env.example` documents this setting.

## Commits

- `cbcbda694206a0c2904b6a5626dc04feff292d07` — enforce bounded durable tool execution deadlines.
- `ca7dce8dcd92f638997adad2abca68f71b62d3c6` — expose worker timeout configuration.
- `e363526fbb820a2f794fc21c48eda0079cf797fa` — document environment setting.
- `92639fbeec936a0e8cc04ce72fe5afb245f55092` — persist explicit timeout outcomes.
- `60395ca0348e2d6c2d427148779ff5cd77e4d708` — phase tracker update.

## Explicitly not completed by this increment

- Provider HTTP timeout remains governed by the provider adapter's HTTP client timeout; this change is specifically the tool invocation boundary.
- Full upstream OpenManus Flow base/factory/planning/server/session/WebSocket parity remains partial.
- Adapter-specific proof that subprocesses, network calls and external services stop promptly after cancellation/deadline still requires authorized runtime tests.
- Phase 07 event replay/outbox acceptance and lease fencing still require full acceptance evidence.
- Phase 04 sandbox/browser/SWE security gates remain open.
- Phase 08 full upstream tool handlers, provider retry/circuit-breaker parity and complete RAG remain open.
- Phase 05/06 remaining PRD schema and API contracts, Phase 09 domain UI integration, Phase 10 end-to-end verification and Phase 11 release gate remain open.

## Verification boundary

No test, lint, typecheck, build, live provider call, worker runtime, Supabase migration/apply, browser QA, staging, production call or deployment was performed. No test-pass or release-readiness claim is made. Do not enable high-risk tools or runtime flags based only on this source change.
