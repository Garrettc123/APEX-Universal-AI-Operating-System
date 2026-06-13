"""FastAPI routes for the APEX integrations hub.

Namespaced under ``/api/integrations``. Consumed by the Integrations tab in
the native Android app.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from src.integrations_service import IntegrationsService, get_integrations_service

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("")
async def list_integrations(
    svc: IntegrationsService = Depends(get_integrations_service),
) -> List[Dict[str, Any]]:
    """All integrations (connected first), for the hub list."""
    return svc.list()


@router.get("/{integration_id}")
async def get_integration(
    integration_id: str,
    svc: IntegrationsService = Depends(get_integrations_service),
) -> Dict[str, Any]:
    """One integration plus its recent trigger runs."""
    item = svc.get(integration_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Unknown integration")
    return item


@router.post("/{integration_id}/trigger")
async def trigger_integration(
    integration_id: str,
    svc: IntegrationsService = Depends(get_integrations_service),
) -> Dict[str, Any]:
    """Trigger a sync/automation run; returns the run record."""
    run = svc.trigger(integration_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Unknown integration")
    return run
