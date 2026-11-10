import asyncio

from app.llm_accounting import ConfiguredCreditEstimator, SupabaseUsageAccounting
from engine.llm.router import ResolvedModelRoute


def route():
    return ResolvedModelRoute(
        "provider", "model", "Model", "https://provider.example/v1",
        "MOREAI_PROVIDER_TEST_API_KEY", 1.0, 2.0, 10000, 1000, ("chat",),
    )


def test_credit_estimator_requires_explicit_business_conversion(monkeypatch):
    monkeypatch.delenv("MOREAI_CREDITS_PER_USD", raising=False)
    async def run():
        try:
            await ConfiguredCreditEstimator().estimate(route=route(), messages=[{"role": "user", "content": "hi"}])
        except RuntimeError as exc:
            assert str(exc) == "credit_conversion_not_configured"
            return
        raise AssertionError("credit conversion must be explicit")
    asyncio.run(run())


def test_credit_estimator_uses_model_price_and_configured_conversion(monkeypatch):
    monkeypatch.setenv("MOREAI_CREDITS_PER_USD", "1000")
    async def run():
        estimate = await ConfiguredCreditEstimator().estimate(route=route(), messages=[{"role": "user", "content": "hello"}])
        assert estimate.estimated_cost > 0
        assert estimate.estimated_credits == estimate.estimated_cost * 1000
    asyncio.run(run())


def test_usage_reservation_uses_atomic_entitlement_quota_credit_rpc(monkeypatch):
    monkeypatch.setenv("MOREAI_CREDIT_WALLET_CURRENCY", "AI_CREDIT")
    monkeypatch.setenv("MOREAI_LLM_ENTITLEMENT_KEY", "ai.generate")
    monkeypatch.setenv("MOREAI_LLM_QUOTA_METRIC_KEY", "ai_credits")
    class FakeClient:
        def __init__(self):
            self.calls = []
        async def select(self, table, params):
            assert table == "wallet_accounts"
            return [{"id": "wallet-1"}]
        async def rpc(self, name, payload):
            self.calls.append((name, payload))
            return {"reservation_id": "reservation-1"}
    async def run():
        client = FakeClient()
        result = await SupabaseUsageAccounting(client).reserve(
            request_id="request-1", user_id="user-1", run_id="run-1",
            request_key="request-key-123", estimated_credits=5, estimated_cost=0.01,
            workspace_id="workspace-1", partner_id=None,
        )
        assert result == "reservation-1"
        name, payload = client.calls[0]
        assert name == "moreai_llm_reserve_request"
        assert payload["p_entitlement_key"] == "ai.generate"
        assert payload["p_quota_metric_key"] == "ai_credits"
        assert payload["p_quota_amount"] == 5
        assert payload["p_workspace_id"] == "workspace-1"
    asyncio.run(run())
