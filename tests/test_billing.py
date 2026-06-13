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
