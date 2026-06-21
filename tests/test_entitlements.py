"""Tests for the entitlement service (in-memory fallback path)."""

import pytest

from src import entitlements


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    # Force the in-memory path and start from a clean store each test.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    entitlements._reset_memory()
    yield
    entitlements._reset_memory()


def test_unknown_customer_has_no_access():
    assert entitlements.get("nobody") is None
    assert entitlements.has_active_access("nobody") is False


def test_grant_then_access():
    assert entitlements.grant("cus_1", plan_id="pro", status="active") is True
    assert entitlements.has_active_access("cus_1") is True
    record = entitlements.get("cus_1")
    assert record == {"customer_id": "cus_1", "plan_id": "pro", "status": "active"}


def test_revoke_removes_access():
    entitlements.grant("cus_2", plan_id="pro")
    entitlements.revoke("cus_2")
    assert entitlements.has_active_access("cus_2") is False
    assert entitlements.get("cus_2")["status"] == "cancelled"


def test_revoke_preserves_plan_id():
    entitlements.grant("cus_3", plan_id="enterprise")
    entitlements.revoke("cus_3")
    # A status-only update must not wipe the known plan.
    assert entitlements.get("cus_3")["plan_id"] == "enterprise"


def test_past_due_is_not_active():
    entitlements.grant("cus_4", status="past_due")
    assert entitlements.has_active_access("cus_4") is False


def test_empty_customer_id_is_rejected():
    assert entitlements.grant("") is False
    assert entitlements.get("") is None
    assert entitlements.has_active_access("") is False
