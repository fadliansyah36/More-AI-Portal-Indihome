from __future__ import annotations

import asyncio
import os

import httpx

from app.client import WorkerRpcClient, WorkerSettings
from app.dispatcher import RegisteredAgentDispatcher
from app.registry_factory import build_agent_registry
from app.runtime import WorkerRuntime


async def run_worker() -> None:
    if os.getenv("MOREAI_AGENT_RUNTIME_ENABLED", "false").lower() != "true":
        raise RuntimeError("worker_runtime_disabled_until_release_gate")
    settings = WorkerSettings(
        supabase_url=os.environ["SUPABASE_URL"],
        service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        worker_id=os.getenv("WORKER_ID", "moreai-worker-main-01"),
        lease_seconds=int(os.getenv("WORKER_LEASE_SECONDS", "90")),
    )
    if not os.getenv("MOREAI_CREDITS_PER_USD") or not os.getenv("MOREAI_CREDIT_WALLET_CURRENCY"):
        raise RuntimeError("credit_estimator_and_wallet_currency_must_be_configured")

    async with httpx.AsyncClient() as http:
        rpc = WorkerRpcClient(settings, http)
        # Do not claim work unless at least one route has been explicitly configured.
        routes = await rpc.select("llm_routing_policies", {
            "enabled": "eq.true", "select": "id,task_type", "limit": "1",
        })
        if not routes:
            raise RuntimeError("no_enabled_llm_routing_policy")
        registry = build_agent_registry(rpc, http)
        runtime = WorkerRuntime(rpc, RegisteredAgentDispatcher(registry))
        poll_seconds = max(1, min(30, int(os.getenv("WORKER_POLL_SECONDS", "3"))))
        while True:
            processed = await runtime.run_once()
            if not processed:
                await asyncio.sleep(poll_seconds)


if __name__ == "__main__":
    asyncio.run(run_worker())
