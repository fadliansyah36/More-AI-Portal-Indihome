from fastapi.testclient import TestClient

from app.main import app


def test_customer_and_partner_routes_require_authenticated_session():
    with TestClient(app) as client:
        assert client.get("/api/v1/customer/context").status_code == 401
        assert client.get("/api/v1/customer/conversations").status_code == 401
        assert client.get("/api/v1/partner/context").status_code == 401
        assert client.get("/api/v1/partner/locations").status_code == 401
