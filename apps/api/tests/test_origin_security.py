from fastapi.testclient import TestClient

from app import main


def test_mutation_rejects_untrusted_origin(monkeypatch):
    monkeypatch.setattr(main, "_cors_origins", ["https://portal.moreai.web.id"])
    client = TestClient(main.app)
    response = client.post("/api/v1/me/profile", headers={"Origin": "https://attacker.example"}, json={"display_name": "Injected"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "untrusted_origin"


def test_mutation_rejects_cross_site_fetch_without_origin(monkeypatch):
    monkeypatch.setattr(main, "_cors_origins", ["https://portal.moreai.web.id"])
    client = TestClient(main.app)
    response = client.post("/api/v1/me/profile", headers={"Sec-Fetch-Site": "cross-site"}, json={"display_name": "Injected"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "cross_site_request_denied"


def test_same_origin_mutation_reaches_authentication_guard(monkeypatch):
    monkeypatch.setattr(main, "_cors_origins", ["https://portal.moreai.web.id"])
    client = TestClient(main.app)
    response = client.post("/api/v1/me/profile", headers={"Origin": "https://portal.moreai.web.id"}, json={"display_name": "Valid"})
    assert response.status_code == 401