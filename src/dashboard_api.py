"""FastAPI routes powering the APEX mobile command dashboard.

All routes are namespaced under ``/api`` and return plain JSON consumed by
the native Android client (see ``android/``). Read endpoints are cheap
snapshots; the ``/cycle/*`` endpoints trigger a single orchestrator cycle.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from src.dashboard_service import DashboardService, get_service

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/overview")
async def overview(svc: DashboardService = Depends(get_service)) -> Dict[str, Any]:
    """KPI snapshot for the dashboard header (health, revenue, intelligence)."""
    return svc.overview()


@router.get("/systems")
async def systems(svc: DashboardService = Depends(get_service)) -> List[Dict[str, Any]]:
    """Per-system health rows, worst first."""
    return svc.systems()


@router.get("/revenue")
async def revenue(svc: DashboardService = Depends(get_service)) -> Dict[str, Any]:
    """Revenue totals and per-strategy breakdown."""
    return svc.revenue()


@router.post("/cycle/evolve")
async def evolve(svc: DashboardService = Depends(get_service)) -> Dict[str, Any]:
    """Run one self-evolution cycle; returns the refreshed overview."""
    return await svc.trigger_evolution()


@router.post("/cycle/optimize")
async def optimize(svc: DashboardService = Depends(get_service)) -> Dict[str, Any]:
    """Run one optimization pass; returns the refreshed overview."""
    return await svc.trigger_optimization()


@router.post("/cycle/revenue")
async def revenue_cycle(svc: DashboardService = Depends(get_service)) -> Dict[str, Any]:
    """Run one revenue-generation cycle; returns the refreshed revenue view."""
    return await svc.trigger_revenue_cycle()
