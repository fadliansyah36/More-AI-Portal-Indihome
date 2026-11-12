# Workspace Durable Run Session Listing — 2026-11-12

## Implemented

- `GET /api/v1/customer/workspaces/{workspace_id}/runs?limit=50`.
- Requires authenticated Customer principal and accessible active workspace.
- Validates limit to 1–100.
- Restricts results to the requesting user's own runs even when they are a shared workspace member.
- Returns lifecycle metadata only; excludes prompts, inputs, outputs, private tool arguments, and observations.
- Adds typed `workspaceApi.runs(workspaceId, limit)`.

## Commits

- FastAPI: `0cb9a0bc3c288315184dc8866fdcf91f619caa89`
- Typed API client: `5d123d879f387f4177f26b1957b5fe35d9053e33`
- Tracker: `6958d83acc5a54fd005d205cc48e584a2096ed77`

## Remaining Phase 04

Workspace file create/upload/update/rename/delete still needs a lease-fenced customer-facing mutation design; direct metadata mutation would bypass the immutable CAS protocol, so it was not introduced. Upstream server/session creation, websocket, logs/thinking tracker, full Flow Engine semantics, and isolated browser/sandbox supervisor remain open.

## Verification

No tests, build, lint, OpenAPI generation, runtime, browser E2E, staging, or deployment were run. Source commits only; runtime acceptance is not claimed.

## Next

Continue Phase 04 by integrating the remaining upstream server/session and Flow capabilities through durable Supabase-backed contracts, then complete safe workspace file mutation and browser/sandbox isolation. Continue Phase 07 → Phase 08 → Phase 06 → Phase 09 after dependency gates.
