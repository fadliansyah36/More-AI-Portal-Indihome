import asyncio
import hashlib
import json
from types import SimpleNamespace

import pytest

from engine.tools.workspace import SupabaseWorkspaceTool


class FakeResponse:
    def __init__(self, *, content=b"", payload=None, status_code=200):
        self.content = content
        self.payload = payload or {}
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http_error")


class FakeHttp:
    def __init__(self, raw):
        self.raw = raw

    async def get(self, url, **kwargs):
        if "/storage/v1/bucket/" in url:
            return FakeResponse(payload={"public": False})
        return FakeResponse(content=self.raw)


class FakeWorkspaceClient:
    def __init__(self, raw, metadata):
        self.settings = SimpleNamespace(supabase_url="https://project.supabase.co", service_role_key="service-secret")
        self.client = FakeHttp(raw)
        self.metadata = metadata

    async def workspace_get_file(self, user_id, workspace_id, path):
        assert user_id == "user-1"
        assert workspace_id == "workspace-1"
        assert path == "src/main.py"
        return self.metadata


def test_workspace_read_returns_text_only_after_scope_and_sha256_validation():
    raw = b"print('hello')\n"
    metadata = {
        "version": 3,
        "storage_path": "workspace-1/src/main.py/v3",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }
    tool = SupabaseWorkspaceTool(FakeWorkspaceClient(raw, metadata))

    async def run():
        return await tool.read_file(
            {"path": "src/main.py"},
            run_id="run-1",
            user_id="user-1",
            workspace_id="workspace-1",
        )

    result = json.loads(asyncio.run(run()))
    assert result["content"] == "print('hello')\n"
    assert result["version"] == 3
    assert result["sha256"] == metadata["sha256"]


def test_workspace_read_rejects_object_integrity_mismatch():
    raw = b"tampered"
    metadata = {
        "version": 2,
        "storage_path": "workspace-1/src/main.py/v2",
        "sha256": "0" * 64,
        "size_bytes": len(raw),
    }
    tool = SupabaseWorkspaceTool(FakeWorkspaceClient(raw, metadata))

    async def run():
        await tool.read_file(
            {"path": "src/main.py"},
            run_id="run-2",
            user_id="user-1",
            workspace_id="workspace-1",
        )

    with pytest.raises(RuntimeError, match="workspace_file_integrity_mismatch"):
        asyncio.run(run())


def test_workspace_read_rejects_path_traversal_before_storage_access():
    tool = SupabaseWorkspaceTool(FakeWorkspaceClient(b"", {}))

    async def run():
        await tool.read_file(
            {"path": "../secrets.txt"},
            run_id="run-3",
            user_id="user-1",
            workspace_id="workspace-1",
        )

    with pytest.raises(ValueError, match="workspace_path_traversal_denied"):
        asyncio.run(run())


class FakeLifecycleClient(FakeWorkspaceClient):
    def __init__(self, metadata_by_path):
        super().__init__(b"", {})
        self.metadata_by_path = metadata_by_path
        self.lifecycle_calls = []

    async def workspace_get_file(self, user_id, workspace_id, path):
        return self.metadata_by_path.get(path, {"version": 0, "storage_path": None})

    async def workspace_delete_file(self, run_id, user_id, workspace_id, path, expected_version):
        self.lifecycle_calls.append(("delete", path, expected_version))
        return {"path": path, "version": expected_version, "deleted": True}

    async def workspace_rename_file(self, run_id, user_id, workspace_id, path, new_path, expected_version):
        self.lifecycle_calls.append(("rename", path, new_path, expected_version))
        return {"old_path": path, "path": new_path, "version": expected_version + 1, "renamed": True}


def test_workspace_delete_uses_expected_version_and_lease_fenced_rpc():
    client = FakeLifecycleClient({
        "src/old.py": {
            "version": 4, "storage_path": "user/workspaces/ws/versions/4/src/old.py",
        },
    })
    tool = SupabaseWorkspaceTool(client)

    async def run():
        return json.loads(await tool.str_replace_editor(
            {"operation": "delete", "path": "src/old.py", "expected_version": 4},
            run_id="run-1", user_id="user-1", workspace_id="workspace-1",
        ))

    result = asyncio.run(run())
    assert result["deleted"] is True
    assert client.lifecycle_calls == [("delete", "src/old.py", 4)]


def test_workspace_rename_uses_expected_version_and_rejects_existing_target():
    client = FakeLifecycleClient({
        "src/old.py": {
            "version": 2, "storage_path": "user/workspaces/ws/versions/2/src/old.py",
        },
        "src/new.py": {"version": 0, "storage_path": None},
    })
    tool = SupabaseWorkspaceTool(client)

    async def run():
        return json.loads(await tool.str_replace_editor(
            {"operation": "rename", "path": "src/old.py", "new_path": "src/new.py", "expected_version": 2},
            run_id="run-2", user_id="user-1", workspace_id="workspace-1",
        ))

    result = asyncio.run(run())
    assert result["renamed"] is True
    assert client.lifecycle_calls == [("rename", "src/old.py", "src/new.py", 2)]

    client.metadata_by_path["src/new.py"] = {
        "version": 1, "storage_path": "user/workspaces/ws/versions/1/src/new.py",
    }
    with pytest.raises(ValueError, match="workspace_rename_target_exists"):
        asyncio.run(run())
