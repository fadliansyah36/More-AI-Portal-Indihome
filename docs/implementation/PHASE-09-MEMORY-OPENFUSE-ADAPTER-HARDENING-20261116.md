# Phase 09 — Memory and OpenFuse adapter integration hardening

Date: 2026-11-16  
Branch: `main`  
Scope: source-level corrections to Unified Memory retrieval fault isolation and the single OpenFuse supervisor adapter lifecycle.

## Source changes committed

1. `e2586b44915de8402739d6724761f5b1eb792b45` — `engine/agents/memory_context.py`
   - Personal Memory retrieval is an optional, consented context source, just like semantic and episodic recall.
   - A transient Personal Memory store failure is now isolated and recorded through the existing safe memory-diagnostic event publisher (`agent.memory.personal_retrieval_failed`).
   - The Agent Run can continue with durable working checkpoints and conversation history rather than failing solely because optional Personal Memory retrieval is temporarily unavailable.
   - The failure event includes only the exception type, not memory content, prompts or credentials. No consent, owner scope, retention or deletion behavior was relaxed.

2. `7fb9e3c857afc1b7f46a20abbc7c4785021941b1` — `apps/worker/app/registry_factory.py`
   - Agent registry construction now receives the already validated `BrowserSupervisor` instance from worker startup.
   - Browser activation remains fail-closed if the browser runtime flag is enabled but no prevalidated supervisor was supplied; passing a supervisor while browser runtime is disabled is rejected.
   - Removed the second independently constructed BrowserSupervisor inside registry construction.

3. `dc66ae9203bb6f3de623c55ec2769f1b7f3ecabb` — `apps/worker/app/main.py`
   - Worker startup passes the single BrowserSupervisor instance, whose readiness was checked before registry creation, into `build_agent_registry`.
   - The same adapter instance is now used by durable Agent tool calls and the worker's browser-session close/profile-retention reconciliation loop. This removes duplicate configuration/object construction and prevents drift between the action path and lifecycle-management path.

## Architecture and data flow

- Customer browser actions continue through the typed Customer API → FastAPI ownership/approval/action-receipt boundary → durable worker → isolated OpenFuse service.
- Worker startup constructs and validates one BrowserSupervisor. It is shared by the registered OpenManus browser tool and the lifecycle reconciler.
- Memory coordinator continues to compose Working, Conversation, Personal/Long-term, Episodic, Semantic and Procedural context. Personal Memory retrieval is best-effort and consent-gated; durable conversation/checkpoint retrieval and approved Skill resolution remain authoritative.
- No new database, persistence store, route, provider, permission or browser capability was introduced.

## Files and protected UI

- Changed: `engine/agents/memory_context.py`, `apps/worker/app/registry_factory.py`, `apps/worker/app/main.py`.
- No frontend/UI files, routes, CSS, design tokens, Supabase migrations, Supabase data, environment secrets, provider configuration or deployment settings were changed.
- No direct browser-to-Supabase access was added.

## Verification and operational status

Per product-owner instruction, no tests, builds, lint, type-check, API/browser/worker runtime calls, provider calls, Docker execution, staging, migration apply or deployment were performed. These source changes are not runtime-verified.

OpenFuse host, encrypted persistent profile volume, immutable ClamAV digest, egress allowlist, secret injection, live worker heartbeat and provider/model/wallet readiness remain external operational blockers. No capability is represented as active by these source changes.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED** and Phase 11 remains **BLOCKED**.
