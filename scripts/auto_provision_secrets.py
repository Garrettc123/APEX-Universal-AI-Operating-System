#!/usr/bin/env python3
"""Auto-provision GitHub Actions secrets for this repository.

Reads secret values from (in order of precedence):
  1. --env-file <path> (KEY=VALUE lines, `#` comments allowed)
  2. Process environment variables

Encrypts each value with the repo's libsodium public key and PUTs it to
`/repos/{owner}/{repo}/actions/secrets/{name}` using a GitHub token.

Required secrets (from .github/workflows/deploy.yml) are provisioned when
present; missing ones are reported and skipped (non-zero exit unless
`--allow-missing`).

Usage:
    export GH_TOKEN=ghp_xxx   # needs `repo` scope (Actions: write)
    python scripts/auto_provision_secrets.py \
        --repo Garrettc123/APEX-Universal-AI-Operating-System \
        --env-file .env.deploy

Requires: requests, pynacl
"""
from __future__ import annotations

import argparse
import os
import sys
from base64 import b64encode
from pathlib import Path

REQUIRED_SECRETS = [
    "RAILWAY_TOKEN",
    "SUPABASE_ACCESS_TOKEN",
    "SUPABASE_PROJECT_ID",
    "SUPABASE_DB_URL",
    "ATLAS_INGEST_URL",
    "ATLAS_API_KEY",
    "ECR_REGISTRY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION",
]

GITHUB_API = "https://api.github.com"


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            values[key] = val
    return values


def encrypt(public_key_b64: str, secret_value: str) -> str:
    from nacl import encoding, public

    pk = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed = public.SealedBox(pk).encrypt(secret_value.encode("utf-8"))
    return b64encode(sealed).decode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/repo")
    ap.add_argument("--env-file", type=Path, default=None)
    ap.add_argument("--token", default=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    ap.add_argument("--allow-missing", action="store_true")
    ap.add_argument("--only", nargs="*", default=None, help="Restrict to a subset of secret names")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.token:
        print("error: GH_TOKEN/GITHUB_TOKEN not set and --token not given", file=sys.stderr)
        return 2

    import requests

    sources: dict[str, str] = {}
    if args.env_file:
        if not args.env_file.exists():
            print(f"error: env file not found: {args.env_file}", file=sys.stderr)
            return 2
        sources.update(load_env_file(args.env_file))
    for k in REQUIRED_SECRETS:
        if k in os.environ and k not in sources:
            sources[k] = os.environ[k]

    targets = args.only or REQUIRED_SECRETS
    missing = [k for k in targets if not sources.get(k)]
    if missing:
        print(f"missing: {', '.join(missing)}", file=sys.stderr)
        if not args.allow_missing:
            return 1

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {args.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    pk_resp = session.get(f"{GITHUB_API}/repos/{args.repo}/actions/secrets/public-key", timeout=30)
    pk_resp.raise_for_status()
    pk = pk_resp.json()
    key_id, public_key = pk["key_id"], pk["key"]

    exit_code = 0
    for name in targets:
        val = sources.get(name)
        if not val:
            continue
        if args.dry_run:
            print(f"DRY-RUN would set {name} (len={len(val)})")
            continue
        payload = {"encrypted_value": encrypt(public_key, val), "key_id": key_id}
        r = session.put(
            f"{GITHUB_API}/repos/{args.repo}/actions/secrets/{name}",
            json=payload,
            timeout=30,
        )
        if r.status_code in (201, 204):
            print(f"set {name}")
        else:
            print(f"FAIL {name}: {r.status_code} {r.text}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
