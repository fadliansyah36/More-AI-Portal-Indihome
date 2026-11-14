# Phase 09 — Customer EduTech Progress Count Contract Correction

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Implementation commit: `45481e9b8352edfa55f55264f9f95b8c57cb3188`

## Scope

Correct the Customer EduTech progress summary contract without changing the protected Customer UI, adding a second learning engine, or bypassing FastAPI.

## Finding

The existing `GET /api/v1/customer/learning/progress/detail` endpoint returned `count = len(items)`. Since the endpoint caps the returned page at 500 records, the EduTech screen's progress summary could under-report a learner's actual canonical progress records once the account exceeded that page size.

## Implemented

- Added `SupabaseRepository.count(table, params)`, using a server-side PostgREST HEAD request with `Prefer: count=exact` and a bounded `Range: 0-0`.
- The count query preserves the caller-supplied filters, excludes page-only parameters, and requires a numeric exact `Content-Range` total. Missing exact-count metadata fails closed with a bounded API error rather than silently reporting a page count.
- Updated the canonical learning progress detail route to return the limited, owner-scoped `items` page and an exact owner-scoped total in the existing `count` field.
- No browser-to-Supabase access, new schema, migration, UI redesign, or change to the learning write lifecycle was introduced.

## Files changed

- `apps/api/app/repositories/supabase.py`
- `apps/api/app/routers/learning.py`

## Verification boundary

Per product-owner instruction, no tests, lint, typecheck, build, browser/API probes, worker execution, provider calls, staging, or deployment were performed. The change is source-committed but runtime behavior is NOT VERIFIED. No Supabase schema or data mutation was performed.

## Phase status and next work

Phase 09 remains **IN PROGRESS**. This closes one Customer EduTech summary-contract discrepancy only; it does not close the full Customer Dashboard integration.

Next dependency-ordered work remains:
1. Continue Customer screen/action to FastAPI contract reconciliation across remaining dashboard domains.
2. Close source-backed workflow/task, artifact and media lifecycle gaps without introducing parallel engines or fabricated provider states.
3. Keep external payment settlement, captive OTP/gateway activation and OAuth connector lifecycle fail-closed until real provider contracts and credentials are supplied.
4. Keep Phase 10 and Phase 11 unaccepted until the product owner authorizes the required verification and release gates.
