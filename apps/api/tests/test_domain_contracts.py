from fastapi.testclient import TestClient
from app.main import app


def test_conversation_and_run_routes_require_authentication():
    with TestClient(app) as client:
        assert client.post("/api/v1/conversations", json={}).status_code == 401
        assert client.get("/api/v1/conversations").status_code == 401
        assert client.get("/api/v1/agent-runs").status_code == 401


def test_message_requires_authentication_and_idempotency():
    with TestClient(app) as client:
        response = client.post("/api/v1/conversations/00000000-0000-0000-0000-000000000001/messages", json={"content": "hello"})
    assert response.status_code == 401


def test_cancel_and_event_stream_require_authentication():
    run_id = "00000000-0000-0000-0000-000000000001"
    with TestClient(app) as client:
        assert client.post(f"/api/v1/agent-runs/{run_id}/cancel").status_code == 401
        assert client.get(f"/api/v1/agent-runs/{run_id}/events").status_code == 401
