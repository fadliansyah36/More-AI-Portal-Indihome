# MoreAI Worker Boundary

The worker uses a durable Supabase run lifecycle and a fail-closed agent registry.

Implemented runtime adapters:
- Supabase RPC: claim, heartbeat, checkpoint, finish and cancel.
- Durable planning steps in `agent_run_steps` plus checkpoint manifest.
- Manus text runtime and Planning runtime, both routed through the metered LLM gateway.
- DB-driven model routing across platform, user, workspace and partner scopes.
- LLM request idempotency, credit reservation, provider usage recording and settlement RPCs.
- Provider stream deltas are persisted as per-run checkpoints and exposed by FastAPI SSE.

The worker registers only `manus` and `planning`. SWE, Bash, Python execution, browser automation, process execution and workspace editing remain blocked until their required isolated sandboxes are deployed and reviewed.

## Runtime configuration

Required server-only environment:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `WORKER_ID` (8–128 characters)
- `MOREAI_AGENT_RUNTIME_ENABLED=true` (off by default)
- `MOREAI_CREDITS_PER_USD` (business-approved credit conversion; no default is assumed)
- `MOREAI_CREDIT_WALLET_CURRENCY` (canonical wallet currency key)
- Provider secret environment variables named by the DB provider config, each beginning `MOREAI_PROVIDER_`

At least one enabled LLM routing policy must exist. Each selected model must have an enabled provider, HTTPS base URL, secret environment reference, input/output pricing and max output token limit.

Do not enable the worker or set `MOREAI_AGENT_EXECUTION_ENABLED=true` in the API until provider routes, secrets, wallet funding, credit conversion, quota/entitlement resolution and worker health checks have been validated.

## Run locally

```bash
cd apps/worker
PYTHONPATH=../.. python -m app.main
```

Service-role credentials must remain in the worker's secret store and must never enter the web app, source code, logs or build artifacts.
