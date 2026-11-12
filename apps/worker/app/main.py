from __future__ import annotations

import asyncio
import json
import os

import httpx

from app.client import WorkerRpcClient, WorkerSettings
from app.dispatcher import RegisteredAgentDispatcher
from app.registry_factory import build_agent_registry
from app.runtime import WorkerRuntime
from app.outbox import DurableEventOutboxPublisher


async def _health_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=2.0)
        parts = request_line.decode('ascii', 'ignore').split(' ')
        path = parts[1] if len(parts) > 1 else '/'
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=2.0)
            if line in (b'\r\n', b'\n', b''):
                break
        ok = path in {'/health', '/ready'}
        body = json.dumps({'status': 'ok' if ok else 'not_found', 'service': 'moreai-worker'}).encode()
        status = '200 OK' if ok else '404 Not Found'
        headers = (f'HTTP/1.1 {status}\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n').encode()
        writer.write(headers + body)
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

async def run_worker() -> None:
    if os.getenv("MOREAI_AGENT_RUNTIME_ENABLED", "false").lower() != "true":
        raise RuntimeError("worker_runtime_disabled_until_release_gate")
    settings = WorkerSettings(
        supabase_url=os.environ["SUPABASE_URL"],
        service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        worker_id=os.getenv("WORKER_ID", "moreai-worker-main-01"),
        lease_seconds=int(os.getenv("WORKER_LEASE_SECONDS", "90")),
        run_timeout_seconds=int(os.getenv("MOREAI_RUN_TIMEOUT_SECONDS", "1800")),
    )
    required_billing = (
        "MOREAI_CREDITS_PER_USD",
        "MOREAI_CREDIT_WALLET_CURRENCY",
        "MOREAI_LLM_ENTITLEMENT_KEY",
        "MOREAI_LLM_QUOTA_METRIC_KEY",
    )
    missing_billing = [key for key in required_billing if not os.getenv(key)]
    if missing_billing:
        raise RuntimeError("llm_entitlement_quota_and_credit_configuration_missing")

    async with httpx.AsyncClient() as http:
        rpc = WorkerRpcClient(settings, http)
        # Do not claim work unless at least one route has been explicitly configured.
        routes = await rpc.select("llm_routing_policies", {
            "enabled": "eq.true", "select": "id,task_type", "limit": "1",
        })
        if not routes:
            raise RuntimeError("no_enabled_llm_routing_policy")
        quota_policies = await rpc.select("quota_policies", {
            "enabled": "eq.true",
            "metric_key": f"eq.{os.environ['MOREAI_LLM_QUOTA_METRIC_KEY']}",
            "select": "id",
            "limit": "1",
        })
        if not quota_policies:
            raise RuntimeError("no_enabled_llm_quota_policy")
        registry = build_agent_registry(rpc, http)
        runtime = WorkerRuntime(rpc, RegisteredAgentDispatcher(registry, checkpoint_loader=rpc.list_checkpoints))
        health_server = await asyncio.start_server(
            _health_handler,
            host=os.getenv("WORKER_HEALTH_HOST", "0.0.0.0"),
            port=int(os.getenv("WORKER_HEALTH_PORT", "8081")),
        )
        async with health_server:
            stop_outbox = asyncio.Event()
            publisher = DurableEventOutboxPublisher(
                rpc, poll_seconds=float(os.getenv("WORKER_OUTBOX_POLL_SECONDS", "1")),
            )
            outbox_task = asyncio.create_task(publisher.run(stop_outbox), name="moreai-event-outbox")
            poll_seconds = max(1, min(30, int(os.getenv("WORKER_POLL_SECONDS", "3"))))
            try:
                while True:
                    processed = await runtime.run_once()
                    if not processed:
                        await asyncio.sleep(poll_seconds)
            finally:
                stop_outbox.set()
                outbox_task.cancel()
                try:
                    await outbox_task
                except asyncio.CancelledError:
                    pass


if __name__ == "__main__":
    asyncio.run(run_worker())
