"""Commercial pricing catalog for APEX Universal AI OS.

This is the single source of truth for the paid plans exposed through the
public API (`GET /pricing`) and referenced by the billing/checkout flow.
Keeping plans in code (rather than hard-coded in the route) means the same
definitions can be reused by the Stripe checkout stub and by tests.

Set the `*_PRICE_ID` environment variables to the corresponding Stripe Price
IDs to make a plan purchasable; plans without a price id are "contact sales".
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Plan:
    """A single purchasable (or contact-sales) commercial plan."""

    id: str
    name: str
    monthly_usd: Optional[float]  # None => custom / contact sales
    description: str
    features: List[str] = field(default_factory=list)
    # Env var that holds the Stripe Price ID for this plan, if any.
    stripe_price_env: Optional[str] = None

    @property
    def stripe_price_id(self) -> Optional[str]:
        """Resolve the Stripe Price ID from the environment, if configured."""
        if not self.stripe_price_env:
            return None
        return os.getenv(self.stripe_price_env) or None

    @property
    def is_purchasable(self) -> bool:
        """A plan is self-serve only when it has a price AND a Stripe id."""
        return self.monthly_usd is not None and self.stripe_price_id is not None

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "monthly_usd": self.monthly_usd,
            "description": self.description,
            "features": list(self.features),
            "purchasable": self.is_purchasable,
            "contact_sales": self.monthly_usd is None,
        }


# ── Catalog ────────────────────────────────────────────────────────────────
# Monthly prices mirror the per-strategy rates in AutonomousRevenueEngine so
# the simulation and the real catalog stay consistent.
PLANS: List[Plan] = [
    Plan(
        id="starter",
        name="Starter",
        monthly_usd=1000.0,
        description="Single-team AI services access with community support.",
        features=[
            "AI services API access",
            "Up to 1M requests / month",
            "Community support",
        ],
        stripe_price_env="STRIPE_PRICE_STARTER",
    ),
    Plan(
        id="growth",
        name="Growth",
        monthly_usd=5000.0,
        description="Production infrastructure with priority support and SLAs.",
        features=[
            "Everything in Starter",
            "Managed infrastructure orchestration",
            "Priority support + 99.9% uptime SLA",
        ],
        stripe_price_env="STRIPE_PRICE_GROWTH",
    ),
    Plan(
        id="scale",
        name="Scale",
        monthly_usd=10000.0,
        description="High-throughput compute for large autonomous workloads.",
        features=[
            "Everything in Growth",
            "Dedicated high-throughput compute",
            "Custom integrations + solutions engineer",
        ],
        stripe_price_env="STRIPE_PRICE_SCALE",
    ),
    Plan(
        id="enterprise",
        name="Enterprise",
        monthly_usd=None,  # custom pricing
        description="Proprietary deployment, custom licensing, and white-glove onboarding.",
        features=[
            "Everything in Scale",
            "Self-hosted / private cloud deployment",
            "Commercial license + indemnification",
            "Dedicated account team",
        ],
        stripe_price_env=None,
    ),
]

_PLANS_BY_ID: Dict[str, Plan] = {p.id: p for p in PLANS}


def get_plan(plan_id: str) -> Optional[Plan]:
    """Return the plan with the given id, or None if it does not exist."""
    return _PLANS_BY_ID.get(plan_id)


def list_plans() -> List[Dict[str, object]]:
    """Return all plans as JSON-serializable dicts (public catalog)."""
    return [p.to_dict() for p in PLANS]
