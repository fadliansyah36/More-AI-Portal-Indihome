# MoreAI Worker Boundary

The worker uses a durable Supabase run lifecycle and a fail-closed agent registry. It must run as an always-on container service; it is not an HTTP request worker and must not be deployed as a short-lived serverless function.

Implemented runtime adapters:
- Supabase RPC: claim, heartbeat, checkpoint, finish and cancel.
- Durable planning steps in `agent_run_steps` plus checkpoint manifest.
- Manus text runtime and Planning runtime, both routed through the metered LLM gateway.
- DB-driven model routing across platform, user, workspace and partner scopes.
- LLM request idempotency, credit reservation, provider usage recording and settlement RPCs.
- Provider stream deltas are persisted as per-run checkpoints and exposed by FastAPI SSE.

The registry includes the durable `manus`, `planning` and `toolcall` runtimes. The SWE runtime and Bash/Python tools remain behind the isolated execution-supervisor and release gates. The OpenFuse Browser tool is registered only when its private persistent browser worker, worker token, egress attestation and authenticated FastAPI boundary are configured and ready. Workspace editing remains owner-scoped through the canonical Supabase workspace service.

## Health and deployment contract

- `GET /health` is the process liveness endpoint and returns `200` while the HTTP health listener is alive.
- `GET /ready` returns `503` until startup configuration gates have passed, the durable event-outbox publisher is running, and a worker capability heartbeat has been successfully published; it returns `200` only while the latest capability publication is healthy. The capability heartbeat runs independently of long Agent Runs. Readiness is not proof that a live provider request or end-to-end Agent Run has succeeded.
- Container platforms should use `/ready` as the readiness/health check on port `8081`, keep the service running continuously (no scale-to-zero), and restart it when the process exits or the readiness check remains unhealthy.
- The worker requires a persistent container host with secret injection and outbound HTTPS to the canonical Supabase project and approved provider endpoints. Vercel Functions are not the worker runtime.
- Do not expose the worker health port as a public business API. Restrict it to the container platform's health-check network where supported.

## Runtime configuration

Required server-only environment:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `WORKER_ID` (8–128 characters)
- `MOREAI_AGENT_RUNTIME_ENABLED=true` (off by default)
- `MOREAI_CREDITS_PER_USD` (business-approved credit conversion; no default is assumed)
- `MOREAI_CREDIT_WALLET_CURRENCY` (canonical wallet currency key)
- Provider secret environment variables named by the DB provider config, each beginning `MOREAI_PROVIDER_`

Enabled `chat` and `planning` routing policies must both resolve to an enabled model and provider. The worker startup gate also requires at least one configured provider secret environment variable for each task type. Each selected model must have an HTTPS base URL, secret environment reference, input/output pricing and max output token limit. This check validates metadata and secret presence only; it does not make live provider calls.

The Super Admin provider form stores only the provider HTTPS base URL and a `MOREAI_PROVIDER_*` environment-variable name in the canonical database. The actual API key value must be added to the persistent worker host secret manager using that exact variable name. The provider stays disabled until an authorized readiness/activation process is completed.

Current provider adapter coverage is OpenAI-compatible chat completions for OpenAI and Google's OpenAI-compatible endpoint. Anthropic's native Messages protocol is not implemented by this adapter and must not be configured as an Anthropic provider until its dedicated adapter is delivered; the Admin API and endpoint allowlist intentionally exclude it.

Do not enable the worker or set `MOREAI_AGENT_EXECUTION_ENABLED=true` in the API until provider routes, secrets, wallet funding, credit conversion, quota/entitlement resolution and worker health checks have been validated.

## Run locally

```bash
cd apps/worker
PYTHONPATH=../.. python -m app.main
```

Service-role credentials must remain in the worker's secret store and must never enter the web app, source code, logs or build artifacts.


## OpenFuse persistent browser adapter

The optional browser adapter targets the pinned OpenFuse browser-worker HTTP contract (the worker API in `CopilotKit/openfuse`): `GET /health`, authenticated `GET /sessions`, `POST /sessions`, and per-session `navigate`, `read`, `screenshot`, `input`, `close`, and `downloads` endpoints. It does not use a private, invented `/v1/browser/actions` endpoint.

Configure these server-only variables on the persistent worker host:
- `MOREAI_BROWSER_ENABLED=true`
- `MOREAI_BROWSER_SERVICE_URL` (for example the private service URL `http://openfuse-browser:8790`)
- `MOREAI_BROWSER_SERVICE_TOKEN` (same 32+ character `WORKER_TOKEN` configured on OpenFuse's browser worker)
- `MOREAI_BROWSER_EGRESS_ENFORCED=true` (explicit deployment attestation; OpenFuse worker enforces public HTTP(S) destination checks and its egress proxy)
- `MOREAI_BROWSER_PRIVATE_NETWORK_HTTP=true` only for the exact private Compose/Render worker host and port
- `MOREAI_INTERNAL_API_URL` (private FastAPI origin, default `http://api:8000`)
- `MOREAI_WORKER_INTERNAL_TOKEN` (32+ character worker-to-FastAPI credential)

OpenFuse browser profiles live on its persistent browser-worker data volume. Do not deploy the browser worker without a persistent volume and its restricted private network. The worker validates the actual OpenFuse `/health` and authenticated `/sessions` response before advertising browser capability.

Supported MoreAI browser actions are `navigate`, `extract` (visible text read), `input` (bounded click/text/key/scroll), `screenshot` (stored as a private owner/run-scoped PNG artifact), `close`, and `downloads` metadata. Every action uses the existing durable owner-approval gate and a run/tool-call-bound action receipt. An ambiguous supervisor outcome is recorded as `unknown` and is never automatically replayed. Customer close requests are reconciled by the worker and acknowledged only after the OpenFuse session is closed.

Downloaded PDF metadata and failure receipts can be inspected, but file bytes are not imported into customer Files until a real malware scanner is integrated. OpenFuse's optional Linux computer/E2B graphical desktop is not activated by this browser adapter; MoreAI's existing isolated bash/Python workspace remains a separate execution boundary. No desktop/VNC or host shell access is exposed to the customer.

This is source integration only. A connected persistent host, real service token, persistent profile volume and live worker heartbeat are still required before operational readiness. Do not claim the browser runtime is active merely because the adapter is present in source.


## Computer Workspace execution receipts

Bash and Python execution remain behind the isolated, network-disabled execution supervisor. The worker propagates the OpenManus tool-call ID, claims an owner/run/workspace-bound Computer action receipt through FastAPI, and derives a stable supervisor request ID. Successful results are stored as bounded receipt payloads for 30 days; ambiguous supervisor outcomes are marked `unknown` and are not automatically replayed. Customer Profile Settings exposes the persisted action history without exposing command source or secrets.

Workspace files are persisted through the canonical Supabase Workspace service and rehydrated into a disposable execution container for each command. This is not a persistent Linux desktop/container, VNC session or OpenFuse E2B Computer. The OpenFuse optional Docker/E2B Computer server must not be mounted directly into the multi-tenant MoreAI API: its current shared access-key/single-owner server model and separate Store are not a drop-in tenant boundary. A dedicated MoreAI per-customer isolated supervisor would be required for persistent desktop parity.
