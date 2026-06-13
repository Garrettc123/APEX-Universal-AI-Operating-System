"""Tests for the integrations hub service and API."""

import pytest
from fastapi.testclient import TestClient

from app import app
from src.integrations_service import IntegrationsService


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# -- service-level -----------------------------------------------------------


def test_list_orders_connected_first():
    svc = IntegrationsService()
    rows = svc.list()

    assert rows, "expected seeded integrations"
    connected_flags = [r["connected"] for r in rows]
    # Once a False appears, no True may follow (connected sorted first).
    assert connected_flags == sorted(connected_flags, reverse=True)


def test_trigger_connected_records_success_and_updates_sync():
    svc = IntegrationsService()
    run = svc.trigger("gmail")

    assert run is not None
    assert run["status"] == "succeeded"
    assert svc.get("gmail")["last_sync"] == run["started_at"]
    assert svc.get("gmail")["recent_runs"][0]["run_id"] == run["run_id"]


def test_trigger_disconnected_is_skipped():
    svc = IntegrationsService()
    run = svc.trigger("stripe")  # seeded as not connected

    assert run is not None
    assert run["status"] == "skipped"


def test_trigger_unknown_returns_none():
    svc = IntegrationsService()
    assert svc.trigger("does-not-exist") is None


# -- API-level ---------------------------------------------------------------


def test_api_list_integrations(client: TestClient):
    resp = client.get("/api/integrations")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert resp.json()


def test_api_get_integration(client: TestClient):
    resp = client.get("/api/integrations/notion")
    assert resp.status_code == 200
    assert resp.json()["id"] == "notion"
    assert "recent_runs" in resp.json()


def test_api_get_unknown_integration_404(client: TestClient):
    assert client.get("/api/integrations/nope").status_code == 404


def test_api_trigger_integration(client: TestClient):
    resp = client.post("/api/integrations/slack/trigger")
    assert resp.status_code == 200
    assert resp.json()["integration_id"] == "slack"


def test_api_trigger_unknown_404(client: TestClient):
    assert client.post("/api/integrations/nope/trigger").status_code == 404
