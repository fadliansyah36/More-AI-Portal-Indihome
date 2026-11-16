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
from app.sandbox_tools import IsolatedSandboxToolAdapter
from app.llm_gateway import provider_readiness_snapshot
from apps.sandbox.app.browser_supervisor import BrowserSupervisor


async def _health_handler(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
    readiness: dict[str, bool],
) -> None:
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=2.0)
        parts = request_line.decode('ascii', 'ignore').split(' ')
        path = parts[1] if len(parts) > 1 else '/'
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=2.0)
            if line in (b'\r\n', b'\n', b''):
                break
        if path == '/health':
            status_code, status_text, state = 200, 'OK', 'alive'
        elif path == '/ready' and readiness.get('ready') is True:
            status_code, status_text, state = 200, 'OK', 'ready'
        elif path == '/ready':
            status_code, status_text, state = 503, 'Service Unavailable', 'not_ready'
        else:
            status_code, status_text, state = 404, 'Not Found', 'not_found'
        body = json.dumps({'status': state, 'service': 'moreai-worker'}).encode()
        status = f'{status_code} {status_text}'
        headers = (f'HTTP/1.1 {status}\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n').encode()
        writer.write(headers + body)
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

logger = logging.getLogger(__name__)


async def _capability_heartbeat_loop(
    rpc: WorkerRpcClient,
    runtime_keys: list[str],
    capability_snapshot: dict[str, object],
    readiness: dict[str, bool],
) -> None:
    interval = max(10, min(120, int(os.getenv("WORKER_CAPABILITY_HEARTBEAT_SECONDS", "30"))))
    while True:
        try:
            await rpc.publish_capabilities(runtime_keys, capability_snapshot)
            readiness["ready"] = True
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            readiness["ready"] = False
            raise
        except Exception:
            readiness["ready"] = False
            logger.exception("worker_capability_heartbeat_failed")
            await asyncio.sleep(min(interval, 10))


