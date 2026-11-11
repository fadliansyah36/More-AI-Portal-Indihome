import asyncio

import pytest
from fastapi import HTTPException

import app.authorization as authorization


class AdminRepository:
    def __init__(self, assignments=None, roles=None):
        self.assignments = assignments or []
        self.roles = roles or []

    async def select(self, table, params):
        if table == "user_role_assignments":
            return self.assignments
        if table == "roles":
            return self.roles
        raise AssertionError(table)


def test_platform_guard_rejects_user_without_assignment(monkeypatch):
    repo = AdminRepository()
    monkeypatch.setattr(authorization, "_repository", lambda request: repo)

    async def run():
        with pytest.raises(HTTPException) as error:
            await authorization.require_platform_context(object(), {"id": "user-1"})
        assert error.value.status_code == 403

    asyncio.run(run())


def test_platform_guard_accepts_server_assigned_platform_admin(monkeypatch):
    repo = AdminRepository(
        assignments=[{"id": "assignment-1", "role_id": "role-1"}],
        roles=[{"id": "role-1", "key": "super_admin", "scope": "platform"}],
    )
    monkeypatch.setattr(authorization, "_repository", lambda request: repo)

    async def run():
        result = await authorization.require_platform_context(object(), {"id": "user-1"})
        assert result["principal_role"] == "super_admin"
        assert result["platform_roles"] == ["super_admin"]

    asyncio.run(run())


def test_platform_guard_rejects_partner_role_or_wrong_scope(monkeypatch):
    repo = AdminRepository(
        assignments=[{"id": "assignment-1", "role_id": "role-1"}],
        roles=[{"id": "role-1", "key": "partner_admin", "scope": "partner"}],
    )
    monkeypatch.setattr(authorization, "_repository", lambda request: repo)

    async def run():
        with pytest.raises(HTTPException) as error:
            await authorization.require_platform_context(object(), {"id": "user-1"})
        assert error.value.status_code == 403

    asyncio.run(run())
