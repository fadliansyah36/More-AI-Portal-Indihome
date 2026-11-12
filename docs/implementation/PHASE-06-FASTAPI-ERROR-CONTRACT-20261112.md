# Phase 06 — FastAPI Error Contract Normalization
Date: 2026-11-12
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main

## Scope
Normalize the API error envelope for HTTP errors, request validation errors, and unexpected exceptions while retaining status codes, correlation IDs, and authentication challenge headers.

## Implementation
- Added one shared error response builder in `apps/api/app/main.py`.
- Registered an `HTTPException` handler mapping common HTTP statuses to stable machine-readable error codes.
- Preserved `WWW-Authenticate` and other exception response headers.
- Registered a `RequestValidationError` handler returning safe field locations/types/messages without echoing submitted values.
- Kept unexpected exception responses generic; internal exception details are not exposed.
- All normalized errors include the request correlation ID.

## Commit
- `0d0ef242dd17713b8fa649ba74e3c988b6379353`

## Compatibility
The response uses the existing client-readable `error.message` property. Existing HTTP status semantics remain unchanged. Endpoint-specific successful response shapes are untouched.

## Verification boundary
No tests, lint, typecheck, OpenAPI generation, build, API runtime, staging, migration, or deployment was run. This is a source implementation increment, not Phase 06 acceptance.

## Remaining Phase 06
- Reconcile route-by-route auth, role, tenant, workspace, and resource ownership contracts.
- Normalize existing endpoint-local JSONResponse errors that bypass exception handlers.
- Complete idempotency and OpenAPI contract coverage.
- Verify every Customer API client method maps to an implemented route and response schema.
