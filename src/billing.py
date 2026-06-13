"""Stripe Checkout integration (env-gated, fails safe).

This module turns a pricing plan into a Stripe Checkout Session so customers
can actually pay. It is intentionally *safe by default*:

  * No live network call happens unless STRIPE_SECRET_KEY is set AND the
    `stripe` package is installed.
  * When billing is not configured, `create_checkout_session` raises
    `BillingNotConfigured`, which the API layer maps to HTTP 503 with a clear
    "contact sales" message instead of a 500.

To go live:
  1. pip install stripe
  2. export STRIPE_SECRET_KEY=sk_live_...           (or sk_test_... for testing)
  3. export STRIPE_PRICE_STARTER / _GROWTH / _SCALE  (Stripe Price IDs)
  4. (optional) export CHECKOUT_SUCCESS_URL / CHECKOUT_CANCEL_URL
"""

import os
from typing import Optional

from .pricing import Plan, get_plan


class BillingError(Exception):
    """Base class for billing errors."""


class BillingNotConfigured(BillingError):
    """Raised when Stripe is not set up (no key / package / price id)."""


class UnknownPlan(BillingError):
    """Raised when a checkout is requested for a plan that does not exist."""


def is_configured() -> bool:
    """True only when a Stripe secret key is present in the environment."""
    return bool(os.getenv("STRIPE_SECRET_KEY"))


def _success_url() -> str:
    return os.getenv("CHECKOUT_SUCCESS_URL", "https://example.com/success")


def _cancel_url() -> str:
    return os.getenv("CHECKOUT_CANCEL_URL", "https://example.com/cancel")


def create_checkout_session(plan_id: str) -> dict:
    """Create a Stripe Checkout Session for the given plan id.

    Returns a dict with at least ``id`` and ``url`` (the hosted checkout page).
    Raises:
        UnknownPlan: the plan id is not in the catalog.
        BillingNotConfigured: Stripe key/package/price id is missing, or the
            plan is contact-sales only.
    """
    plan: Optional[Plan] = get_plan(plan_id)
    if plan is None:
        raise UnknownPlan(f"Unknown plan: {plan_id!r}")

    if plan.monthly_usd is None:
        raise BillingNotConfigured(f"Plan '{plan.id}' is contact-sales only and cannot be purchased self-serve.")

    if not is_configured():
        raise BillingNotConfigured("Stripe is not configured. Set STRIPE_SECRET_KEY to enable checkout.")

    price_id = plan.stripe_price_id
    if not price_id:
        raise BillingNotConfigured(f"No Stripe Price ID configured for plan '{plan.id}' " f"(set {plan.stripe_price_env}).")

    try:
        import stripe  # imported lazily so the package is optional
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise BillingNotConfigured("The 'stripe' package is not installed. Run: pip install stripe") from exc

    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=_success_url(),
        cancel_url=_cancel_url(),
    )
    return {"id": session["id"], "url": session["url"], "plan": plan.id}
