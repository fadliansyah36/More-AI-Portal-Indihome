import asyncio
import json

import httpx
import pytest

from app.client import WorkerRpcClient, WorkerSettings
from app.runtime import WorkerRuntime
from engine.agents.errors import RunPausedForApproval


def test_worker_settings_reject_http_and_short_worker_id():
    with pytest.raises(ValueError):
        WorkerSettings("http://localhost", "secret", "worker")


def test_claim_uses_server_only_credentials_and_existing_rpc():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=b'null', headers={'content-type': 'application/json'})

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


def test_workspace_editor_uses_persisted_file_edit_approval_key():
    calls = []

    def handler(request):
        calls.append((request.url.path, json.loads(request.content)))
        return httpx.Response(
            200,
            json={"status": "pending", "approval_id": "approval-1"},
        )

    async def run():
        settings = WorkerSettings("https://project.supabase.co", "service-secret", "worker-test-01")
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = WorkerRpcClient(settings, http)
            with pytest.raises(RunPausedForApproval):
                await client.wait_for_tool_approval(
                    "run-1", "user-1", "str_replace_editor",
                    {"path": "src/main.py", "old_str": "old", "new_str": "new"},
                )

    asyncio.run(run())
    assert len(calls) == 1
    path, payload = calls[0]
    assert path.endswith("/rpc/moreai_worker_pause_for_tool_approval")
    assert payload["p_tool_key"] == "file_edit"
    assert payload["p_run_id"] == "run-1"
    assert payload["p_user_id"] == "user-1"


def test_runtime_requires_dispatcher_before_claiming():
    settings = WorkerSettings("https://project.supabase.co", "service-secret", "worker-test-01")

    async def run():
        async with httpx.AsyncClient() as http:
            rpc = WorkerRpcClient(settings, http)
            with pytest.raises(ValueError):
                WorkerRuntime(rpc, None)

    asyncio.run(run())
