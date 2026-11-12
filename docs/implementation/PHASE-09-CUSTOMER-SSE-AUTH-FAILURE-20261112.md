# Customer SSE Authentication Recovery Correction
Date: 2026-11-12
Branch: main

## Finding
The Customer SSE client refreshed Supabase Auth after a 401, but a failed refresh threw inside the same catch block used for transient transport failures. That caused an expired/invalid session to be treated as a retryable network failure and could repeatedly reconnect with no valid credentials.

## Change
- Mark refresh failure as terminal before clearing the local Supabase session.
- Rethrow authentication failure immediately instead of applying exponential reconnect backoff.
- Preserve bounded reconnect behavior for actual transport failures and keep the existing event cursor semantics.

## Commit
- 31335899ece903328c01772d416157f7fb3a22b8

## Verification
No tests, lint, typecheck, build, browser, runtime API call, staging or deployment were run. Source-level correction only.
