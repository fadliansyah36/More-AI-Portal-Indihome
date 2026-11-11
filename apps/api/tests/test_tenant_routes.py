from fastapi.testclient import TestClient

from app.main import app


def test_customer_and_partner_routes_require_authenticated_session():
    run_id = "00000000-0000-0000-0000-000000000001"
    with TestClient(app) as client:
        assert client.get("/api/v1/customer/context").status_code == 401
        assert client.get("/api/v1/customer/wallet").status_code == 401
        assert client.get("/api/v1/customer/wallet/ledger").status_code == 401
        assert client.get("/api/v1/customer/usage").status_code == 401
        assert client.get("/api/v1/customer/entitlements").status_code == 401
        assert client.get("/api/v1/customer/quotas").status_code == 401
        assert client.get("/api/v1/customer/conversations").status_code == 401
        assert client.get(f"/api/v1/customer/agent-runs/{run_id}/stream").status_code == 401
        assert client.get("/api/v1/partner/tenants").status_code == 401
        assert client.get("/api/v1/partner/context").status_code == 401
        assert client.get("/api/v1/partner/locations").status_code == 401
        assert client.get("/api/v1/partner/members").status_code == 401
        assert client.get("/api/v1/partner/sessions").status_code == 401
        assert client.get("/api/v1/partner/campaigns").status_code == 401
        assert client.get("/api/v1/partner/campaigns/00000000-0000-0000-0000-000000000001/rewards").status_code == 401


def test_legacy_customer_routes_are_not_public():
    with TestClient(app) as client:
        assert client.get("/api/v1/conversations").status_code == 401
        assert client.get("/api/v1/agent-runs").status_code == 401
