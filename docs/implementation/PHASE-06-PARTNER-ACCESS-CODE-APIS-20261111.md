# Phase 06/09 — Partner access-code and customer redemption APIs

- Added partner-scoped access-code inventory and redemption history endpoints, restricted to partner owner/admin roles and tenant IDs.
- Added customer access-code redemption endpoint. The raw code is SHA-256 hashed server-side and passed to the existing atomic redemption RPC; user identity comes from the authenticated customer principal and verification session/network are explicitly bound.
- API maps common verification, expiry, exhaustion, scope and idempotency failures to stable HTTP status responses.
- Typed frontend client now exposes partner code/redemption reads and customer redemption. No UI design/component changes.
- Runtime contract tests not run.
