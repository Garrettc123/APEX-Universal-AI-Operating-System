# ⚡ Garcar Enterprise — ATLAS Automation Hub

Unified event-driven automation spine. Stripe, GitHub, Apollo, and DocuSign
events flow through one ingestion point → ATLAS dispatches to the right task crew.

This spine is integrated into this repo (it coexists with the in-app Stripe
checkout/entitlement path in `app.py`).

---

## 📁 Files in this repo

| Path | Purpose |
|------|---------|
| `supabase/migrations/0002_atlas_schema.sql` | Supabase Postgres — 8 tables, RLS, auto-triggers |
| `supabase/functions/atlas-ingest/index.ts` | Supabase Edge Function — webhook ingestion + ATLAS dispatch |
| `src/atlas_dispatch.py` | FastAPI dispatch service (Railway) — routes ATLAS task crews (env-gated, tested) |
| `.github/workflows/garcar-deploy.yml` | Reusable GHA pipeline (`workflow_call`) |
| `.github/workflows/deploy.yml` | Caller — manual dispatch only, wired to the local reusable pipeline |
| `scripts/garcar.sh` | Termux CLI: `garcar status`, `deploy`, `revenue`, `watch`, etc. |

---

## 🔄 Event Flow

```
Stripe / GitHub / Apollo / DocuSign
         │
         ▼
  atlas-ingest (Supabase Edge Function)
  ├── HMAC verify (Stripe) / header detect (others)
  ├── Idempotent upsert → webhook_events table
  └── EdgeRuntime.waitUntil → POST to ATLAS
         │
         ▼
  atlas-dispatch (Railway / FastAPI — src/atlas_dispatch.py)
  ├── payment_intent.succeeded  → accrual_tax + sweep_treasury + notify
  ├── invoice.paid              → accrual_tax + sweep_treasury
  ├── lead.created (Apollo)     → qualify_lead
  ├── envelope-completed        → activate_subscription + notify
  └── github:push               → deploy log
         │
         ▼
  Supabase tables updated:
  revenue_ledger, tax_accruals, treasury_positions,
  leads, contracts, deployments, atlas_tasks
```

---

## 🚀 Deploy Order

### 1 — Apply Supabase Schema
```bash
supabase db push --project-ref YOUR_PROJECT_REF   # applies supabase/migrations/
```

### 2 — Deploy Edge Function
```bash
supabase functions deploy atlas-ingest --project-ref YOUR_REF --no-verify-jwt
supabase secrets set ATLAS_API_URL=https://your-atlas.railway.app --project-ref YOUR_REF
supabase secrets set ATLAS_API_KEY=$(openssl rand -hex 32) --project-ref YOUR_REF
supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_... --project-ref YOUR_REF
```

### 3 — Deploy ATLAS Dispatch (Railway)
```bash
pip install supabase httpx
# Railway env vars:
#   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ATLAS_API_KEY, NTFY_TOPIC
uvicorn src.atlas_dispatch:app --host 0.0.0.0 --port 8000
```
The service is **safe by default**: without `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
(and the `supabase` package) the dispatch endpoint returns `503` instead of crashing.

### 4 — Wire Stripe Webhooks
```
Stripe Dashboard → Developers → Webhooks → Add endpoint
URL: https://YOUR_PROJECT.supabase.co/functions/v1/atlas-ingest
Events: payment_intent.succeeded, payment_intent.payment_failed,
        customer.subscription.created, invoice.paid
```

### 5 — Deploy pipeline (GitHub Actions)
`deploy.yml` is **manual-dispatch only** and calls the local reusable
`garcar-deploy.yml`, so nothing fires on push and there's no dependency on an
external repo. To enable continuous deploys, add a `push: { branches: [main] }`
trigger and set the secrets listed in `deploy.yml`. For a true multi-repo
fan-out, move `garcar-deploy.yml` to `Garrettc123/garcar-workflows` and point
each caller's `uses:` at it.

### 6 — Install Termux CLI
```bash
cp scripts/garcar.sh $PREFIX/bin/garcar && chmod +x $PREFIX/bin/garcar
garcar setup
echo "source ~/.garcar/credentials" >> ~/.bashrc && source ~/.bashrc
garcar status
```

---

*Garcar Enterprise — Built by Garrett Carroll | garcar.enterprise*
