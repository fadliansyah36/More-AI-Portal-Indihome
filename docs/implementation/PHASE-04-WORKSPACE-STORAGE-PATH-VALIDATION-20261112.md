# Phase 04 — Workspace Storage URL Validation Follow-up
Date: 2026-11-12
Branch: main

## Changes
Commit `53a2850bde142f4a4f01ea75e7470e13a7e9665f` updates `apps/api/app/routers/workspaces.py`:
- Rejects any backslash in a relative Storage signed path (including a single backslash).
- URL-encodes the configured Storage bucket name in both bucket lookup and signed-object URL construction.
- Retains same-origin HTTPS validation for absolute signed URLs, rejection of protocol-relative paths, userinfo, and control characters.
- Preserves the existing owner/member workspace authorization and private-bucket requirement.

## Why
The prior guard checked for a two-backslash sequence, which did not reject a single backslash. Bucket names were also interpolated into URL path segments without encoding. This closes both input/path construction gaps at the workspace download boundary.

## Verification boundary
Source-only implementation commit. No test suite, lint, typecheck, build, API runtime, browser QA, staging, migration, or deployment was run. Phase 04 is not accepted as complete.

## Remaining work
Phase 04 still requires complete OpenManus backend capability parity, durable Flow/server/session integration, full workspace mutation/restore UI and lifecycle, browser supervisor and sandbox runtime security. Dependent phases 07, 08, 06, and 09 remain open as tracked.
