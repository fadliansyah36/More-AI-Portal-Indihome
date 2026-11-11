# Frontend ↔ OpenManus Integration Continuation — 2026-11-11

## Execution constraints
- Canonical repository: fadliansyah36/More-AI-Portal-Indihome.
- Target branch: main only; do not create a branch.
- Deployment quota and production deployment are deferred by the product owner.
- The owner explicitly requested that real/live testing be skipped for this implementation increment. Do not run production calls, paid provider calls, browser E2E, migrations, or runtime activation.
- Preserve the existing Customer and Partner UI. Do not import or mount OpenManusWeb frontend code.
- Never claim tests, deployment, or production behavior that were not run.

## Current integration seams inspected
- Customer chat creates a durable conversation through `POST /api/v1/customer/conversations`, enqueues a run through `POST /api/v1/customer/conversations/{id}/messages`, and consumes persisted worker events through the Customer SSE endpoint.
- The worker dispatches the `manus` and `planning` agent keys through `RegisteredAgentDispatcher` and `build_agent_registry`.
- The Manus runtime uses the metered gateway, durable checkpoints, Supabase-backed conversation memory and a policy-enforced tool registry.
- The API client already separates Customer and Partner API origins and attaches the Supabase access token server-side at the API boundary.
- Agent Studio reads the enabled agent catalog; ChatView uses the durable Customer conversation/run APIs and SSE stream.
- Files currently reads owner-scoped artifact metadata only. It explicitly does not claim download capability.

## Verified gaps from source inspection
1. OpenManus backend behavioral parity is still partial. The capability map records pending/partial upstream flow lifecycle, server/session/WebSocket compatibility, tool handlers, structured logging, log parsing, artifact storage, search provider, workspace editor, and SWE runtime.
2. Browser automation remains default-deny because browser route/subresource interception and socket-level egress enforcement are not deployed. URL validation helpers alone are not a browser security boundary.
3. Bash/Python adapters remain release-gated; source registration is not production activation.
4. Phase 09 is partial. Customer and Partner screens outside the already-connected domains still need typed API contracts and real persistence. No fabricated fallback data may be introduced.
5. The live Supabase Storage inventory inspected for this continuation returned no configured buckets. Artifact download must remain unavailable until a canonical bucket and object-path convention are provisioned and reconciled with the artifact table.
6. Service-role credentials, provider secrets, worker deployment, and Vercel quota are intentionally not supplied/activated in this increment.

## Implementation order
### Track A — OpenManus runtime parity
- Complete source-to-target capability mapping for agent, flow, LLM, tool and upstream server contracts.
- Port remaining safe backend domain/runtime contracts into `engine/` and `apps/api/`; keep `vendor/openmanusweb/` pristine.
- Connect all tools only through the central policy-enforced registry and durable worker dispatcher.
- Keep tools without a real isolated adapter disabled/default-deny.
- Complete durable run events, cancellation, retries, timeout and recovery semantics before widening tool availability.

### Track B — Existing frontend integration
- Keep existing route/component hierarchy and design intact.
- Inventory every screen's current data source and map it to a typed FastAPI endpoint.
- Add missing Pydantic contracts and server-side authorization before binding UI.
- Replace mock/static/demo data only when the corresponding API and persistence contract exists; otherwise show an explicit unavailable/empty state.
- Bind Customer, Partner and Super Admin separately to their authorized API namespaces.
- Add artifact download only after the Storage bucket/path contract exists.

### Track C — Documentation and release boundaries
- Update `docs/implementation/openmanus-backend-capability-map.json` as each capability is implemented.
- Update `docs/implementation/PHASE-TRACKER.md` and the dated continuation report after each implementation increment.
- Record skipped tests explicitly. This increment has no new test/build/browser evidence.
- Keep Phase 10 and Phase 11 open until the product owner authorizes the corresponding verification and deployment work.

## Acceptance rule
A screen is integrated only when it reads/writes through a typed FastAPI contract, the server enforces owner/tenant/role scope, persistence is canonical in Supabase, and the UI has no fabricated success/data path. A tool is integrated only when the upstream capability is mapped to a real adapter, policy and approval are enforced, execution is durable, and its security boundary is real. Catalog presence or source-copy presence alone is not acceptance.
