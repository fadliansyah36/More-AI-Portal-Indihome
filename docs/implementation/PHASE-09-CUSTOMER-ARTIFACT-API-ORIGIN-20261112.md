# Customer Artifact API Origin Alignment
Date: 2026-11-12
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main

## Scope
Phase 09 source integration correction for the existing Customer Files view. The UI and artifact behavior are unchanged.

## Implementation
- Updated the existing `artifactApi` list, upload, and signed-download methods in `lib/api/client.ts` to use `moreAiCustomerApi`.
- This ensures all three Customer artifact operations honor `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL` when configured, with the existing fallback to `NEXT_PUBLIC_MOREAI_API_URL`.
- Supabase Auth bearer-token handling, retry-on-401 behavior, private signed-download flow, and server-side authorization remain in the existing shared API transport.
- No direct browser Supabase Storage, PostgREST, RPC, or Realtime access was added.
- No UI component or visual styling was changed.

## Commit
- `a28719068ccdefb05d0fed88b0975799a89358eb` — `fix(customer): route artifact API through customer origin`

## Verification boundary
Source commit only. No tests, lint, typecheck, build, browser QA, API runtime call, staging, migration, or deployment was run. This does not constitute Phase 09 acceptance.

## Remaining phase status
Phase 04, 07, 08, 06, and 09 remain IN PROGRESS. The remaining work is substantial: workspace file CRUD and restore lifecycle; complete upstream Flow/server/session compatibility; browser supervisor and isolated sandbox security; durable retry/timeout/cancellation/lease/approval race recovery; complete agent/tool/provider fallback/memory/RAG parity; route-by-route OpenAPI/auth/tenant/idempotency reconciliation; and the remaining Customer screens and real domain API coverage.

## Next execution
Continue Phase 04 first: complete the endpoint/capability parity map for the pinned OpenManusWeb server and implement the missing durable Flow/session and workspace mutation semantics behind FastAPI. Then continue Phase 07, Phase 08, Phase 06, and Phase 09 in the required order.
