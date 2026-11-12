# Phase 04 / 06 — WebSocket Session Replay Cursor Correction

Date: 2026-11-13
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main

## Finding
The authenticated Agent Run WebSocket replay endpoint previously fetched the latest 200 events in descending order, reversed them, and advanced the stream cursor to the maximum sequence. On reconnect with a caller-supplied `after` cursor, this initial batch could include already-acknowledged events and advance past a gap, violating strict replay semantics.

## Implemented
File: `apps/api/app/routers/agent_runs.py`
- Initial replay now applies `sequence=gt.{cursor}`.
- Initial replay uses ascending sequence order.
- The batch remains bounded to 200 events.
- Subsequent polling already uses the updated cursor and ascending sequence order.
- Conversation session WebSocket continues to delegate to the same authenticated run stream after checking conversation ownership and run association.

Commit: `66a374c6d1969f020a92e9adf71c03c159954de5`

## Safety and verification
- No test, lint, typecheck, build, browser/API runtime call, staging, database migration, or deployment was run.
- This is a source-level replay correctness fix only. Runtime event delivery, reconnect behavior under concurrent writes, and WebSocket lifecycle acceptance remain unverified.

## Phase status
- Phase 04: IN PROGRESS.
- Phase 06: IN PROGRESS.
- Phase 07: IN PROGRESS.
- Phase 08: IN PROGRESS.
- Phase 09: IN PROGRESS.
