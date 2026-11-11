# Phase 04 — OpenManus approval key alignment
Date: 2026-11-11

## Scope
Resolve a concrete mismatch between canonical runtime tool identifiers, the approval API schema and the persisted Supabase approval allowlist.

## Findings
- The policy-enforced tool registry uses `browser_use` for the upstream browser tool.
- The PlanningAgentRuntime requests durable approval using `planning_step` for high-risk or non-basic planning steps.
- The Customer approval Pydantic schema, the `agent_tool_approvals.tool_key` check constraint, and `moreai_request_tool_approval` allowlist did not consistently accept these canonical keys. This could reject an approval before the existing durable pause/resume and single-use consumption lifecycle could complete.

## Changes
- `apps/api/app/routers/tool_approvals.py`: accepts canonical `browser_use` and `planning_step`, retaining existing compatibility keys.
- `supabase/migrations/20261111180000_moreai_openmanus_approval_tool_keys.sql`: forward-only change to the check constraint and server-only request RPC allowlist. Existing ownership check, argument hash validation, expiry, reuse semantics, SECURITY DEFINER search_path and service_role-only EXECUTE are preserved.
- Migration applied to canonical Supabase project `uunfgimtokhucegqbpce`.
- Commits: `379944a6d4715ce551155df7fe39d38882a79a56` (migration file), `5af4da0670319326d2e562f6e4a3f21961f3f7d7` (API schema).

## Verification
- Read-only SQL inspection confirms the table constraint contains both canonical keys.
- Function ACL inspection confirms EXECUTE is held by postgres and service_role only; no PUBLIC/anon/authenticated execute grant is present.
- Supabase Security Advisor still reports leaked-password protection disabled (WARN); no Auth setting was changed.
- No worker runtime, provider, staging, browser, test suite, build, lint, typecheck or deployment was run. This is a contract/schema verification, not end-to-end Phase 04 acceptance.

## Remaining Phase 04 blockers
- A deployed browser supervisor must enforce DNS resolution pinning, private/link-local IP rejection, redirect and subresource checks at the socket/egress boundary, plus download and resource controls. A worker-side HTTPS client and environment boolean are not proof of this enforcement.
- Full upstream session/WebSocket, Flow lifecycle, server API, log/tracking and remaining agent/tool parity must be mapped and integrated.
- SWE execution still needs a complete isolated workspace/sandbox execution contract; the current Storage-backed editor alone is not full SWE agent parity.
- Runtime acceptance must be performed in an authorized isolated environment before any high-risk adapter is activated.

## Next
Continue Phase 04: implement/verify the isolated browser supervisor and complete the remaining upstream backend capability mapping. Do not advance to Phase 07/08/06/09 until Phase 04 is actually accepted.
