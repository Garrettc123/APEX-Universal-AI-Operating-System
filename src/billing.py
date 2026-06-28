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

import logging
import os
from typing import Optional

from . import entitlements
from .pricing import Plan, get_plan

logger = logging.getLogger(__name__)


class BillingError(Exception):
    """Base class for billing errors."""


class BillingNotConfigured(BillingError):
    """Raised when Stripe is not set up (no key / package / price id)."""


class UnknownPlan(BillingError):
    """Raised when a checkout is requested for a plan that does not exist."""


class WebhookError(BillingError):
    """Raised when a Stripe webhook payload fails verification/parsing."""


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


# ── Webhooks ─────────────────────────────────────────────────────────────────
# Stripe notifies us asynchronously about payment lifecycle events. The handler
# below verifies the signature (when STRIPE_WEBHOOK_SECRET is set) and routes a
# handful of events. handle_event() takes an already-parsed dict so it is fully
# testable without the stripe package or a live signature.

# Events we explicitly act on. Anything else is acknowledged but ignored.
HANDLED_EVENTS = {
    "checkout.session.completed",
    "invoice.paid",
    "invoice.payment_failed",
    "customer.subscription.deleted",
}


def webhook_configured() -> bool:
    """True only when a webhook signing secret is present in the environment."""
    return bool(os.getenv("STRIPE_WEBHOOK_SECRET"))


def verify_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify a raw Stripe webhook payload and return the parsed event dict.

    Raises:
        BillingNotConfigured: no signing secret or the stripe package missing.
        WebhookError: signature/payload verification failed.
    """
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise BillingNotConfigured("Webhooks are not configured. Set STRIPE_WEBHOOK_SECRET to enable them.")

    try:
        import stripe  # imported lazily so the package is optional
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise BillingNotConfigured("The 'stripe' package is not installed. Run: pip install stripe") from exc

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except Exception as exc:  # stripe raises SignatureVerificationError / ValueError
        raise WebhookError(f"Webhook verification failed: {exc}") from exc

    return dict(event)


def handle_event(event: dict) -> dict:
    """Route a parsed Stripe event. Returns a small ack dict.

    This is deliberately side-effect-light: it logs and reports what it would
    act on. Wire real entitlement/state changes into the branches below.
    """
    event_type = event.get("type", "")
    data_object = (event.get("data") or {}).get("object") or {}

    if event_type not in HANDLED_EVENTS:
        logger.info("Ignoring unhandled Stripe event: %s", event_type)
        return {"status": "ignored", "type": event_type}

    customer = data_object.get("customer")

    if event_type == "checkout.session.completed":
        # A customer finished checkout — grant access.
        logger.info("Checkout completed: customer=%s", customer)
        entitlements.grant(customer, status="active")
    elif event_type == "invoice.paid":
        logger.info("Invoice paid: %s", data_object.get("id"))
        entitlements.grant(customer, status="active")
    elif event_type == "invoice.payment_failed":
        # Payment failed — flag the account / start dunning.
        logger.warning("Payment failed: customer=%s", customer)
        entitlements.grant(customer, status="past_due")
    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled — revoke access.
        logger.info("Subscription cancelled: customer=%s", customer)
        entitlements.revoke(customer)

    return {"status": "handled", "type": event_type}
