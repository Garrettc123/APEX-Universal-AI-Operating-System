"""Tests for the Vercel Connect helper (no network required)."""

import pytest

from src import vercel_connect


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("VERCEL_OIDC_TOKEN", raising=False)
    yield


def test_not_configured_without_oidc_token():
    assert vercel_connect.is_configured() is False
    assert vercel_connect.oidc_token() is None


def test_get_token_returns_none_when_unconfigured():
    # No OIDC token -> no network call, safe None.
    assert vercel_connect.get_token("github/acme-github") is None


def test_get_token_requires_connector(monkeypatch):
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc_abc")
    assert vercel_connect.get_token("") is None


def test_get_token_success(monkeypatch):
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc_abc")
    captured = {}

    def fake_request(url, payload, oidc, timeout):
        captured.update(url=url, payload=payload, oidc=oidc)
        return {"token": "ghs_live_123", "connector": "github/acme-github"}

    monkeypatch.setattr(vercel_connect, "_request", fake_request)

    token = vercel_connect.get_token("github/acme-github")
    assert token == "ghs_live_123"
    assert captured["url"].endswith("/github/acme-github")
    assert captured["url"].startswith("https://")
    assert captured["payload"] == {"subject": {"type": "app"}}
    assert captured["oidc"] == "oidc_abc"


def test_get_token_user_subject_and_scopes(monkeypatch):
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc_abc")
    captured = {}

    def fake_request(url, payload, oidc, timeout):
        captured.update(payload=payload)
        return {"token": "t"}

    monkeypatch.setattr(vercel_connect, "_request", fake_request)

    vercel_connect.get_token("github/acme-github", subject_type="user", subject_id="user_42", scopes=["repo"])
    assert captured["payload"] == {"subject": {"type": "user", "id": "user_42"}, "scopes": ["repo"]}


def test_get_token_swallows_request_errors(monkeypatch):
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc_abc")

    def boom(*args, **kwargs):
        raise OSError("network down")

    monkeypatch.setattr(vercel_connect, "_request", boom)
    assert vercel_connect.get_token("github/acme-github") is None
