# Phase 06/09 — Customer financial and usage read APIs

- Added authenticated customer wallet summary, immutable credit ledger pagination, LLM usage history, active entitlement listing and scoped quota/usage read models.
- Every endpoint derives user identity from the authenticated principal; wallet reads are restricted to owner_type=user/owner_id=current user; ledger is restricted to those wallet IDs; usage and entitlements are user scoped.
- Fixed typed frontend API client run list/detail/steps/stream paths to use the existing `/api/v1/agent-runs` contract rather than nonexistent `/customer/agent-runs` paths.
- No visual/UI component changes. No financial mutation or credit adjustment endpoints added; wallet/ledger remain read-only to customers.
- Runtime/API contract tests were not run.
