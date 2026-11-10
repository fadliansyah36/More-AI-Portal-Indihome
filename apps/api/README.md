# MoreAI FastAPI Boundary

Run locally:

```bash
cd apps/api
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --host 0.0.0.0 --port 8000
pytest
```

Configuration:
- `SUPABASE_URL`: canonical MoreAI Supabase project URL.
- `SUPABASE_ANON_KEY`: publishable/anon key used server-side for Auth and user-scoped PostgREST requests. It is not a service-role secret.

Implemented:
- `GET /health`, `GET /ready`.
- `GET /v1/me`: validates the bearer token through Supabase Auth, then reads the caller's profile with the same user JWT so existing RLS applies.
- Correlation IDs and generic unhandled-error responses.

Security boundary:
- No service-role key or LLM provider key is used.
- No browser-supplied role/workspace claim is trusted.
- The schema denies direct client access to agent runs, messages, tools, billing and LLM configuration. Those server-only domains remain unavailable through this API until explicit server-side authorization and audited privileged data access are implemented.
- This increment does not claim OpenManusWeb runtime parity or production readiness.
