"""Tests for the env-gated DB layer (no live database required)."""

from src import db


def test_not_configured_without_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    assert db.is_configured() is False
    assert db.database_url() is None


def test_configured_with_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
    assert db.is_configured() is True


def test_writes_are_safe_noops_when_unconfigured(monkeypatch):
    """All write helpers must return False (never raise) without a DB."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    assert db.save_revenue_state(100.0, {"2026-01": 100.0}) is False
    assert db.record_subscription("cus_1") is False
    assert db.revoke_subscription("cus_1") is False
    assert db.load_revenue_state() is None


def test_connect_returns_none_when_unconfigured(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    assert db._connect() is None


def test_record_subscription_rejects_empty_customer(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
    # Empty customer id is rejected before any connection attempt.
    assert db.record_subscription("") is False
