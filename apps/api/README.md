# MoreAI FastAPI

FastAPI is the only business-data and AI execution boundary. The browser may use Supabase directly for Auth only; all application data, conversations, runs, events, tools, model calls, credits and partner workflows go through this API.

## Environment
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY` (or legacy `SUPABASE_ANON_KEY`) for validating user access tokens
- `SUPABASE_SERVICE_ROLE_KEY` server-only for the privileged repository adapter. It must never be exposed to the web app, logs, CI artifacts or source.

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
