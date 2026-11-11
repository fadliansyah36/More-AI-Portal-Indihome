from fastapi.testclient import TestClient

from app.main import app


def test_admin_routes_require_bearer_token():
    paths = [
        "/api/v1/admin/context",
        "/api/v1/admin/overview",
        "/api/v1/admin/partners",
        "/api/v1/admin/agent-runs",
        "/api/v1/admin/audit",
    ]
    with TestClient(app) as client:
        for path in paths:
            response = client.get(path)
            assert response.status_code == 401, path
