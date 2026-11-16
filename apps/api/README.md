# MoreAI FastAPI

FastAPI is the only business-data and AI execution boundary. The browser may use Supabase directly for Auth only; all application data, conversations, runs, events, tools, model calls, credits and partner workflows go through this API.

## Environment
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY` (or legacy `SUPABASE_ANON_KEY`) for validating user access tokens
- `SUPABASE_SERVICE_ROLE_KEY` server-only for the privileged repository adapter. It must never be exposed to the web app, logs, CI artifacts or source.

## Customer and Partner API origins
The browser API client supports optional `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL` and `NEXT_PUBLIC_MOREAI_PARTNER_API_URL`. If unset, both use `NEXT_PUBLIC_MOREAI_API_URL` and remain separated by the server-enforced `/api/v1/customer/*` and `/api/v1/partner/*` namespaces. If distinct origins are configured, set `MOREAI_CORS_ALLOWED_ORIGINS` to the exact frontend origin(s), comma-separated. Never put server secrets in `NEXT_PUBLIC_*` variables.

## Run
```bash
cd apps/api
python -m venv .venv && . .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload --port 8000
```

OpenAPI: `/openapi.json`.

Current implemented domain endpoints:
- `POST/GET /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}`
- `POST /api/v1/conversations/{conversation_id}/messages` (idempotent durable run enqueue)
- `GET /api/v1/agent-runs`
- `GET /api/v1/agent-runs/{run_id}`
- `POST /api/v1/agent-runs/{run_id}/cancel`
- `GET /api/v1/agent-runs/{run_id}/events`
- `GET /api/v1/agent-runs/{run_id}/stream`

Privileged REST operations are explicitly scoped to authenticated `user_id` / ownership. The existing database policies deny client access to conversations and agent-runs; therefore no browser database CRUD is used. Production access requires the server-only service role and explicit backend authorization checks.


## Pinned Skill source ingestion

The Customer Skill Registry fetches pinned public source repositories through GitHub's REST API. For high-volume ingestion, configure an optional fine-grained GitHub token with read-only access to public repositories as the server-only environment variable `MOREAI_GITHUB_TOKEN` on the API service. The value is read by `Settings.from_env()` and attached only to backend GitHub API requests. It must not be added to `NEXT_PUBLIC_*`, browser runtime, app logs or repository files.

For Docker Compose deployments, `docker-compose.runtime.yml` forwards `MOREAI_GITHUB_TOKEN` from the host environment to the API container. Vercel-hosted FastAPI deployments must set the same variable in the protected server environment configuration. Without a token, public GitHub API limits may interrupt a large batch; rate-limited responses are returned as HTTP 503 with a `Retry-After` header. Resume the Customer Skill batch after the retry window; completed `validated` and `review_required` packages are skipped.

The token grants source-reading capability only. It does not publish, install, approve or execute imported Skills. Keep it scoped to read-only public repository content and rotate it through the host's secret manager.
