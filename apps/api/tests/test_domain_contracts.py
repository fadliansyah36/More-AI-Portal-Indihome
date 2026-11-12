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

from app.dependencies import current_user
from app.authorization import customer_principal


def test_agent_run_enqueue_fails_closed_until_runtime_is_enabled(monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000010"
    app.dependency_overrides[current_user] = lambda: {"id": user_id, "email": "test@example.invalid"}
    app.dependency_overrides[customer_principal] = lambda: {"id": user_id, "email": "test@example.invalid", "principal_role": "customer"}
    monkeypatch.setenv("MOREAI_AGENT_EXECUTION_ENABLED", "false")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/conversations/00000000-0000-0000-0000-000000000001/messages",
                headers={"Idempotency-Key": "integration-test-key-001"},
                json={"content": "do not enqueue without a worker"},
            )
        assert response.status_code == 503
        assert "Agent execution is disabled" in response.json()["error"]["message"]
        assert response.json()["error"]["correlation_id"] == response.headers["X-Correlation-ID"]
    finally:
        app.dependency_overrides.clear()
