import asyncio
import pytest

from engine.llm.router import ModelRouter, NoEligibleModelRoute


class EmptyRepository:
    async def list_enabled_routes(self, task_type, *, user_id=None, workspace_id=None, partner_id=None):
        return []
    async def get_enabled_model(self, model_id):
        return None
    async def get_enabled_provider(self, provider_id):
        return None


def test_router_fails_closed_when_no_provider_route_is_configured():
    with pytest.raises(NoEligibleModelRoute):
        asyncio.run(ModelRouter(EmptyRepository()).resolve("chat", user_id="user-1"))


def test_router_passes_tenant_scope_to_repository():
    class ScopedRepository(EmptyRepository):
        def __init__(self):
            self.scope = None
        async def list_enabled_routes(self, task_type, *, user_id=None, workspace_id=None, partner_id=None):
            self.scope = (user_id, workspace_id, partner_id)
            return []
    repository = ScopedRepository()
    with pytest.raises(NoEligibleModelRoute):
        asyncio.run(ModelRouter(repository).resolve("chat", user_id="u1", workspace_id="w1", partner_id="p1"))
    assert repository.scope == ("u1", "w1", "p1")
