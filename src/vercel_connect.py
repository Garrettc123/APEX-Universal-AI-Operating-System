"""Vercel Connect helper — read scoped third-party tokens (env-gated, fail-safe).

This is the Python equivalent of the ``@vercel/connect`` ``getToken()`` flow
documented by the ``vercel-connect`` skill (its "HTTP API → Python Example").
Because this project is Python/FastAPI rather than a Node app, we consume a
Vercel Connect connector (e.g. ``github/acme-github``) over the HTTP API instead
of the TypeScript SDK.

It exchanges the project's **Vercel OIDC token** (``VERCEL_OIDC_TOKEN`` — pulled
by ``vercel env pull`` locally, or injected automatically at runtime on Vercel)
for a short-lived token scoped to a connector.

Like the rest of this codebase, it is safe by default: with no OIDC token in the
environment, every call returns ``None`` so callers can fall back instead of
crashing. No network call is made unless a token is present.

Example::

    from src import vercel_connect

    # App-scoped GitHub token from the `github/acme-github` connector.
    token = vercel_connect.get_token("github/acme-github")
    if token:
        # use it as: Authorization: Bearer <token>
        ...
"""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import List, Optional

logger = logging.getLogger(__name__)

# Override for testing / self-hosted Vercel API endpoints.
API_BASE = os.getenv("VERCEL_CONNECT_API_BASE", "https://api.vercel.com/v1/connect/token")


def oidc_token() -> Optional[str]:
    """Return the project's Vercel OIDC token, if present."""
    return os.getenv("VERCEL_OIDC_TOKEN")


def is_configured() -> bool:
    """True only when a Vercel OIDC token is available to exchange."""
    return bool(oidc_token())


def _request(url: str, payload: dict, oidc: str, timeout: float) -> dict:  # pragma: no cover - network
    """POST the token-exchange request and return the parsed JSON body."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Authorization": f"Bearer {oidc}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - https URL asserted below
        return json.loads(resp.read().decode("utf-8"))


def get_token(
    connector: str,
    subject_type: str = "app",
    subject_id: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    timeout: float = 10.0,
) -> Optional[str]:
    """Exchange the Vercel OIDC token for a connector-scoped token.

    Args:
        connector: connector id, e.g. ``github/acme-github``.
        subject_type: ``"app"`` (act as the app) or ``"user"`` (on behalf of a
            user — requires ``subject_id``).
        subject_id: end-user id, required when ``subject_type`` is ``"user"``.
        scopes: optional list of scopes to request.
        timeout: network timeout in seconds.

    Returns:
        The scoped token string, or ``None`` if unconfigured or the exchange
        fails (never raises).
    """
    oidc = oidc_token()
    if not oidc or not connector:
        return None

    url = f"{API_BASE}/{connector}"
    if not url.startswith("https://"):
        logger.warning("Refusing non-HTTPS Vercel Connect endpoint: %s", url)
        return None

    subject: dict = {"type": subject_type}
    if subject_id:
        subject["id"] = subject_id
    payload: dict = {"subject": subject}
    if scopes:
        payload["scopes"] = scopes

    try:
        body = _request(url, payload, oidc, timeout)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        logger.warning("Vercel Connect token exchange failed for %s: %s", connector, exc)
        return None

    return (body or {}).get("token")
