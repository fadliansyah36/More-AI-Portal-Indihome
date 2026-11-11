import asyncio

import pytest
from fastapi import HTTPException

import app.authorization as authorization


class FakeRepository:
    def __init__(self, memberships=None, orgs=None, assignments=None, roles=None):
        self.memberships = memberships or []
        self.orgs = orgs or []
        self.assignments = assignments or []
        self.roles = roles or []

    async def select(self, table, params):
        if table == "partner_members":
            return self.memberships
        if table == "partner_organizations":
            return self.orgs
        if table == "user_role_assignments":
            return self.assignments
        if table == "roles":
            return self.roles
        raise AssertionError(table)


def test_customer_access_rejects_active_partner_principals(monkeypatch):
    repo = FakeRepository(memberships=[{"partner_id": "partner-1", "role_key": "partner_staff"}])
    monkeypatch.setattr(authorization, "repository", lambda request: repo)

    async def run():
        with pytest.raises(HTTPException) as error:
            await authorization.require_customer_context(object(), {"id": "user-1"})
        assert error.value.status_code == 403
    asyncio.run(run())


def test_customer_access_derives_base_customer_role_for_non_partner_user(monkeypatch):
    repo = FakeRepository()
    monkeypatch.setattr(authorization, "repository", lambda request: repo)

    async def run():
        result = await authorization.require_customer_context(object(), {"id": "user-1"})
        assert result["principal_role"] == "customer"
        assert result["tenant_id"] is None
    asyncio.run(run())


def test_partner_access_resolves_only_active_membership_tenant(monkeypatch):
    repo = FakeRepository(
        memberships=[{"partner_id": "partner-1", "role_key": "partner_admin", "location_id": None}],
        orgs=[{"id": "partner-1", "status": "active", "display_name": "Partner"}],
    )
    monkeypatch.setattr(authorization, "repository", lambda request: repo)

    async def run():
        result = await authorization.require_partner_context(object(), {"id": "user-1"})
        assert result["partner_id"] == "partner-1"
        assert result["principal_role"] == "partner_admin"
    asyncio.run(run())


def test_partner_access_rejects_unassigned_tenant(monkeypatch):
    repo = FakeRepository(
        memberships=[{"partner_id": "partner-1", "role_key": "partner_staff", "location_id": "loc-1"}],
        orgs=[{"id": "partner-1", "status": "active", "display_name": "Partner"}],
    )
    monkeypatch.setattr(authorization, "repository", lambda request: repo)

    async def run():
        with pytest.raises(HTTPException) as error:
            await authorization.require_partner_context(object(), {"id": "user-1"}, "partner-other")
        assert error.value.status_code == 403
    asyncio.run(run())
