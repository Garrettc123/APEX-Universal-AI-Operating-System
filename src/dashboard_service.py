"""APEX Dashboard Service.

A thin, thread-safe service layer that wraps the :class:`APEXOrchestrator`
and exposes a stable, JSON-friendly view of system state for the mobile
command dashboard (and any other client).

The orchestrator's ``run`` loop is long-running and noisy; the mobile app
instead wants to:

* read a snapshot of overall + per-system health, revenue and intelligence
* trigger individual evolution / optimization / revenue cycles on demand

This module provides exactly that as a small async service with a process
-wide singleton, so the FastAPI layer can stay declarative.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.apex_core import APEXOrchestrator, SystemState

# ISO-8601 UTC, e.g. 2026-06-02T12:34:56Z
_ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _iso(dt: datetime) -> str:
    """Render a datetime as a UTC ISO-8601 string the app can parse."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(_ISO_FMT)


class DashboardService:
    """Process-wide, lazily-initialized facade over the orchestrator."""

    def __init__(self) -> None:
        self._orchestrator = APEXOrchestrator()
        self._orchestrator.initialize_repositories()
        self._orchestrator.state = SystemState.ACTIVE
        self._started_at = datetime.now(timezone.utc)
        # Serialize mutations so concurrent requests can't race the engines.
        self._lock = asyncio.Lock()

    # -- read -----------------------------------------------------------------

    def overview(self) -> Dict[str, Any]:
        """High-level KPIs for the dashboard header cards."""
        orch = self._orchestrator
        repos = orch.repositories.values()
        count = len(orch.repositories) or 1

        avg_health = sum(r.health_score for r in repos) / count
        avg_perf = sum(r.metrics.get("performance", 0.0) for r in repos) / count
        healthy = sum(1 for r in repos if r.health_score >= 0.9)

        return {
            "state": orch.state.value,
            "intelligence_level": round(orch.intelligence_level, 6),
            "evolution_cycles": orch.evolution_cycles,
            "systems_total": len(orch.repositories),
            "systems_healthy": healthy,
            "average_health": round(avg_health, 4),
            "average_performance": round(avg_perf, 2),
            "total_revenue": round(orch.revenue_engine.total_revenue, 2),
            "annual_projection": round(orch.revenue_engine.get_annual_projection(), 2),
            "uptime_seconds": int((datetime.now(timezone.utc) - self._started_at).total_seconds()),
            "generated_at": _iso(datetime.now(timezone.utc)),
        }

    def systems(self) -> List[Dict[str, Any]]:
        """Per-system health rows, worst-health first so issues surface."""
        rows = [
            {
                "name": repo.name,
                "status": repo.status,
                "health_score": round(repo.health_score, 4),
                "last_update": _iso(repo.last_update),
                "metrics": {k: round(v, 3) for k, v in repo.metrics.items()},
                "dependencies": repo.dependencies,
            }
            for repo in self._orchestrator.repositories.values()
        ]
        rows.sort(key=lambda r: r["health_score"])
        return rows

    def revenue(self) -> Dict[str, Any]:
        """Revenue breakdown by strategy for the revenue screen/card."""
        engine = self._orchestrator.revenue_engine
        strategies = [
            {
                "name": name,
                "rate": cfg["rate"],
                "clients": cfg["clients"],
                "revenue": round(cfg["clients"] * cfg["rate"], 2),
            }
            for name, cfg in engine.strategies.items()
        ]
        strategies.sort(key=lambda s: s["revenue"], reverse=True)
        return {
            "total_revenue": round(engine.total_revenue, 2),
            "annual_projection": round(engine.get_annual_projection(), 2),
            "strategies": strategies,
        }

    # -- actions --------------------------------------------------------------

    async def trigger_evolution(self) -> Dict[str, Any]:
        async with self._lock:
            await self._orchestrator.evolve()
        return self.overview()

    async def trigger_optimization(self) -> Dict[str, Any]:
        async with self._lock:
            await self._orchestrator.optimize_systems()
        return self.overview()

    async def trigger_revenue_cycle(self) -> Dict[str, Any]:
        async with self._lock:
            await self._orchestrator.generate_revenue_cycle()
        return self.revenue()


# Process-wide singleton. FastAPI dependency-injects this.
_service: DashboardService | None = None


def get_service() -> DashboardService:
    """Return (creating on first use) the shared dashboard service."""
    global _service
    if _service is None:
        _service = DashboardService()
    return _service
