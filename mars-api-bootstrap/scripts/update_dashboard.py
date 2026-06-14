#!/usr/bin/env python3
"""Unified Revenue Dashboard updater for the GARCAR / MARS API system.

Pulls live numbers from Stripe (cash), Linear (blockers) and Apollo (outbound
replies), then writes a dated summary block to the Notion dashboard page. Built
to run from GitHub Actions on a daily cron (see dashboard-update.yml).

Design principles:
- Every integration degrades gracefully: a missing/invalid key logs a warning
  and the section is reported as "n/a" rather than crashing the whole run.
- No secrets are hard-coded. Everything comes from environment variables that
  GitHub Actions injects from repository secrets.

Required env (set as GitHub secrets):
    STRIPE_SECRET_KEY            Stripe API key (sk_live_... or sk_test_...)
    LINEAR_API_KEY              Linear personal API key
    LINEAR_TEAM_ID              Linear team UUID (GARCAR: see README)
    NOTION_API_KEY             Notion internal integration token
    NOTION_DASHBOARD_PAGE_ID   Page ID the daily summary is appended to
Optional:
    APOLLO_API_KEY             Apollo.io API key (outbound reply stats)
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("dashboard")

STRIPE_API = "https://api.stripe.com/v1"
LINEAR_API = "https://api.linear.app/graphql"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
HTTP_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Stripe — cash
# ---------------------------------------------------------------------------
def stripe_mrr(secret_key: str) -> dict:
    """Return {'mrr', 'customers', 'failed_payments', 'arr'} from Stripe.

    MRR is computed by summing the monthly-normalized amount of every active
    subscription item.
    """
    auth = (secret_key, "")
    mrr_cents = 0
    customers: set[str] = set()
    starting_after: Optional[str] = None

    while True:
        params = {"status": "active", "limit": 100, "expand[]": "data.customer"}
        if starting_after:
            params["starting_after"] = starting_after
        resp = requests.get(f"{STRIPE_API}/subscriptions", params=params, auth=auth, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        for sub in body.get("data", []):
            cust = sub.get("customer")
            customers.add(cust.get("id") if isinstance(cust, dict) else cust)
            for item in sub.get("items", {}).get("data", []):
                price = item.get("price", {})
                amount = price.get("unit_amount") or 0
                qty = item.get("quantity", 1)
                interval = (price.get("recurring") or {}).get("interval", "month")
                count = (price.get("recurring") or {}).get("interval_count", 1) or 1
                monthly = amount * qty
                if interval == "year":
                    monthly = monthly / (12 * count)
                elif interval == "week":
                    monthly = monthly * 52 / 12 / count
                elif interval == "day":
                    monthly = monthly * 365 / 12 / count
                else:  # month
                    monthly = monthly / count
                mrr_cents += monthly
        if not body.get("has_more"):
            break
        starting_after = body["data"][-1]["id"]

    # Failed/open invoices.
    failed = 0
    inv = requests.get(
        f"{STRIPE_API}/invoices",
        params={"status": "open", "limit": 100},
        auth=auth,
        timeout=HTTP_TIMEOUT,
    )
    if inv.ok:
        failed = sum(1 for i in inv.json().get("data", []) if i.get("attempt_count", 0) > 0)

    mrr = round(mrr_cents / 100, 2)
    return {
        "mrr": mrr,
        "customers": len(customers),
        "failed_payments": failed,
        "arr": round(mrr * 12, 2),
    }


# ---------------------------------------------------------------------------
# Linear — blockers
# ---------------------------------------------------------------------------
def linear_blockers(api_key: str, team_id: str) -> dict:
    """Return {'open_blockers', 'urgent'} for the team's unstarted/started work."""
    query = """
    query Blockers($teamId: String!) {
      team(id: $teamId) {
        issues(
          filter: {
            state: { type: { in: ["unstarted", "started", "backlog"] } }
            priority: { lte: 2, gte: 1 }
          }
          first: 100
        ) {
          nodes { identifier priority title }
        }
      }
    }
    """
    resp = requests.post(
        LINEAR_API,
        json={"query": query, "variables": {"teamId": team_id}},
        headers={"Authorization": api_key, "Content-Type": "application/json"},
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    nodes = payload["data"]["team"]["issues"]["nodes"]
    urgent = [n for n in nodes if n.get("priority") == 1]
    return {"open_blockers": len(nodes), "urgent": len(urgent)}


# ---------------------------------------------------------------------------
# Apollo — outbound (best effort)
# ---------------------------------------------------------------------------
def apollo_replies(api_key: str) -> dict:
    """Return {'replies', 'sent'} from Apollo email analytics (best effort).

    Apollo's analytics surface varies by plan; if the endpoint is unavailable
    this returns n/a rather than failing the run.
    """
    try:
        resp = requests.post(
            "https://api.apollo.io/v1/emailer_campaigns/stats",
            json={"api_key": api_key},
            timeout=HTTP_TIMEOUT,
        )
        if not resp.ok:
            return {"replies": None, "sent": None}
        data = resp.json()
        return {
            "replies": data.get("replied_count"),
            "sent": data.get("delivered_count") or data.get("sent_count"),
        }
    except requests.RequestException as exc:  # pragma: no cover - network
        log.warning("Apollo stats unavailable: %s", exc)
        return {"replies": None, "sent": None}


# ---------------------------------------------------------------------------
# Notion — write the summary
# ---------------------------------------------------------------------------
def notion_append(api_key: str, page_id: str, cash: dict, blockers: dict, outbound: dict) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def money(v) -> str:
        return f"${v:,.2f}" if isinstance(v, (int, float)) else "n/a"

    def num(v) -> str:
        return str(v) if v is not None else "n/a"

    lines = [
        f"CASH — MRR {money(cash.get('mrr'))} · ARR {money(cash.get('arr'))} · "
        f"customers {num(cash.get('customers'))} · failed {num(cash.get('failed_payments'))}",
        f"BLOCKERS — open {num(blockers.get('open_blockers'))} · urgent {num(blockers.get('urgent'))}",
        f"OUTBOUND — replies {num(outbound.get('replies'))} · sent {num(outbound.get('sent'))}",
    ]

    children = [
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": f"📊 Daily sync — {today}"}}]},
        }
    ]
    for line in lines:
        children.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line}}]},
            }
        )

    resp = requests.patch(
        f"{NOTION_API}/blocks/{page_id}/children",
        json={"children": children},
        headers={
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()


def _safe(label: str, fn, *args) -> dict:
    """Run an integration call, logging and swallowing failures."""
    try:
        result = fn(*args)
        log.info("%s: %s", label, result)
        return result
    except Exception as exc:  # noqa: BLE001 - we want full resilience here
        log.warning("%s failed: %s", label, exc)
        return {}


def main() -> int:
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    linear_key = os.getenv("LINEAR_API_KEY")
    team_id = os.getenv("LINEAR_TEAM_ID")
    notion_key = os.getenv("NOTION_API_KEY")
    page_id = os.getenv("NOTION_DASHBOARD_PAGE_ID")
    apollo_key = os.getenv("APOLLO_API_KEY")

    cash = _safe("stripe", stripe_mrr, stripe_key) if stripe_key else {}
    blockers = _safe("linear", linear_blockers, linear_key, team_id) if linear_key and team_id else {}
    outbound = _safe("apollo", apollo_replies, apollo_key) if apollo_key else {}

    if not (notion_key and page_id):
        log.error("NOTION_API_KEY / NOTION_DASHBOARD_PAGE_ID not set — printing only.")
        print({"cash": cash, "blockers": blockers, "outbound": outbound})
        return 0

    try:
        notion_append(notion_key, page_id, cash, blockers, outbound)
        log.info("Notion dashboard updated.")
    except Exception as exc:  # noqa: BLE001
        log.error("Notion update failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
