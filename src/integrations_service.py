"""APEX Integrations Service.

Models the "everything I own in one place" integrations layer: a registry of
connected services (email, docs, commerce, comms, infra, automation) plus the
ability to trigger a sync/automation run against any of them.

The registry is intentionally backend-owned so the mobile app stays a thin
client — new integrations appear in the app the moment they're added here,
and trigger runs are recorded so the app can show recent activity.
"""

from __future__ import annotations

import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

_ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime(_ISO_FMT)


# Seed registry. Each entry mirrors a real service the user wants merged into
# the APEX control plane. ``connected`` reflects whether credentials exist;
# disconnected ones still render in the app with a "Connect" affordance.
_SEED: List[Dict[str, Any]] = [
    {"id": "gmail", "name": "Gmail", "category": "Email", "connected": True, "automations": 4},
    {"id": "notion", "name": "Notion", "category": "Docs", "connected": True, "automations": 3},
    {"id": "shopify", "name": "Shopify", "category": "Commerce", "connected": True, "automations": 6},
    {"id": "slack", "name": "Slack", "category": "Comms", "connected": True, "automations": 5},
    {"id": "airtable", "name": "Airtable", "category": "Data", "connected": True, "automations": 2},
    {"id": "vercel", "name": "Vercel", "category": "Infra", "connected": True, "automations": 3},
    {"id": "github", "name": "GitHub", "category": "Code", "connected": True, "automations": 7},
    {"id": "stripe", "name": "Stripe", "category": "Payments", "connected": False, "automations": 0},
    {"id": "zapier", "name": "Zapier", "category": "Automation", "connected": True, "automations": 9},
]


class IntegrationsService:
    """In-memory registry of integrations and their recent trigger runs."""

    def __init__(self) -> None:
        self._integrations: Dict[str, Dict[str, Any]] = {}
        for seed in _SEED:
            self._integrations[seed["id"]] = {
                **seed,
                "status": "active" if seed["connected"] else "disconnected",
                "last_sync": _now_iso() if seed["connected"] else None,
            }
        # Bounded activity log, newest first.
        self._runs: Deque[Dict[str, Any]] = deque(maxlen=50)

    def list(self) -> List[Dict[str, Any]]:
        """All integrations, connected first then alphabetical."""
        rows = list(self._integrations.values())
        rows.sort(key=lambda r: (not r["connected"], r["name"].lower()))
        return rows

    def get(self, integration_id: str) -> Optional[Dict[str, Any]]:
        item = self._integrations.get(integration_id)
        if item is None:
            return None
        return {**item, "recent_runs": self._runs_for(integration_id)}

    def trigger(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """Trigger a sync/automation run; returns the run record (or None)."""
        item = self._integrations.get(integration_id)
        if item is None:
            return None
        if not item["connected"]:
            run = {
                "run_id": uuid.uuid4().hex[:12],
                "integration_id": integration_id,
                "status": "skipped",
                "detail": "Integration not connected",
                "started_at": _now_iso(),
            }
        else:
            run = {
                "run_id": uuid.uuid4().hex[:12],
                "integration_id": integration_id,
                "status": "succeeded",
                "detail": f"Synced {item['name']} ({item['automations']} automations)",
                "started_at": _now_iso(),
            }
            item["last_sync"] = run["started_at"]
        self._runs.appendleft(run)
        return run

    def _runs_for(self, integration_id: str) -> List[Dict[str, Any]]:
        return [r for r in self._runs if r["integration_id"] == integration_id][:10]


# Process-wide singleton.
_service: Optional[IntegrationsService] = None


def get_integrations_service() -> IntegrationsService:
    """Return (creating on first use) the shared integrations service."""
    global _service
    if _service is None:
        _service = IntegrationsService()
    return _service
