"""Entitlement service — the read/write layer that closes the payment loop.

Stripe webhooks call :func:`grant` / :func:`revoke` here; the API and any
feature gate call :func:`get` / :func:`has_active_access` to decide whether a
customer may use a paid capability.

Storage is transparent to callers:
  * When a database is configured (``src/db.py``), entitlements live in the
    ``subscriptions`` table and survive restarts / multiple processes.
  * Otherwise they live in an in-process dict so the loop still works end-to-end
    in a single running instance (and in tests) without external services.
"""

import logging
from typing import Dict, Optional

from . import db

logger = logging.getLogger(__name__)

# Statuses that grant access to paid capabilities.
ACTIVE_STATUSES = frozenset({"active", "trialing"})

# In-memory fallback store: customer_id -> {"plan_id", "status"}
_MEMORY: Dict[str, dict] = {}


def grant(customer_id: str, plan_id: Optional[str] = None, status: str = "active") -> bool:
    """Grant or update a customer's entitlement. Returns True on success."""
    if not customer_id:
        return False
    if db.is_configured() and db.record_subscription(customer_id, plan_id=plan_id, status=status):
        return True
    # Fallback: keep the existing plan_id if a later event omits it.
    existing = _MEMORY.get(customer_id, {})
    _MEMORY[customer_id] = {
        "plan_id": plan_id or existing.get("plan_id"),
        "status": status,
    }
    return True


def revoke(customer_id: str) -> bool:
    """Mark a customer's entitlement as cancelled. Returns True on success."""
    return grant(customer_id, status="cancelled")


def get(customer_id: str) -> Optional[dict]:
    """Return {'customer_id','plan_id','status'} for a customer, or None."""
    if not customer_id:
        return None
    if db.is_configured():
        record = db.get_subscription(customer_id)
        if record is not None:
            return record
    entry = _MEMORY.get(customer_id)
    if entry is None:
        return None
    return {"customer_id": customer_id, "plan_id": entry.get("plan_id"), "status": entry.get("status")}


def has_active_access(customer_id: str) -> bool:
    """True if the customer currently holds an access-granting entitlement."""
    record = get(customer_id)
    return bool(record and record.get("status") in ACTIVE_STATUSES)


def _reset_memory() -> None:
    """Clear the in-memory store (test helper)."""
    _MEMORY.clear()
