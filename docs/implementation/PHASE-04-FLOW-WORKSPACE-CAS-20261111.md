# Phase 04 — Durable FlowFactory and SWE workspace CAS
Date: 2026-11-11

- Worker registry now creates PlanningAgentRuntime through the allowlisted FlowFactory; the adapter deliberately avoids upstream PlanningFlow process-global log/task state and delegates plan/step persistence to Supabase.
- SWE workspace files now use immutable versioned Storage objects and a Postgres metadata pointer. `expected_version` is checked before a lease-fenced reservation; commit requires the same run lease, write token and version. Failed uploads attempt reservation abort. File reads are workspace owner/member scoped.
- Browser egress architecture is present in source: internal-only browser supervisor, authenticated CONNECT proxy, exact domain allowlist, DNS pinning, public-IP validation and peer-IP check. Browser runtime remains disabled unless deployment asserts egress enforcement.
- Migration applied: `20261111150000_moreai_workspace_file_cas_versioning.sql`.
- No runtime execution or tests were performed. Flow lifecycle parity beyond Planning, full upstream server/session parity and browser end-to-end network verification remain incomplete.
