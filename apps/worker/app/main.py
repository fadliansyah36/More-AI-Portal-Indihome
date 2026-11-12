from __future__ import annotations

import asyncio
import json
import logging
import os

import httpx

from app.client import WorkerRpcClient, WorkerSettings
from app.dispatcher import RegisteredAgentDispatcher
from app.registry_factory import build_agent_registry
from app.runtime import WorkerRuntime
from app.outbox import DurableEventOutboxPublisher
from app.knowledge_tools import SupabaseKnowledgeTools
from apps.sandbox.app.browser_supervisor import BrowserSupervisor


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

logger = logging.getLogger(__name__)


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
        if os.getenv("MOREAI_BROWSER_ENABLED", "false").lower() == "true":
            browser_client = BrowserSupervisor(
                service_url=os.getenv("MOREAI_BROWSER_SERVICE_URL", ""),
                service_token=os.getenv("MOREAI_BROWSER_SERVICE_TOKEN", ""),
                egress_enforced=os.getenv("MOREAI_BROWSER_EGRESS_ENFORCED", "false").lower() == "true",
                allow_private_http=os.getenv("MOREAI_BROWSER_PRIVATE_NETWORK_HTTP", "false").lower() == "true",
                http=http,
            )
            await browser_client.check_ready()
        registry = build_agent_registry(rpc, http)
        runtime = WorkerRuntime(rpc, RegisteredAgentDispatcher(registry, checkpoint_loader=rpc.list_checkpoints))
        knowledge_ingestion = SupabaseKnowledgeTools(rpc, http)
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
                # A transient Supabase/PostgREST failure while claiming the next run
                # must not terminate the long-lived worker process. Startup remains
                # fail-fast (credentials, routes, quota and registry are validated
                # above); only the steady-state claim/poll loop uses bounded backoff.
                consecutive_poll_failures = 0
                while True:
                    try:
                        processed = await runtime.run_once()
                        if not processed:
                            ingestion_job = await rpc.claim_knowledge_ingestion()
                            if ingestion_job:
                                document_id = str(ingestion_job["id"])
                                owner_id = str(ingestion_job["owner_user_id"])
                                lease_until = str(ingestion_job.get("ingestion_lease_until") or "")
                                lease_lost = asyncio.Event()
                                async def heartbeat() -> None:
                                    nonlocal lease_until
                                    while True:
                                        await asyncio.sleep(45)
                                        try:
                                            renewed = await rpc.heartbeat_knowledge_ingestion(
                                                document_id, owner_id, lease_until, lease_seconds=900,
                                            )
                                        except asyncio.CancelledError:
                                            raise
                                        except Exception:
                                            logger.exception("knowledge_ingestion_heartbeat_error document_id=%s", document_id)
                                            # A transient heartbeat error is retried once before fail-closed cancellation.
                                            await asyncio.sleep(5)
                                            renewed = await rpc.heartbeat_knowledge_ingestion(
                                                document_id, owner_id, lease_until, lease_seconds=900,
                                            )
                                        except Exception:
                                            lease_lost.set()
                                            logger.exception("knowledge_ingestion_heartbeat_unavailable document_id=%s", document_id)
                                            return
                                        if not renewed:
                                            lease_lost.set()
                                            logger.warning("knowledge_ingestion_lease_lost document_id=%s", document_id)
                                            return
                                        lease_until = renewed

                                processing_task = asyncio.create_task(
                                    knowledge_ingestion.process_uploaded_document(ingestion_job),
                                    name=f"knowledge-ingestion-{document_id}",
                                )
                                heartbeat_task = asyncio.create_task(
                                    heartbeat(), name=f"knowledge-heartbeat-{document_id}",
                                )
                                try:
                                    done, _ = await asyncio.wait(
                                        {processing_task, heartbeat_task},
                                        return_when=asyncio.FIRST_COMPLETED,
                                    )
                                    if heartbeat_task in done and lease_lost.is_set():
                                        processing_task.cancel()
                                        await asyncio.gather(processing_task, return_exceptions=True)
                                    else:
                                        extracted_page_count = await processing_task
                                        finished = await rpc.finish_knowledge_ingestion(
                                            document_id, owner_id, True,
                                            page_count=extracted_page_count,
                                        )
                                        if not finished:
                                            logger.warning("knowledge_ingestion_finish_fenced document_id=%s", document_id)
                                except asyncio.CancelledError:
                                    processing_task.cancel()
                                    raise
                                except Exception as ingestion_error:
                                    attempt = int(ingestion_job.get("ingestion_attempt") or 1)
                                    code = type(ingestion_error).__name__.lower()[:80] or "knowledge_ingestion_failed"
                                    if not lease_lost.is_set():
                                        await rpc.finish_knowledge_ingestion(
                                            document_id, owner_id, False, error_code=code,
                                        )
                                    logger.exception("knowledge_ingestion_failed document_id=%s attempt=%s", document_id, attempt)
                                finally:
                                    heartbeat_task.cancel()
                                    await asyncio.gather(heartbeat_task, return_exceptions=True)
                                processed = True
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        consecutive_poll_failures = min(consecutive_poll_failures + 1, 5)
                        logger.exception("worker_run_poll_failed")
                        delay = min(30.0, poll_seconds * (2 ** (consecutive_poll_failures - 1)))
                        await asyncio.sleep(delay)
                        continue

                    if processed:
                        consecutive_poll_failures = 0
                        continue

                    consecutive_poll_failures = 0
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
