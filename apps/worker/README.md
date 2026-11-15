# MoreAI Worker Boundary

The worker uses a durable Supabase run lifecycle and a fail-closed agent registry. It must run as an always-on container service; it is not an HTTP request worker and must not be deployed as a short-lived serverless function.

Implemented runtime adapters:
- Supabase RPC: claim, heartbeat, checkpoint, finish and cancel.
- Durable planning steps in `agent_run_steps` plus checkpoint manifest.
- Manus text runtime and Planning runtime, both routed through the metered LLM gateway.
- DB-driven model routing across platform, user, workspace and partner scopes.
- LLM request idempotency, credit reservation, provider usage recording and settlement RPCs.
- Provider stream deltas are persisted as per-run checkpoints and exposed by FastAPI SSE.

The worker registers only `manus` and `planning`. SWE, Bash, Python execution, browser automation, process execution and workspace editing remain blocked until their required isolated sandboxes are deployed and reviewed.

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

Do not enable the worker or set `MOREAI_AGENT_EXECUTION_ENABLED=true` in the API until provider routes, secrets, wallet funding, credit conversion, quota/entitlement resolution and worker health checks have been validated.

## Run locally

```bash
cd apps/worker
PYTHONPATH=../.. python -m app.main
```

Service-role credentials must remain in the worker's secret store and must never enter the web app, source code, logs or build artifacts.
