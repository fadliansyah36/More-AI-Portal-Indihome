# Phase 09 — Customer Terminal Lifecycle & API-Origin Parity

Date: 2026-11-13  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Scope: source-level Customer dashboard integration corrections. Existing visual UI is preserved.

## Implemented

1. **SSE terminal-state parity**
   - Added `run.timed_out` to the browser stream parser's terminal event set.
   - Chat now maps `run.timed_out` and `run.expired` events to terminal states.
   - Chat's persisted-run polling now recognizes `timed_out` and `expired` as terminal statuses.
   - Chat renders a timeout/expired explanation rather than showing a generic still-processing state.
   - Commits: `1710a01ae8f3e0eb2de614dc8960574eda06b3d3`, `750aa79435eea59c9c0eb78e1fc0fecebfdfbd01`.

2. **Customer API origin consistency**
   - Profile get/update, notifications list/preferences/read/read-all, tools catalog and model capabilities now route through `moreAiCustomerApi`.
   - This honors `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL` when a separate Customer API origin is configured instead of silently falling back to the generic API origin.
   - Commit: `009741623e081dfa5543feb7f537b7d69f43ba6b`.

3. **Typed Agent Studio catalog**
   - Added `CustomerAgentCatalogItem` and `customerApi.agents()` for `GET /api/v1/agents`.
   - Agent Studio now consumes the typed Customer API method rather than defining an inline response shape at the call site.
   - Commit: `4e709c282d5b148f00b3e35ba50b72d0fb8e0642`.

## UI/UX impact

- No layout, copy, styles, spacing, colors, typography, navigation, or component hierarchy was changed.
- The Chat view changes only terminal event/status handling and the resulting status text/source label.
- No before/after browser screenshots were generated because the requested execution boundary excludes browser/runtime checks.

## Verification boundary

- Source files were read from `main` before updates and committed directly to `main`.
- No tests, lint, typecheck, build, browser checks, screenshots, API probes, worker execution, staging, migrations, or deployment were run in this increment.
- This report documents source-level implementation only; it does not claim runtime acceptance.

## Remaining Phase 09 work

- Continue reviewing Customer workspace/file/version/artifact/approval/wallet/quota/learning/notification action parity against FastAPI response schemas and authorization.
- Close only provider-independent API gaps where a real backend contract exists.
- Keep Captive Gateway, EduTech catalog/video, payment settlement, and support workflows fail-closed until their authoritative provider contracts, configuration, and server-side adapters exist.
- Provider adapters remain blocked by missing real credentials/configuration and contracts; no mock integrations are acceptable.

4. **Terminal run classification in Customer history**
   - Tasks now classifies `succeeded`, `failed`, `cancelled`, `timed_out`, and `expired` as terminal so these runs no longer remain in the active filter.
   - Workflow history now gives `timed_out` a clear Indonesian status label.
   - Commits: `49a7eb5d164f89a843960b0a3d27fbd1cc8b8281`, `195c2a90228adcda042e4be61907e1ec08fa3cd7`.
