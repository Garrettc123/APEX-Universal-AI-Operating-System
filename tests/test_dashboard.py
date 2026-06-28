"""Tests for the mobile command dashboard service and API."""

import pytest
from fastapi.testclient import TestClient

from app import app
from src.dashboard_service import DashboardService


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# -- service-level -----------------------------------------------------------


def test_overview_reports_initialized_systems():
    svc = DashboardService()
    overview = svc.overview()

    assert overview["systems_total"] > 0
    assert overview["systems_healthy"] <= overview["systems_total"]
    assert overview["state"] == "active"
    assert 0.0 <= overview["average_health"] <= 1.0
    assert overview["generated_at"].endswith("Z")


def test_systems_sorted_worst_health_first():
    svc = DashboardService()
    rows = svc.systems()

    assert len(rows) == svc.overview()["systems_total"]
    healths = [r["health_score"] for r in rows]
    assert healths == sorted(healths)


def test_revenue_breakdown_shape():
    svc = DashboardService()
    revenue = svc.revenue()

    assert "total_revenue" in revenue
    assert "annual_projection" in revenue
    assert isinstance(revenue["strategies"], list)
    assert revenue["strategies"], "expected at least one revenue strategy"
    for strat in revenue["strategies"]:
        assert {"name", "rate", "clients", "revenue"} <= strat.keys()


@pytest.mark.asyncio
async def test_evolution_increments_cycle_count():
    svc = DashboardService()
    before = svc.overview()["evolution_cycles"]

    after = await svc.trigger_evolution()

    assert after["evolution_cycles"] == before + 1


# -- API-level ---------------------------------------------------------------


def test_api_overview_endpoint(client: TestClient):
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    assert "intelligence_level" in resp.json()


def test_api_systems_endpoint(client: TestClient):
    resp = client.get("/api/systems")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_api_revenue_endpoint(client: TestClient):
    resp = client.get("/api/revenue")
    assert resp.status_code == 200
    assert "strategies" in resp.json()


def test_api_cycle_endpoints(client: TestClient):
    assert client.post("/api/cycle/evolve").status_code == 200
    assert client.post("/api/cycle/optimize").status_code == 200
    assert client.post("/api/cycle/revenue").status_code == 200
