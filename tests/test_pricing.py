"""Tests for the commercial pricing catalog."""

from src import pricing


def test_list_plans_returns_all_plans():
    plans = pricing.list_plans()
    assert len(plans) == len(pricing.PLANS)
    ids = {p["id"] for p in plans}
    assert {"starter", "growth", "scale", "enterprise"} <= ids


def test_get_plan_known_and_unknown():
    assert pricing.get_plan("starter") is not None
    assert pricing.get_plan("does-not-exist") is None


def test_enterprise_is_contact_sales():
    enterprise = pricing.get_plan("enterprise")
    assert enterprise is not None
    assert enterprise.monthly_usd is None
    assert enterprise.to_dict()["contact_sales"] is True
    assert enterprise.is_purchasable is False


def test_plan_not_purchasable_without_stripe_price(monkeypatch):
    """A priced plan is only purchasable once its Stripe price id is set."""
    monkeypatch.delenv("STRIPE_PRICE_STARTER", raising=False)
    starter = pricing.get_plan("starter")
    assert starter is not None
    assert starter.is_purchasable is False

    monkeypatch.setenv("STRIPE_PRICE_STARTER", "price_123")
    assert starter.stripe_price_id == "price_123"
    assert starter.is_purchasable is True
