# Phase 04 — Workspace CAS reservation expiry recovery

- Added a five-minute reservation expiry to pending SWE workspace writes.
- A worker crash after reservation no longer permanently blocks a file: a later CAS writer can reclaim an expired reservation; read metadata also clears an expired pending reservation.
- Commit requires an unexpired reservation token plus the current worker lease, version and run binding.
- Migration: `20261111170000_moreai_workspace_cas_expiry_recovery.sql`.