async def _browser_session_close_reconciliation_loop(
    browser: BrowserSupervisor,
    http: httpx.AsyncClient,
    api_url: str,
    internal_token: str,
    stop: asyncio.Event,
) -> None:
    """Close customer-requested OpenFuse sessions and acknowledge durable completion."""
    headers = {"X-MoreAI-Worker-Token": internal_token}
    while not stop.is_set():
        try:
            expiry_response = await http.get(
                f"{api_url.rstrip('/')}/api/v1/customer/browser-sessions/internal/expire-requests",
                headers=headers, timeout=httpx.Timeout(12.0, connect=3.0),
            )
            expiry_response.raise_for_status()
            expiry_payload = expiry_response.json()
            if not isinstance(expiry_payload, dict) or not isinstance(expiry_payload.get("items"), list):
                raise RuntimeError("browser_session_expiry_requests_contract_invalid")
            response = await http.get(
                f"{api_url.rstrip('/')}/api/v1/customer/browser-sessions/internal/close-requests",
                headers=headers, timeout=httpx.Timeout(12.0, connect=3.0),
            )
            response.raise_for_status()
            payload = response.json()
            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                raise RuntimeError("browser_session_close_requests_contract_invalid")
            for item in items:
                if not isinstance(item, dict):
                    continue
                session_id, user_id = item.get("session_id"), item.get("user_id")
                if not isinstance(session_id, str) or not isinstance(user_id, str):
                    continue
                try:
                    await browser.close_session(session_id)
                    completed = await http.post(
                        f"{api_url.rstrip('/')}/api/v1/customer/browser-sessions/internal/{session_id}/close-complete",
                        json={"user_id": user_id},
                        headers=headers, timeout=httpx.Timeout(12.0, connect=3.0),
                    )
                    completed.raise_for_status()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("browser_session_close_reconciliation_failed session_id=%s", session_id)
            # Closed profiles are retained for 30 days. Delete only after FastAPI
            # confirms the canonical retention deadline and ownership.
            try:
                retention = await http.get(
                    f"{api_url.rstrip('/')}/api/v1/customer/browser-sessions/internal/profile-cleanup-requests",
                    headers=headers, timeout=httpx.Timeout(12.0, connect=3.0),
                )
                retention.raise_for_status()
                retention_payload = retention.json()
                candidates = retention_payload.get("items") if isinstance(retention_payload, dict) else None
                if not isinstance(candidates, list):
                    raise RuntimeError("browser_profile_retention_requests_contract_invalid")
                for candidate in candidates:
                    if not isinstance(candidate, dict):
                        continue
                    profile_id, owner_id = candidate.get("session_id"), candidate.get("user_id")
                    if not isinstance(profile_id, str) or not isinstance(owner_id, str):
                        continue
                    try:
                        await browser.delete_profile(profile_id)
                        acknowledged = await http.post(
                            f"{api_url.rstrip('/')}/api/v1/customer/browser-sessions/internal/{profile_id}/profile-deleted",
                            json={"user_id": owner_id},
                            headers=headers, timeout=httpx.Timeout(12.0, connect=3.0),
                        )
                        acknowledged.raise_for_status()
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        logger.exception("browser_profile_retention_delete_failed profile_id=%s", profile_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("browser_profile_retention_reconciliation_unavailable")

            # Orphan cleanup uses a complete canonical ownership snapshot. If
            # count, pagination, or any API call is incomplete, deletion is skipped.
            try:
                ownership = await http.get(
                    f"{api_url.rstrip('/')}/api/v1/customer/browser-sessions/internal/owned-profile-ids",
                    headers=headers, timeout=httpx.Timeout(12.0, connect=3.0),
                )
                ownership.raise_for_status()
                owner_payload = ownership.json()
                owned = owner_payload.get("items") if isinstance(owner_payload, dict) else None
                if (
                    not isinstance(owned, list)
                    or owner_payload.get("complete") is not True
                    or owner_payload.get("total") != len(owned)
                    or any(not isinstance(value, str) for value in owned)
                    or len(set(owned)) != len(owned)
                ):
                    raise RuntimeError("browser_profile_ownership_inventory_incomplete")
                profiles = await browser.list_profiles()
                owned_set = set(owned)
                for profile in profiles:
                    profile_id = profile["id"]
                    if profile_id not in owned_set:
                        try:
                            await browser.delete_profile(profile_id)
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            logger.exception("browser_orphan_profile_cleanup_failed profile_id=%s", profile_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("browser_orphan_profile_reconciliation_unavailable")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("browser_session_close_requests_poll_failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=15.0)
        except TimeoutError:
            pass


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
        # Both primary runtime paths must resolve to enabled models/providers
        # and have their secret references injected in this worker process.
        # This is metadata validation only; no external provider call is made.
        llm_readiness = await provider_readiness_snapshot(rpc)
        logger.info("llm_provider_configuration_ready tasks=%s", sorted(llm_readiness["tasks"]))
        quota_policies = await rpc.select("quota_policies", {
            "enabled": "eq.true",
            "metric_key": f"eq.{os.environ['MOREAI_LLM_QUOTA_METRIC_KEY']}",
            "select": "id",
            "limit": "1",
        })
        if not quota_policies:
            raise RuntimeError("no_enabled_llm_quota_policy")
        browser_client: BrowserSupervisor | None = None
        if os.getenv("MOREAI_BROWSER_ENABLED", "false").lower() == "true":
            browser_client = BrowserSupervisor(
                service_url=os.getenv("MOREAI_BROWSER_SERVICE_URL", ""),
                service_token=os.getenv("MOREAI_BROWSER_SERVICE_TOKEN", ""),
                egress_enforced=os.getenv("MOREAI_BROWSER_EGRESS_ENFORCED", "false").lower() == "true",
                allow_private_http=os.getenv("MOREAI_BROWSER_PRIVATE_NETWORK_HTTP", "false").lower() == "true",
                http=http,
                api_url=os.getenv("MOREAI_INTERNAL_API_URL", os.getenv("MOREAI_API_URL", "http://api:8000")),
                internal_token=os.getenv("MOREAI_WORKER_INTERNAL_TOKEN", ""),
            )
            await browser_client.check_ready()
        sandbox_tools = None
        sandbox_enabled = os.getenv("MOREAI_SANDBOX_ENABLED", "false").lower() == "true"
        sandbox_gate_passed = os.getenv("MOREAI_SANDBOX_RELEASE_GATE_PASSED", "false").lower() == "true"
        if sandbox_enabled and sandbox_gate_passed:
            sandbox_tools = IsolatedSandboxToolAdapter(
                service_url=os.getenv("MOREAI_SANDBOX_SERVICE_URL", ""),
                service_token=os.getenv("MOREAI_SANDBOX_SERVICE_TOKEN", ""),
                allow_private_http=os.getenv("MOREAI_SANDBOX_PRIVATE_NETWORK_HTTP", "false").lower() == "true",
                http=http,
                api_url=os.getenv("MOREAI_INTERNAL_API_URL", os.getenv("MOREAI_API_URL", "http://api:8000")),
                internal_token=os.getenv("MOREAI_WORKER_INTERNAL_TOKEN", ""),
            )
            # Readiness is checked before the worker can claim runs. The worker
            # itself has no Docker socket and cannot launch host-side containers.
            await sandbox_tools.check_ready()
        registry = build_agent_registry(rpc, http, sandbox_tools=sandbox_tools)
        capability_snapshot = registry.capability_snapshot()
        capability_snapshot["llm_provider_readiness"] = llm_readiness
        dispatcher = RegisteredAgentDispatcher(
            registry,
            checkpoint_loader=rpc.list_checkpoints,
            sandbox_supervisor=sandbox_tools,
        )
        runtime = WorkerRuntime(rpc, dispatcher)
        knowledge_ingestion = SupabaseKnowledgeTools(rpc, http)
        readiness = {"ready": False}
        health_server = await asyncio.start_server(
            lambda reader, writer: _health_handler(reader, writer, readiness),
            host=os.getenv("WORKER_HEALTH_HOST", "0.0.0.0"),
            port=int(os.getenv("WORKER_HEALTH_PORT", "8081")),
        )
        async with health_server:
            stop_outbox = asyncio.Event()
            stop_browser_reconciliation = asyncio.Event()
            browser_reconciliation_task = (
                asyncio.create_task(
                    _browser_session_close_reconciliation_loop(
                        browser_client, http,
                        os.getenv("MOREAI_INTERNAL_API_URL", os.getenv("MOREAI_API_URL", "http://api:8000")),
                        os.getenv("MOREAI_WORKER_INTERNAL_TOKEN", ""),
                        stop_browser_reconciliation,
                    ),
                    name="moreai-browser-session-close-reconciliation",
                )
                if browser_client is not None else None
            )
            publisher = DurableEventOutboxPublisher(
                rpc, poll_seconds=float(os.getenv("WORKER_OUTBOX_POLL_SECONDS", "1")),
            )
            outbox_task = asyncio.create_task(publisher.run(stop_outbox), name="moreai-event-outbox")
            # Capability publication is a required readiness gate and runs
            # independently so long Agent Runs do not stale the worker heartbeat.
            capability_task = asyncio.create_task(
                _capability_heartbeat_loop(
                    rpc, list(registry.enabled_keys()), capability_snapshot, readiness,
                ),
                name="moreai-capability-heartbeat",
            )
            poll_seconds = max(1, min(30, int(os.getenv("WORKER_POLL_SECONDS", "3"))))
            memory_purge_interval_seconds = max(
                3600, min(86400, int(os.getenv("MOREAI_MEMORY_PURGE_INTERVAL_SECONDS", "21600"))),
            )
            next_memory_purge_at = 0.0
            monotonic = asyncio.get_running_loop().time
            try:
                # A transient Supabase/PostgREST failure while claiming the next run
                # must not terminate the long-lived worker process. Startup remains
                # fail-fast (credentials, routes, quota and registry are validated
                # above); only the steady-state claim/poll loop uses bounded backoff.
                consecutive_poll_failures = 0
                while True:
                    now = monotonic()
                    if now >= next_memory_purge_at:
                        try:
                            purged_memories = await rpc.rpc("moreai_worker_purge_expired_customer_memories", {})
                            logger.info("personal_memory_retention_purge_completed deleted=%s", purged_memories)
                            next_memory_purge_at = now + memory_purge_interval_seconds
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            logger.exception("personal_memory_retention_purge_failed")
                            next_memory_purge_at = now + 300
                        try:
                            purged_browser_results = await rpc.rpc(
                                "moreai_worker_purge_expired_browser_action_receipt_results", {},
                            )
                            logger.info("browser_action_receipt_result_retention_completed cleared=%s", purged_browser_results)
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            logger.exception("browser_action_receipt_result_retention_failed")
                        try:
                            purged_computer_results = await rpc.rpc(
                                "moreai_worker_purge_expired_computer_action_receipt_results", {},
                            )
                            logger.info("computer_action_receipt_result_retention_completed cleared=%s", purged_computer_results)
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            logger.exception("computer_action_receipt_result_retention_failed")

                    if not readiness["ready"]:
                        await asyncio.sleep(5)
                        continue

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
                                            try:
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
                readiness["ready"] = False
                stop_outbox.set()
                stop_browser_reconciliation.set()
                capability_task.cancel()
                outbox_task.cancel()
                if browser_reconciliation_task is not None:
                    browser_reconciliation_task.cancel()
                await asyncio.gather(
                    capability_task, outbox_task,
                    *([browser_reconciliation_task] if browser_reconciliation_task is not None else []),
                    return_exceptions=True,
                )


if __name__ == "__main__":
    asyncio.run(run_worker())
