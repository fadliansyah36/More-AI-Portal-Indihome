from fastapi.testclient import TestClient
from app.main import app


def test_health_is_live():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_fails_closed_without_supabase_configuration(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"]["supabase_auth"] is False


def test_me_requires_bearer_token():
    with TestClient(app) as client:
        response = client.get("/v1/me")
    assert response.status_code == 401
