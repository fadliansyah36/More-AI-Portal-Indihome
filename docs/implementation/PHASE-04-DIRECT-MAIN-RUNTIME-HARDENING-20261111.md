# Phase 04 — Direct-main Runtime Hardening Report

Date: 2026-11-11
Target: `main`
Reference: `AGENTS.md`, pinned OpenManusWeb source manifest, existing Phase 04 capability map and worker architecture.

## Scope completed in this increment

- Hardened `engine/agents/runtime.py` tool-call normalization for both provider SDK objects and plain dictionary responses.
- Validates tool-call list shape, function name, call ID, JSON argument syntax and object-only arguments before dispatch.
- Preserves the OpenManus tool-call message cycle: assistant tool-call message → tool execution → tool observation linked by `tool_call_id` → next model iteration.
- Converts handler failures into redacted tool observations so raw exception messages, tokens and provider internals are not sent back to the model.
- Adds explicit terminal states for cancellation and maximum-step exhaustion; rejects empty requests and invalid max-step configuration.
- Adds runtime tests for object/dict provider responses, successful tool roundtrip, invalid argument rejection, redacted failures, cancellation and step exhaustion.
- Hardens `PolicyEnforcedToolRegistry` with catalog-based argument validation, default-deny policy checks, per-tool timeout enforcement, normalized tool keys and strict text output validation.
- Adds dispatcher tests proving invalid schemas and unapproved tools never reach handlers.
- Adds a durable conversation-memory contract and Supabase adapter using the already-existing `conversations` and `conversation_messages` tables (both RLS-enabled in the live project); no new migration was applied.
- The memory adapter verifies conversation owner and workspace on every read/write, persists messages with run/message idempotency keys, and restores assistant tool-call metadata.
- Wires this adapter into the existing worker Manus runtime so previous conversation turns are restored and user/assistant turns are persisted.
- Declares pinned engine test dependencies and adds the engine test suite to the Phase 04 CI workflow, including engine/worker path filters.
- Updates the phase tracker to reflect direct-main execution and remaining parity gates.

## Commits on main

- `13f7353d1ed6252f1313f3d47a6ede159b7ed0b3` — runtime hardening.
- `2eda22e07efc38398080dba2c512eb5cef167bf0` — terminal lifecycle states.
- `11e724242c69d76b152fca7d96441e5ede2d2759` — runtime tests.
- `59acb70953c6cb6ca5e35cb641e403e4a41248f3` — pinned engine test dependencies.
- `e2eb64c147f2f4a8d5ad92d152c20a4d76e5b6ca` — CI engine test job and path filters.
- `63abe5f52ad2aa4016af2f1a54e496c4ca16deda` — phase tracker update.

## Important gaps — Phase 04 remains open

This increment does not yet establish full upstream backend parity:

1. Worker `build_agent_registry` still wires `GatewayManusRuntime` (text-only) and `PlanningAgentRuntime`; it does not yet wire `ToolCallAgent`/the policy registry into the durable worker.
2. The existing OpenAI-compatible adapter currently sends text-only completion/stream requests; structured provider tool-call transport and usage settlement for tool rounds still need implementation.
3. The catalog includes Bash, Python, browser and editor capabilities, but their actual sandbox supervisor adapters are not all wired. These remain disabled; no unsafe execution was enabled.
4. No durable conversation memory adapter is currently present under `engine/memory`. Existing worker checkpoints and planning persistence do not by themselves prove cross-run short-term or long-term memory parity. The correct existing Supabase schema and consent/retention controls must be verified before implementing persistence.
5. Upstream FlowFactory/PlanningFlow coverage, recovery/replay semantics, tool audit/approval and tenant-isolation tests remain incomplete.
6. No provider API keys, model routes, wallet/entitlement seed data, production worker activation, live provider test or deployment was performed.

## Verification status

The first engine CI run exposed two implementation/configuration defects: the new terminal enum was committed with escaped newline characters, and the existing Engine Contract Tests workflow installed pytest without the newly required async plugin. Both were corrected on main (enum syntax commit `2e27af9e365997aa459a009b748f923c8892166c`; workflow dependency commit `410c76391bf096b86b68d5989b5c282bd4c01764`). The subsequent engine run `42959017293` passed. After dispatcher schema/policy tests were added, [Engine Contract Tests run 42959145056](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42959145056) passed, and [Phase 04 Sandbox Security Tests run 42959145125](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42959145125) passed both `engine-policy` and `sandbox-policy`. The Phase 00 run `42959145140` had API and worker tests passing while its frontend baseline job was still running at report update time. [Phase 04 Sandbox Security Tests run 42959465073](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42959465073) passed both engine-policy and sandbox-policy after the durable memory changes. [Phase 00 run 42959465066](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42959465066) has API and worker tests passing; the frontend baseline job (lint/build/browser smoke) was still in progress at the time of this report update. These results validate the current automated suites only, not full Phase 04 acceptance.

## Safety and release

- No Supabase migration or production data mutation was made.
- No LLM provider secret was added.
- No sandbox/high-risk tool was enabled.
- No worker activation, deployment or release was performed.
- No Customer/Mitra UI changes were made.
- Phase 04 sign-off is withheld until runtime/tool/flow/memory parity, security and recovery evidence pass.
