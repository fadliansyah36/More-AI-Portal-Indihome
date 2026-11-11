# Phase 04 / 08 / 09 Integration Continuation — 2026-11-11

## Scope
This increment connects the OpenManus structured tool-call cycle to the existing durable worker and Supabase checkpoint RPC. It deliberately does not enable production worker execution or claim real-provider E2E acceptance.

## Phase 04
- Added `DurableOpenManusRuntime`, a bounded multi-round tool-call loop hosted behind the existing `RegisteredAgentDispatcher` and durable `WorkerRuntime`.
- Each model round writes requested/response checkpoints. Each tool call writes an intent checkpoint and a settled observation checkpoint.
- Tool exposure is derived from the policy-enforced registry. Only a worker-registered handler is exposed. Bash, Python, browser, editor and process tools remain unavailable/default-denied until approval and isolated supervisor wiring is configured.
- Durable worker lease, heartbeat, cancellation, checkpoint and finish remain the canonical lifecycle and Supabase RPC path.

## Phase 08
- Model requests carry structured tool definitions to the OpenAI-compatible adapter.
- Provider tool calls are normalized into the OpenAI-compatible `tool_calls` shape and passed back to the runtime.
- Each model round has a deterministic request key; the existing metered gateway claims, reserves, records and settles each round independently. Nested completion tool calls use a separate deterministic key.
- Provider failover/retry remains constrained by configured routing policy and is not represented as complete until candidate-route retry is implemented and provider response accounting is verified. No provider credentials or live calls were used in this increment.

## Phase 09
- Existing browser Supabase client remains Auth/session-only; business operations remain FastAPI-mediated.
- Customer/Mitra route split and server-verified role boundary remain open. The current single-page role switcher is not an access-control boundary and must not be treated as one.
- Do not expose Mitra navigation from Customer routes; enforce partner membership and tenant scope in FastAPI before enabling Mitra routes.

## Phase 10–11 release status
- Real provider/API-key E2E intentionally deferred per product-owner instruction.
- No production worker activation, deployment, or release-gate pass is authorized by this increment.
- Required before acceptance: provider candidate failover/retry, full partner route guards, sandbox supervisor integration, and authenticated integration evidence (can be a later controlled test window).

## Operational rule
Keep `MOREAI_AGENT_RUNTIME_ENABLED=false` until Phase 11 is explicitly accepted. Do not enable high-risk tools by environment toggle alone.
