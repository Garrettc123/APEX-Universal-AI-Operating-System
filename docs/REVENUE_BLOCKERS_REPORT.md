# Revenue Blockers — Status & Prioritized Backlog

_Last updated: 2026-06-13_

This report separates what has been **fixed in this repo** from the **real-world
blockers** that cannot be solved by code alone. The original ask — "fix all
revenue blockers and gain full autonomy" — is partly outside what a code change
can deliver: an AI agent cannot incorporate a company, open a bank account,
charge customers' cards, or become literally self-operating. Those items are
listed honestly below as owner actions, not as things the code now does.

---

## ✅ Cleared in this change (in-repo)

| # | Blocker | Resolution |
|---|---------|------------|
| 1 | No way for a customer to see prices | `GET /pricing` serves a real catalog (`src/pricing.py`) |
| 2 | No payment path | `POST /api/checkout` creates a Stripe Checkout Session (`src/billing.py`), env-gated and fail-safe |
| 3 | No contact method ("Contact Garrett Carroll" with no details) | Email added to README, `/pricing`, and LICENSE |
| 4 | No license terms behind a "commercial licensing" pitch | Proprietary `LICENSE` added (template — see caveat) |
| 5 | Revenue state lost on restart | Optional JSON persistence in `AutonomousRevenueEngine` (`APEX_STATE_FILE`) |
| 6 | API disconnected from the core engine | `app.py` now exposes `/api/status` backed by the revenue engine |
| 7 | Flaky local lint (flake8 fell back to 79 chars) | Native `.flake8` config; 0 errors locally and in CI |
| 8 | Unpinned deps + broken `asyncio` PyPI pin | `requirements.txt` pinned with upper bounds; bogus pin removed |

Test suite: **64 passing** (was 48). CI quality gate (black/isort/flake8/bandit): clean.

---

## 🔴 Real-world blockers (owner action required — cannot be done from code)

Priority order to first dollar:

1. **Live Stripe account + Price IDs.** Code is ready; create products/prices in
   Stripe, then set `STRIPE_SECRET_KEY` and `STRIPE_PRICE_*`. Until then checkout
   correctly returns HTTP 503.
2. **Legal entity + license review.** The bundled `LICENSE` is a template, not
   legal advice. Have counsel review before relying on it; register the entity
   that will hold the contract and receive funds.
3. **Bank account + tax/EIN** so Stripe payouts have a destination.
4. **A public website with the pricing page and a checkout button** wired to
   `POST /api/checkout`. The API exists; the front-end does not.
5. **A deployed, reachable API.** `vercel.json` + `Dockerfile` exist; an actual
   production deployment with a domain and TLS is still required.
6. **Webhook handling for Stripe events** (subscription created / payment
   failed / cancelled) to keep entitlement state correct. Not yet implemented.

---

## ⚠️ Honesty notes

- **"Full autonomy" is not a deliverable.** The `Superintelligence`,
  `UnicornFactory`, and `AutonomousRevenueEngine` modules are **simulations**
  (`numpy` random draws), not real money generation. The `/pricing` + checkout
  path above is the genuine, working revenue mechanism in this repo.
- Revenue figures in `docs/` (e.g. "$10M+/year", "$120K-500K run rate") are
  projections from the business plan, not actuals.
