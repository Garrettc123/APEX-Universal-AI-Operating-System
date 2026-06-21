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


def test_breakthroughs_endpoint():
    resp = client.get("/api/breakthroughs?count=3&seed=42")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 3
    assert len(body["breakthroughs"]) == 3
    scores = [b["score"] for b in body["breakthroughs"]]
    assert scores == sorted(scores, reverse=True)


def test_breakthroughs_invalid_count():
    assert client.get("/api/breakthroughs?count=0").status_code == 422
    assert client.get("/api/breakthroughs?count=999").status_code == 422


def test_breakthroughs_unknown_domain_400():
    resp = client.get("/api/breakthroughs?domain=nope")
    assert resp.status_code == 400


def test_breakthrough_domains_endpoint():
    resp = client.get("/api/breakthroughs/domains")
    assert resp.status_code == 200
    assert "fintech" in resp.json()["domains"]


def test_entitlement_unknown_customer():
    resp = client.get("/api/entitlements/never_seen")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"customer_id": "never_seen", "active": False, "status": None, "plan_id": None}


def test_entitlement_loop_grant_then_read(monkeypatch):
    from src import entitlements

    monkeypatch.delenv("DATABASE_URL", raising=False)
    entitlements._reset_memory()
    # Simulate a Stripe webhook granting access, then read it back via the API.
    entitlements.grant("cus_api", plan_id="pro", status="active")
    body = client.get("/api/entitlements/cus_api").json()
    assert body["active"] is True
    assert body["status"] == "active"
    assert body["plan_id"] == "pro"
    entitlements._reset_memory()


def test_breakthroughs_open_when_enforcement_off(monkeypatch):
    monkeypatch.delenv("ENFORCE_ENTITLEMENTS", raising=False)
    # No customer header needed when enforcement is disabled (default).
    assert client.get("/api/breakthroughs?count=2").status_code == 200


def test_breakthroughs_requires_header_when_enforced(monkeypatch):
    monkeypatch.setenv("ENFORCE_ENTITLEMENTS", "true")
    resp = client.get("/api/breakthroughs?count=2")
    assert resp.status_code == 401


def test_breakthroughs_payment_required_without_access(monkeypatch):
    from src import entitlements

    monkeypatch.setenv("ENFORCE_ENTITLEMENTS", "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    entitlements._reset_memory()
    resp = client.get("/api/breakthroughs?count=2", headers={"X-Customer-Id": "cus_none"})
    assert resp.status_code == 402


def test_breakthroughs_allowed_with_active_entitlement(monkeypatch):
    from src import entitlements

    monkeypatch.setenv("ENFORCE_ENTITLEMENTS", "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    entitlements._reset_memory()
    entitlements.grant("cus_paid", plan_id="pro", status="active")
    resp = client.get("/api/breakthroughs?count=2", headers={"X-Customer-Id": "cus_paid"})
    assert resp.status_code == 200
    assert resp.json()["count"] == 2
    entitlements._reset_memory()
