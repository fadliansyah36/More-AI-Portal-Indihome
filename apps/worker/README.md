# MoreAI Worker Boundary

This package now contains a server-only RPC adapter for the canonical durable run lifecycle:
- `moreai_worker_claim_run`
- `moreai_worker_heartbeat`
- `moreai_worker_checkpoint`
- `moreai_worker_finish_run`

Run tests:

```bash
cd apps/worker
python -m venv .venv && . .venv/bin/activate
pip install -e '.[test]'
pytest
```

Required environment when deployed: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and a unique `WORKER_ID` (8–128 chars). The service-role key must exist only in the worker's secret store and must never be copied into frontend environment variables, logs or repository files.

**Execution remains disabled until a reviewed production `AgentDispatcher` has been implemented and registered.** The lifecycle adapter does not pretend that upstream agents/tools have been ported. Never claim jobs with a placeholder dispatcher.
