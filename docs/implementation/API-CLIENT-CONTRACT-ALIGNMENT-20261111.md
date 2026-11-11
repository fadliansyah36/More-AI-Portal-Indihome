# MoreAI — API Client Contract Alignment

Date: 2026-11-11
Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Implementation commit: `c2e1c5a437485207a09712d3e118f095b5e579eb`

## Scope

Aligned the existing browser API client with the actual authenticated FastAPI contracts used by the Customer conversation and durable Agent Run workflow.

## Changes

- Added `customerApi.getConversation(conversationId)` for the existing owner-scoped Customer conversation detail endpoint. The return type models the conversation plus persisted message history.
- Added `customerApi.getRunEvents(runId, after)` for the durable, sequence-ordered run event replay endpoint. The cursor is clamped to a non-negative integer.
- Corrected `CustomerWorkflowStep` to match the metadata-only response from `GET /api/v1/agent-runs/{run_id}/steps`. Removed input/output/error/updated_at fields that the API intentionally does not expose.

## Security and UI preservation

- Reuses the existing authenticated FastAPI client; no direct Supabase business-data access was added.
- Does not expose private step input/output/error payloads through the frontend contract.
- No UI components, routes, styles or navigation were changed.

## Verification and limitations

- No tests, build, lint, typecheck, staging, provider calls, database writes or deployment were run, per product-owner instruction.
- This commit is a typed API contract alignment increment only; it does not prove runtime endpoint behavior or complete page-level UI integration.

## Next

Continue Phase 04 Flow/server parity and Phase 07 durable event lifecycle, then map and connect every existing Customer, Partner and Super Admin screen to the real typed API methods without redesigning the UI.
