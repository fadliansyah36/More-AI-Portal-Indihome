import asyncio
import pytest

from engine.llm.router import ModelRouter, NoEligibleModelRoute


class EmptyRepository:
    async def list_enabled_routes(self, task_type):
        return []
    async def get_enabled_model(self, model_id):
        return None
    async def get_enabled_provider(self, provider_id):
        return None


def test_router_fails_closed_when_no_provider_route_is_configured():
    with pytest.raises(NoEligibleModelRoute):
        asyncio.run(ModelRouter(EmptyRepository()).resolve("chat"))
