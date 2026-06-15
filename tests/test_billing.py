"""Tests for the env-gated Stripe checkout layer."""

import pytest

from src import billing


def test_unknown_plan_raises(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    with pytest.raises(billing.UnknownPlan):
        billing.create_checkout_session("nope")


def test_contact_sales_plan_not_purchasable(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    with pytest.raises(billing.BillingNotConfigured):
        billing.create_checkout_session("enterprise")


def test_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    assert billing.is_configured() is False
    with pytest.raises(billing.BillingNotConfigured):
        billing.create_checkout_session("starter")


def test_missing_price_id_raises(monkeypatch):
    """Key present but no Stripe Price ID for the plan => not configured."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.delenv("STRIPE_PRICE_STARTER", raising=False)
    with pytest.raises(billing.BillingNotConfigured):
        billing.create_checkout_session("starter")


def test_webhook_not_configured(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    assert billing.webhook_configured() is False
    with pytest.raises(billing.BillingNotConfigured):
        billing.verify_webhook(b"{}", "sig")


def test_handle_event_handled():
    result = billing.handle_event({"type": "checkout.session.completed", "data": {"object": {"customer": "cus_1"}}})
    assert result == {"status": "handled", "type": "checkout.session.completed"}


def test_handle_event_payment_failed():
    result = billing.handle_event({"type": "invoice.payment_failed", "data": {"object": {"customer": "cus_2"}}})
    assert result["status"] == "handled"


def test_handle_event_ignored():
    result = billing.handle_event({"type": "some.other.event", "data": {"object": {}}})
    assert result == {"status": "ignored", "type": "some.other.event"}
