import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src import billing, pricing
from src.apex_core import AutonomousRevenueEngine

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = FastAPI(title="APEX AI OS", version="1.0.0")

# FIX: Load allowed origins from env var instead of wildcard "*"
# Set ALLOWED_ORIGINS="https://your-domain.com,https://api.your-domain.com" in production
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Single revenue engine instance for status reporting. Persists to disk when
# APEX_STATE_FILE is set in the environment.
revenue_engine = AutonomousRevenueEngine()

# Where contact-sales / enterprise inquiries should go.
CONTACT_SALES = os.getenv("CONTACT_SALES_EMAIL", "gwc2780@gmail.com")


class CheckoutRequest(BaseModel):
    plan_id: str


@app.get("/")
async def root():
    return {"status": "healthy", "service": "APEX AI Operating System"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/pricing")
async def get_pricing():
    """Public commercial pricing catalog."""
    return {
        "currency": "USD",
        "billing_enabled": billing.is_configured(),
        "contact_sales": CONTACT_SALES,
        "plans": pricing.list_plans(),
    }


@app.get("/store", include_in_schema=False)
async def store():
    """Serve the minimal checkout front-end."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/checkout")
async def create_checkout(req: CheckoutRequest):
    """Create a Stripe Checkout Session for a purchasable plan.

    Returns 404 for unknown plans and 503 when billing is not configured or
    the plan is contact-sales only.
    """
    try:
        return billing.create_checkout_session(req.plan_id)
    except billing.UnknownPlan as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except billing.BillingNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Receive and process Stripe webhook events.

    Returns 503 when webhooks are not configured and 400 when signature
    verification fails.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = billing.verify_webhook(payload, sig_header)
    except billing.BillingNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except billing.WebhookError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return billing.handle_event(event)


@app.get("/api/status")
async def status():
    """Operational + revenue snapshot of the running system."""
    return {
        "status": "healthy",
        "service": "APEX AI Operating System",
        "version": app.version,
        "revenue": {
            "total_usd": revenue_engine.total_revenue,
            "annual_projection_usd": revenue_engine.get_annual_projection(),
            "persistence_enabled": revenue_engine.state_file is not None,
        },
        "billing_enabled": billing.is_configured(),
    }


# NOTE: Entrypoint is in main.py - no duplicate uvicorn block here
