import asyncio
import httpx
import pytest

from app.client import WorkerRpcClient, WorkerSettings
from app.runtime import WorkerRuntime


def test_worker_settings_reject_http_and_short_worker_id():
    with pytest.raises(ValueError):
        WorkerSettings("http://localhost", "secret", "worker")


def test_claim_uses_server_only_credentials_and_existing_rpc():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=None)

    async def run():
        settings = WorkerSettings("https://project.supabase.co", "service-secret", "worker-test-01")
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            result = await WorkerRpcClient(settings, http).claim_run()
        return result

    assert asyncio.run(run()) is None
    request = calls[0]
    assert request.url.path.endswith("/rpc/moreai_worker_claim_run")
    assert request.headers["apikey"] == "service-secret"
    assert request.headers["authorization"] == "Bearer service-secret"


def test_runtime_requires_dispatcher_before_claiming():
    settings = WorkerSettings("https://project.supabase.co", "service-secret", "worker-test-01")
    async def run():
        async with httpx.AsyncClient() as http:
            rpc = WorkerRpcClient(settings, http)
            with pytest.raises(ValueError):
                WorkerRuntime(rpc, None)
    asyncio.run(run())
