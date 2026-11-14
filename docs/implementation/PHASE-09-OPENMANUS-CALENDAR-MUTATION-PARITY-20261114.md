# Phase 09 Continuation — OpenManus Calendar Mutation Parity

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Baseline HEAD: `0afea6b10d7c362be8b1629963493f5618a0d086`  
Status: **SOURCE IMPLEMENTATION COMMITTED — NOT RUNTIME VERIFIED; PHASE 09 REMAINS IN PROGRESS**

## Scope

This increment closes the worker-side OpenManus parity gap for Google Calendar event update and delete. It extends the existing OpenManus runtime and FastAPI Google Connections adapter; it does not add another agent runtime or browser UI.

## Implemented source changes

- `engine/tools/catalog.py`: added `calendar_update_event` and `calendar_delete_event` definitions for Manus, Planning and ToolCall; both are critical-risk tools and require explicit approval.
- `engine/tools/policy.py`: classified both actions as high-risk/default-deny.
- `engine/agents/durable_tool_runtime.py`: maps the existing `calendar.write` skill permission to the two new tools, enables them only when the Google connection adapter exists, and registers their handlers in the same policy-enforced OpenManus tool registry.
- `apps/worker/app/connection_tools.py`: validates action inputs, binds each operation to a run/user, and creates deterministic run-and-payload idempotency keys.
- `apps/api/app/routers/connections.py`: internal Calendar list now returns each event's ETag and selected Google connection ID. Internal update/delete endpoints authenticate the worker token, require a currently running Agent Run owned by the same user, bind the exact owner-owned Google connection and Calendar write scope, fetch the current provider event, compare the fresh ETag, claim a durable connection-action receipt, and pass the same ETag as `If-Match` to Google. Ambiguous provider outcomes are recorded as `unknown` and are not automatically retried.

## Approval and data flow

`OpenManus tool call → existing durable run-scoped approval gate → worker GoogleConnectionTools → internal FastAPI endpoint → owner/run/connection/scope checks → fresh Google ETag check → idempotent Supabase action receipt → Google Calendar mutation → final action receipt`

The browser never receives Google credentials. The worker does not choose a different Google connection during mutation: the connection ID returned with the event listing is required by update/delete.

## Supabase and migrations

The existing forward-only migration `20261114108000_moreai_calendar_event_mutation_actions.sql` already adds `calendar.update` and `calendar.delete` to the action receipt allowlist. No new migration was required for this worker parity increment. No Supabase schema operation or migration application was performed in this increment.

## UI preservation

No UI files were changed. The existing Customer Connections Center remains the customer-facing surface. OpenManus mutations are exposed only through the existing Agent Runtime and existing approval workflow.

## Verification and release boundary

Per product-owner instruction, no tests, lint, typecheck, build, API/provider probes, browser checks, worker execution, staging, deployment or live OAuth operations were run. This report records source changes only; it does not claim runtime acceptance or Phase 09 completion.

## Remaining Phase 09 work

1. Persistent OpenFuse browser session lifecycle through FastAPI and Supabase: tenant/owner identity, durable session metadata, encrypted state handling, restore/close/expiry and lifecycle receipts.
2. Browser download lifecycle: bounded capture, quarantine, MIME/content validation, malware scanning with fail-closed behavior, owner-scoped artifact persistence, signed download and cleanup.
3. Memory Coordinator reconciliation across Working, Conversation, Long-term, Episodic, Semantic and Procedural memory while preserving existing Conversation Memory, consented Personal Memory, Knowledge/RAG and durable Agent Run checkpoints as distinct sources.
4. Complete Customer Dashboard route/action reconciliation against typed FastAPI contracts; remove only confirmed simulated actions and add missing UI only where a PRD workflow is genuinely absent.
5. Continue the OpenFuse 219-path and AI Skills provenance/license/capability review; this increment does not close those inventories.

**Next dependency:** Phase 09 Continuation — Persistent OpenFuse Browser Session Lifecycle. Download import remains disabled until quarantine, scanning and tenant-scoped artifact controls are implemented. Phase 10 verification and Phase 11 release gate remain blocked under the current no-testing/no-staging instruction.
