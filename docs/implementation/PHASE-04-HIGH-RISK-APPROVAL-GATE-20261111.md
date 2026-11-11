# Phase 04 — Independent high-risk approval gate wiring
Date: 2026-11-11
Branch: `main`

## Change
Updated `apps/worker/app/registry_factory.py` so `DurableOpenManusRuntime` always receives the durable `WorkerRpcClient.wait_for_tool_approval` gate. Previously, the gate was supplied only when the Docker sandbox adapter was enabled. That accidentally coupled approval availability to sandbox configuration: an independently enabled browser supervisor was advertised by the tool registry but had no approval gate and would fail closed at execution.

## Result
- Browser and sandbox tools now share the same run/user/tool/argument-hash approval flow whenever their adapters are independently enabled.
- Approval remains owner-scoped and one-time consumption remains delegated to the existing `moreai_consume_tool_approval` RPC.
- No browser or sandbox adapter was enabled by this change. Their existing independent environment/release gates remain mandatory.
- This does not implement run-level lease release/reclaim after approval; the worker currently waits while holding its lease and heartbeats it. That behavior remains an explicit limitation.

## Constraints
No staging, runtime test, provider call, production write, migration, build, lint, typecheck or deployment was run. UI untouched. Phase 04 remains IN PROGRESS.
