"""ATLAS Dispatch Service — GARCAR ENTERPRISE (env-gated, fail-safe).

FastAPI service that receives routed webhook events from the `atlas-ingest`
Supabase Edge Function and runs the matching task crews, writing results to the
ATLAS Postgres tables (see supabase/migrations/0002_atlas_schema.sql).

Deployable standalone (e.g. Railway):
    uvicorn src.atlas_dispatch:app --host 0.0.0.0 --port 8000

Like the rest of this codebase it is safe by default: the Supabase client is
created lazily and only when ``SUPABASE_URL`` + ``SUPABASE_SERVICE_ROLE_KEY`` are
set and the optional ``supabase`` package is installed. When unconfigured the
dispatch endpoint returns 503 rather than crashing at import time.

Optional dependency: ``pip install supabase httpx``
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="ATLAS Dispatch Engine", version="1.0.0")
security = HTTPBearer(auto_error=False)

_client = None


def get_client():
    """Return a cached Supabase client, or None when unconfigured/unavailable."""
    global _client
    if _client is not None:
        return _client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
    except ImportError:
        logger.warning("SUPABASE_URL set but 'supabase' package not installed; ATLAS dispatch disabled.")
        return None
    _client = create_client(url, key)
    return _client


def atlas_api_key() -> Optional[str]:
    """The bearer key callers must present (the edge function shares it)."""
    return os.getenv("ATLAS_API_KEY")


def ntfy_topic() -> str:
    return os.getenv("NTFY_TOPIC", "garcar-alerts")


def verify(creds: Optional[HTTPAuthorizationCredentials] = Security(security)) -> str:
    """Authn dependency: validate the bearer token against ATLAS_API_KEY."""
    expected = atlas_api_key()
    if not expected:
        raise HTTPException(503, "ATLAS dispatch not configured (ATLAS_API_KEY unset)")
    if creds is None or creds.credentials != expected:
        raise HTTPException(401, "Invalid API key")
    return creds.credentials


class DispatchReq(BaseModel):
    webhook_event_id: str
    source: str
    event_type: str
    task_types: List[str]
    payload: dict


# ── Task Handlers ────────────────────────────────────────────
async def handle_accrual_tax(sb, wid: str, payload: dict) -> dict:
    amount = payload.get("data", {}).get("object", {}).get("amount", 0)
    now = datetime.now(timezone.utc)
    q = (now.month - 1) // 3 + 1
    rows = []
    for jur, bps in [("federal", 2100), ("texas", 0)]:
        r = (
            sb.table("tax_accruals")
            .insert(
                dict(
                    period_year=now.year,
                    period_quarter=q,
                    tax_jurisdiction=jur,
                    taxable_amount=amount,
                    tax_rate_bps=bps,
                    status="accrued",
                )
            )
            .execute()
        )
        rows.append(r.data)
    return {"accruals": len(rows), "amount_cents": amount}


async def handle_sweep_treasury(sb, wid: str, payload: dict) -> dict:
    amount = payload.get("data", {}).get("object", {}).get("amount", 0)
    sb.table("treasury_positions").upsert(
        dict(
            account_name="stripe_primary",
            account_type="stripe",
            balance_cents=amount,
            last_synced_at=datetime.now(timezone.utc).isoformat(),
        ),
        on_conflict="account_name",
    ).execute()
    return {"treasury_updated": True, "amount_cents": amount}


async def handle_qualify_lead(sb, wid: str, payload: dict) -> dict:
    data = dict(
        email=payload.get("email", ""),
        first_name=payload.get("first_name", ""),
        last_name=payload.get("last_name", ""),
        company=payload.get("organization", {}).get("name", ""),
        title=payload.get("title", ""),
        apollo_id=payload.get("id"),
        enrichment_data=payload,
        status="new",
        assigned_agent="lead_qualifier_crew",
    )
    sb.table("leads").upsert(data, on_conflict="apollo_id").execute()
    return {"lead_queued": True, "email": data["email"]}


async def handle_activate_subscription(sb, wid: str, payload: dict) -> dict:
    eid = payload.get("envelopeId", "")
    sb.table("contracts").update(dict(status="completed", signed_at=datetime.now(timezone.utc).isoformat())).eq(
        "docusign_envelope_id", eid
    ).execute()
    return {"contract_completed": True, "envelope_id": eid}


async def handle_deploy(sb, wid: str, payload: dict) -> dict:
    sb.table("deployments").insert(
        dict(
            webhook_event_id=wid,
            repo_name=payload.get("repository", {}).get("name", ""),
            repo_full_name=payload.get("repository", {}).get("full_name", ""),
            branch=payload.get("ref", "refs/heads/main").replace("refs/heads/", ""),
            commit_sha=payload.get("after", ""),
            status="triggered",
            triggered_by=payload.get("pusher", {}).get("name", ""),
            environment="production",
        )
    ).execute()
    return {"deploy_logged": True}


async def handle_notify(sb, wid: str, payload: dict) -> dict:
    import httpx

    amount = payload.get("data", {}).get("object", {}).get("amount", 0)
    etype = payload.get("type", "event")
    async with httpx.AsyncClient() as c:
        await c.post(
            f"https://ntfy.sh/{ntfy_topic()}",
            content=f"⚡ {etype} | ${amount / 100:.2f}",
            headers={"Title": "Garcar ATLAS", "Priority": "default", "Tags": "money_with_wings"},
        )
    return {"notified": True}


HANDLERS = {
    "accrual_tax": handle_accrual_tax,
    "sweep_treasury": handle_sweep_treasury,
    "qualify_lead": handle_qualify_lead,
    "activate_subscription": handle_activate_subscription,
    "deploy": handle_deploy,
    "notify": handle_notify,
}


# ── Dispatch endpoint ────────────────────────────────────────
@app.post("/api/v1/dispatch")
async def dispatch(req: DispatchReq, _: str = Depends(verify)):
    sb = get_client()
    if sb is None:
        raise HTTPException(503, "ATLAS dispatch not configured (Supabase unavailable)")

    results, errors = {}, []
    now = datetime.now(timezone.utc)

    for task_type in req.task_types:
        handler = HANDLERS.get(task_type)
        if not handler:
            errors.append(f"Unknown task: {task_type}")
            continue

        rec = (
            sb.table("atlas_tasks")
            .insert(
                dict(
                    webhook_event_id=req.webhook_event_id,
                    task_type=task_type,
                    crew_agent=f"{task_type}_crew",
                    input_data=req.payload,
                    status="running",
                    started_at=now.isoformat(),
                )
            )
            .execute()
        )
        tid = rec.data[0]["id"] if rec.data else None

        try:
            t0 = asyncio.get_event_loop().time()
            result = await handler(sb, req.webhook_event_id, req.payload)
            ms = int((asyncio.get_event_loop().time() - t0) * 1000)
            if tid:
                sb.table("atlas_tasks").update(
                    dict(
                        status="completed",
                        output_data=result,
                        completed_at=datetime.now(timezone.utc).isoformat(),
                        duration_ms=ms,
                    )
                ).eq("id", tid).execute()
            results[task_type] = result
        except Exception as e:  # noqa: BLE001 - record failure, continue other tasks
            if tid:
                sb.table("atlas_tasks").update(
                    dict(status="failed", error_message=str(e), completed_at=datetime.now(timezone.utc).isoformat())
                ).eq("id", tid).execute()
            errors.append(f"{task_type}: {e}")

    sb.table("webhook_events").update(
        dict(
            status="processed" if not errors else "failed",
            processed_at=datetime.now(timezone.utc).isoformat(),
            error_message="; ".join(errors) or None,
        )
    ).eq("id", req.webhook_event_id).execute()

    return {
        "ok": True,
        "webhook_event_id": req.webhook_event_id,
        "tasks_completed": list(results.keys()),
        "errors": errors,
        "results": results,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "atlas-dispatch", "configured": get_client() is not None}
