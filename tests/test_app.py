"""Tests for the FastAPI application endpoints."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root_and_health():
    assert client.get("/").status_code == 200
    assert client.get("/health").json() == {"status": "healthy"}


def test_pricing_endpoint():
    resp = client.get("/pricing")
    assert resp.status_code == 200
    body = resp.json()
    assert body["currency"] == "USD"
    assert isinstance(body["plans"], list) and body["plans"]
    assert "contact_sales" in body


def test_status_endpoint():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "revenue" in body
    assert "annual_projection_usd" in body["revenue"]


def test_checkout_unknown_plan_404():
    resp = client.post("/api/checkout", json={"plan_id": "nope"})
    assert resp.status_code == 404


def test_checkout_not_configured_503(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    resp = client.post("/api/checkout", json={"plan_id": "starter"})
    assert resp.status_code == 503


def test_store_front_end_served():
    resp = client.get("/store")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "APEX" in resp.text


def test_webhook_not_configured_503(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    resp = client.post("/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "x"})
    assert resp.status_code == 503
