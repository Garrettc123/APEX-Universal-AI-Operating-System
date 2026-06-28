"""Tests for the ATLAS dispatch service (fake Supabase client, no network)."""

import pytest
from fastapi.testclient import TestClient

from src import atlas_dispatch

API_KEY = "test_atlas_key"
AUTH = {"Authorization": f"Bearer {API_KEY}"}


# ── Fake Supabase client ─────────────────────────────────────
class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, table, client, op, row=None):
        self.table, self.client, self.op, self.row = table, client, op, row
        self.filters = {}

    def eq(self, col, val):
        self.filters[col] = val
        return self

    def select(self, *a, **k):
        return self

    def execute(self):
        self.client.calls.append({"table": self.table, "op": self.op, "row": self.row, "filters": self.filters})
        if self.op in ("insert", "upsert"):
            self.client.n += 1
            return FakeResult([{**(self.row or {}), "id": f"id{self.client.n}"}])
        return FakeResult([])


class FakeTable:
    def __init__(self, name, client):
        self.name, self.client = name, client

    def insert(self, row):
        return FakeQuery(self.name, self.client, "insert", row)

    def upsert(self, row, on_conflict=None):
        return FakeQuery(self.name, self.client, "upsert", row)

    def update(self, row):
        return FakeQuery(self.name, self.client, "update", row)


class FakeSupabase:
    def __init__(self):
        self.calls = []
        self.n = 0

    def table(self, name):
        return FakeTable(name, self)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ATLAS_API_KEY", API_KEY)
    fake = FakeSupabase()
    monkeypatch.setattr(atlas_dispatch, "get_client", lambda: fake)
    tc = TestClient(atlas_dispatch.app)
    tc.fake = fake
    return tc


def _req(task_types, payload=None):
    return {
        "webhook_event_id": "evt_1",
        "source": "github",
        "event_type": "push",
        "task_types": task_types,
        "payload": payload or {},
    }


def test_health_reports_unconfigured(monkeypatch):
    monkeypatch.setattr(atlas_dispatch, "get_client", lambda: None)
    body = TestClient(atlas_dispatch.app).get("/health").json()
    assert body["status"] == "ok"
    assert body["configured"] is False


def test_dispatch_requires_auth(client):
    # Missing bearer token -> 401.
    assert client.post("/api/v1/dispatch", json=_req(["deploy"])).status_code == 401


def test_dispatch_503_when_key_unset(monkeypatch):
    monkeypatch.delenv("ATLAS_API_KEY", raising=False)
    resp = TestClient(atlas_dispatch.app).post("/api/v1/dispatch", json=_req(["deploy"]), headers=AUTH)
    assert resp.status_code == 503


def test_dispatch_503_when_supabase_unavailable(monkeypatch):
    monkeypatch.setenv("ATLAS_API_KEY", API_KEY)
    monkeypatch.setattr(atlas_dispatch, "get_client", lambda: None)
    resp = TestClient(atlas_dispatch.app).post("/api/v1/dispatch", json=_req(["deploy"]), headers=AUTH)
    assert resp.status_code == 503


def test_dispatch_deploy_task(client):
    payload = {"repository": {"name": "apex", "full_name": "Garrettc123/apex"}, "after": "abc123"}
    resp = client.post("/api/v1/dispatch", json=_req(["deploy"], payload), headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tasks_completed"] == ["deploy"]
    assert body["errors"] == []
    # A deployments row was inserted, and webhook_events marked processed.
    tables = [c["table"] for c in client.fake.calls]
    assert "deployments" in tables
    assert any(c["table"] == "webhook_events" and c["row"].get("status") == "processed" for c in client.fake.calls)


def test_dispatch_unknown_task_records_error(client):
    resp = client.post("/api/v1/dispatch", json=_req(["does_not_exist"]), headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tasks_completed"] == []
    assert any("Unknown task" in e for e in body["errors"])
    # webhook_events should be marked failed when there are errors.
    assert any(c["table"] == "webhook_events" and c["row"].get("status") == "failed" for c in client.fake.calls)


def test_dispatch_multiple_financial_tasks(client):
    payload = {"type": "invoice.paid", "data": {"object": {"amount": 5000}}}
    resp = client.post("/api/v1/dispatch", json=_req(["accrual_tax", "sweep_treasury"], payload), headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["tasks_completed"]) == {"accrual_tax", "sweep_treasury"}
    assert body["results"]["sweep_treasury"]["amount_cents"] == 5000
    assert body["results"]["accrual_tax"]["accruals"] == 2
