# ADR-004: Durable Server-Sent Events for Agent Run Streaming

- Status: Accepted for the current MoreAI web client; WebSocket parity is deferred.
- Date: 2026-11-11
- Scope: Browser-facing delivery of durable agent-run events from FastAPI.

## Context

The upstream OpenManusWeb frontend uses a WebSocket-oriented interaction model. MoreAI separates the existing Next.js UI from the backend runtime and persists run state, event sequence numbers, and checkpoints in Supabase. A reconnectable transport must support authenticated browser access, event replay, proxy compatibility, and durable run status without making the browser a privileged database client.

## Decision

Use authenticated HTTP Server-Sent Events (SSE) for server-to-browser run event delivery. Keep command operations (create conversation, enqueue message, cancel run, retrieve run state) as authenticated FastAPI HTTP endpoints. Supabase remains server-side behind FastAPI and Worker.

The SSE endpoint accepts a monotonically increasing `after` cursor. Each event includes its durable sequence as the SSE `id`; reconnect clients resume from the last processed sequence. The stream reads persisted `agent_run_events` and checkpoint state, emits keep-alives, and emits a terminal event based on authoritative `agent_runs.status`.

## Why not WebSocket now

- Agent execution is asynchronous and durable; the event log, not a socket session, is the source of truth.
- SSE provides one-way streaming with standard HTTP auth, simpler reverse-proxy support, and native reconnect semantics.
- Client-to-server actions are discrete commands and fit HTTP request/response semantics.
- Persisted sequence cursors make reconnect/replay independent of worker process lifetime.

## Required parity and safeguards

- Event type and payload contracts must be documented and versioned.
- Every stream request must authenticate a current Supabase access token and verify run ownership before streaming.
- Every query must be scoped to the authorized run and tenant context.
- Event sequence must be monotonic per run; reconnect with `after` must not silently skip events.
- Terminal status is read from the durable run record; client stream completion is not proof of run success.
- Apply connection limits, request timeouts, keep-alives, proxy buffering disablement, and cancellation on disconnect.
- Do not send provider secrets, internal chain-of-thought, raw tool credentials, or unredacted exception traces in event payloads.
- Tests must cover replay, duplicate delivery tolerance, terminal states, disconnect, unauthorized access, cross-user denial, and checkpoint ordering.

## Consequences

SSE replaces the transport mechanism, not the upstream session/run/event semantics. The application must preserve durable run lifecycle, cancellation, progress, logs, and event replay. A bidirectional socket is not required for current product behavior; if future interactive tool sessions require it, introduce a separate scoped WebSocket protocol without bypassing the same auth, ownership, audit, and event persistence rules.

## Current implementation status

FastAPI exposes authenticated run detail, cancel, event list, and SSE stream endpoints. Event sequence IDs and checkpoint hydration are implemented. This ADR does not certify full upstream parity: session revocation/session_id checks, event schema versioning, full log redaction/retention, replay edge-case tests, and production connection management remain release gates.
