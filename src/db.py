"""Env-gated Postgres / Supabase persistence layer (fails safe).

This module gives the rest of the app durable storage *when a database is
configured*, and otherwise stays completely out of the way:

  * Every public function is a no-op that returns ``False`` / ``None`` when
    no connection string is set or the ``psycopg`` driver is missing — callers
    simply fall back to their previous behavior (JSON file / in-memory).
  * Connection details come from ``DATABASE_URL`` (preferred) or
    ``SUPABASE_DB_URL``. Both accept a standard Postgres URI.

To enable:
  1. pip install "psycopg[binary]"
  2. supabase start            (or point DATABASE_URL at any Postgres)
  3. apply supabase/migrations/0001_init.sql
  4. export DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def database_url() -> Optional[str]:
    """Return the configured Postgres URI, if any."""
    return os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")


def is_configured() -> bool:
    """True only when a database URL is present in the environment."""
    return bool(database_url())


def _connect():
    """Open a psycopg connection, or return None if unavailable.

    Never raises — a missing driver or unreachable DB degrades to None so the
    caller can fall back instead of crashing a request.
    """
    url = database_url()
    if not url:
        return None
    try:
        import psycopg  # imported lazily so the driver is optional
    except ImportError:
        logger.warning("DATABASE_URL is set but 'psycopg' is not installed; skipping DB write.")
        return None
    try:
        return psycopg.connect(url)
    except Exception as exc:  # pragma: no cover - depends on a live DB
        logger.warning("Could not connect to database: %s", exc)
        return None


def save_revenue_state(total_revenue: float, monthly_revenue: dict) -> bool:
    """Upsert the singleton revenue snapshot. Returns True on success."""
    conn = _connect()
    if conn is None:
        return False
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into revenue_state (id, total_revenue, monthly_revenue, updated_at)
                values (1, %s, %s::jsonb, now())
                on conflict (id) do update
                set total_revenue = excluded.total_revenue,
                    monthly_revenue = excluded.monthly_revenue,
                    updated_at = now()
                """,
                (total_revenue, json.dumps(monthly_revenue)),
            )
        return True
    except Exception as exc:  # pragma: no cover - depends on a live DB
        logger.warning("save_revenue_state failed: %s", exc)
        return False
    finally:
        conn.close()


def load_revenue_state() -> Optional[dict]:
    """Return {'total_revenue': float, 'monthly_revenue': dict} or None."""
    conn = _connect()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("select total_revenue, monthly_revenue from revenue_state where id = 1")
            row = cur.fetchone()
        if not row:
            return None
        return {"total_revenue": float(row[0]), "monthly_revenue": dict(row[1] or {})}
    except Exception as exc:  # pragma: no cover - depends on a live DB
        logger.warning("load_revenue_state failed: %s", exc)
        return None
    finally:
        conn.close()


def record_subscription(customer_id: str, plan_id: Optional[str] = None, status: str = "active") -> bool:
    """Upsert a customer entitlement row. Returns True on success."""
    if not customer_id:
        return False
    conn = _connect()
    if conn is None:
        return False
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into subscriptions (customer_id, plan_id, status, updated_at)
                values (%s, %s, %s, now())
                on conflict (customer_id) do update
                set plan_id = coalesce(excluded.plan_id, subscriptions.plan_id),
                    status = excluded.status,
                    updated_at = now()
                """,
                (customer_id, plan_id, status),
            )
        return True
    except Exception as exc:  # pragma: no cover - depends on a live DB
        logger.warning("record_subscription failed: %s", exc)
        return False
    finally:
        conn.close()


def revoke_subscription(customer_id: str) -> bool:
    """Mark a customer's entitlement as cancelled. Returns True on success."""
    return record_subscription(customer_id, status="cancelled")


def get_subscription(customer_id: str) -> Optional[dict]:
    """Return {'customer_id','plan_id','status'} for a customer, or None."""
    if not customer_id:
        return None
    conn = _connect()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "select customer_id, plan_id, status from subscriptions where customer_id = %s",
                (customer_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {"customer_id": row[0], "plan_id": row[1], "status": row[2]}
    except Exception as exc:  # pragma: no cover - depends on a live DB
        logger.warning("get_subscription failed: %s", exc)
        return None
    finally:
        conn.close()
