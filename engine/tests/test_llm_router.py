import asyncio
import pytest

from engine.llm.router import CreditEstimate, MeteredGateway, ModelRouter, NoEligibleModelRoute, ResolvedModelRoute


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


def test_router_uses_fallback_model_when_primary_is_unavailable():
    class FallbackRepository:
        async def list_enabled_routes(self, task_type, *, user_id=None, workspace_id=None, partner_id=None):
            return [{"model_id": "primary", "fallback_model_id": "fallback", "priority": 10}]
        async def get_enabled_model(self, model_id):
            if model_id == "primary":
                return None
            return {"id": "fallback", "key": "model-fallback", "display_name": "Fallback", "provider_id": "provider-1", "capabilities": ["chat"], "input_cost_per_million": 1, "output_cost_per_million": 2, "max_input_tokens": 10000, "max_output_tokens": 1000}
        async def get_enabled_provider(self, provider_id):
            return {"key": "provider-1", "config": {"base_url": "https://provider.example/v1", "secret_env_name": "MOREAI_PROVIDER_TEST_API_KEY"}}
    route = asyncio.run(ModelRouter(FallbackRepository()).resolve("chat"))
    assert route.model_key == "model-fallback"


def test_metered_stream_reserves_and_settles_before_completion():
    class Router:
        async def resolve(self, task_type, **kwargs):
            return ResolvedModelRoute("provider", "model", "Model", "https://provider.example/v1", "MOREAI_PROVIDER_TEST_API_KEY", 1, 2, 10000, 1000, ("chat",))
    class Estimator:
        async def estimate(self, **kwargs):
            return CreditEstimate(estimated_cost=0.01, estimated_credits=10)
        async def actual_credits(self, **kwargs):
            return 8
    class Accounting:
        def __init__(self):
            self.calls = []
        async def claim_request(self, **kwargs):
            self.calls.append("claim")
            return {"created": True, "id": "request-1"}
        async def reserve(self, **kwargs):
            self.calls.append("reserve")
            return "reservation-1"
        async def record_provider_result(self, **kwargs):
            self.calls.append("provider_result")
        async def finalize(self, **kwargs):
            self.calls.append("finalize")
        async def fail(self, **kwargs):
            self.calls.append("fail")
    class Adapter:
        async def stream(self, **kwargs):
            yield {"type": "delta", "text": "hello"}
            yield {"type": "usage", "provider_key": "provider", "model_key": "model", "input_tokens": 5, "output_tokens": 2, "actual_cost": 0.001}
    async def run():
        accounting = Accounting()
        gateway = MeteredGateway(router=Router(), estimator=Estimator(), accounting=accounting, adapter=Adapter())
        chunks = [item async for item in gateway.stream(user_id="u1", run_id="r1", request_key="request-key-001", messages=[{"role": "user", "content": "hello"}])]
        assert chunks[0] == {"type": "delta", "text": "hello"}
        assert chunks[-1]["type"] == "done"
        assert accounting.calls == ["claim", "reserve", "provider_result", "finalize"]
    asyncio.run(run())
