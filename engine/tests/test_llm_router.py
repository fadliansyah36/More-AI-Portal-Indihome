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

def test_metered_completion_passes_workspace_scope_to_credit_reservation():
    class Router:
        async def resolve(self, task_type, **kwargs):
            self.scope = kwargs
            return ResolvedModelRoute("provider", "model", "Model", "https://provider.example/v1", "MOREAI_PROVIDER_TEST_API_KEY", 1, 2, 10000, 1000, ("chat",))
    class Estimator:
        async def estimate(self, **kwargs):
            return CreditEstimate(0.01, 10)
        async def actual_credits(self, **kwargs):
            return 8
    class Accounting:
        def __init__(self):
            self.reservation_args = None
        async def claim_request(self, **kwargs):
            return {"created": True, "id": "request-1"}
        async def reserve(self, **kwargs):
            self.reservation_args = kwargs
            return "reservation-1"
        async def record_provider_result(self, **kwargs):
            return None
        async def finalize(self, **kwargs):
            return None
        async def fail(self, **kwargs):
            raise AssertionError("successful completion must not fail")
    class Adapter:
        async def complete(self, **kwargs):
            return {"text": "answer", "provider_key": "provider", "model_key": "model", "input_tokens": 5, "output_tokens": 2, "actual_cost": 0.001}
    async def run():
        router = Router()
        accounting = Accounting()
        gateway = MeteredGateway(router=router, estimator=Estimator(), accounting=accounting, adapter=Adapter())
        result = await gateway.complete(
            user_id="user-1", run_id="run-1", request_key="request-key-001",
            messages=[{"role": "user", "content": "hello"}], workspace_id="workspace-1",
        )
        assert result["text"] == "answer"
        assert router.scope["workspace_id"] == "workspace-1"
        assert accounting.reservation_args["workspace_id"] == "workspace-1"
    asyncio.run(run())


def test_metered_completion_fails_over_and_settles_against_the_selected_provider():
    from engine.llm.errors import RetryableProviderError

    primary = ResolvedModelRoute("provider-a", "model-a", "A", "https://a.example/v1", "MOREAI_PROVIDER_A", 1, 2, 10000, 1000, ("chat",))
    fallback = ResolvedModelRoute("provider-b", "model-b", "B", "https://b.example/v1", "MOREAI_PROVIDER_B", 2, 3, 10000, 1000, ("chat",))

    class Router:
        async def resolve_candidates(self, task_type, **kwargs):
            return [primary, fallback]

    class Estimator:
        async def estimate(self, *, route, messages):
            return CreditEstimate(route.input_cost_per_million / 100, route.input_cost_per_million * 10)
        async def actual_credits(self, *, route, result):
            assert route.provider_key == "provider-b"
            return 3

    class Accounting:
        def __init__(self):
            self.calls = []
        async def claim_request(self, **kwargs):
            return {"created": True, "id": "request-1"}
        async def reserve(self, **kwargs):
            self.calls.append(("reserve", kwargs))
            return "reservation-1"
        async def record_provider_result(self, **kwargs):
            self.calls.append(("result", kwargs["result"]["provider_key"]))
        async def finalize(self, **kwargs):
            self.calls.append(("finalize", kwargs))
        async def fail(self, **kwargs):
            raise AssertionError("fallback success must not release the reservation")

    class Adapter:
        async def complete(self, *, route, **kwargs):
            if route.provider_key == "provider-a":
                raise RetryableProviderError("provider_timeout")
            return {"text": "fallback answer", "provider_key": route.provider_key, "model_key": route.model_key, "input_tokens": 5, "output_tokens": 2, "actual_cost": 0.001}

    async def run():
        accounting = Accounting()
        gateway = MeteredGateway(router=Router(), estimator=Estimator(), accounting=accounting, adapter=Adapter())
        result = await gateway.complete(
            user_id="u1", run_id="r1", request_key="fallback-request-001",
            messages=[{"role": "user", "content": "hello"}],
        )
        assert result["provider_key"] == "provider-b"
        assert accounting.calls[0][0] == "reserve"
        assert accounting.calls[0][1]["estimated_credits"] == 20
        assert ("result", "provider-b") in accounting.calls
    asyncio.run(run())


def test_stream_fails_over_only_before_first_emitted_delta():
    from engine.llm.errors import RetryableProviderError

    primary = ResolvedModelRoute("provider-a", "model-a", "A", "https://a.example/v1", "MOREAI_PROVIDER_A", 1, 2, 10000, 1000, ("chat",))
    fallback = ResolvedModelRoute("provider-b", "model-b", "B", "https://b.example/v1", "MOREAI_PROVIDER_B", 2, 3, 10000, 1000, ("chat",))

    class Router:
        async def resolve_candidates(self, task_type, **kwargs):
            return [primary, fallback]

    class Estimator:
        async def estimate(self, **kwargs):
            return CreditEstimate(0.01, 10)
        async def actual_credits(self, **kwargs):
            return 4

    class Accounting:
        async def claim_request(self, **kwargs):
            return {"created": True, "id": "request-1"}
        async def reserve(self, **kwargs):
            return "reservation-1"
        async def record_provider_result(self, **kwargs):
            return None
        async def finalize(self, **kwargs):
            return None
        async def fail(self, **kwargs):
            raise AssertionError("fallback stream should settle")

    class Adapter:
        async def stream(self, *, route, **kwargs):
            if route.provider_key == "provider-a":
                raise RetryableProviderError("provider_unavailable")
            yield {"type": "delta", "text": "fallback"}
            yield {"type": "usage", "provider_key": "provider-b", "model_key": "model-b", "input_tokens": 2, "output_tokens": 1, "actual_cost": 0.001}

    async def run():
        gateway = MeteredGateway(router=Router(), estimator=Estimator(), accounting=Accounting(), adapter=Adapter())
        events = [item async for item in gateway.stream(
            user_id="u1", run_id="r1", request_key="fallback-stream-001",
            messages=[{"role": "user", "content": "hello"}],
        )]
        assert events[0] == {"type": "delta", "text": "fallback"}
        assert events[-1]["provider_key"] == "provider-b"
    asyncio.run(run())
