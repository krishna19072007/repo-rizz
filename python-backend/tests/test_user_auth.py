"""
Tests for normal-user (non-admin) Supabase login plumbing:

- the /login page (GitHub OAuth + email/password UI)
- the shared frontend auth bootstrap (frontend/auth.js) on every page
- the publishable config endpoint (/api/config/supabase)
- the CSP change that lets the browser reach Supabase Auth

Rizz Master admin auth is covered in test_admin_api.py — the two
authentication systems must stay separate.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

URL = "https://project.supabase.co"
ANON = "pk_test_anon_key_123"
SERVICE_SECRET = "svc_role_secret_never_served"

PAGES = ["/", "/about", "/analyze", "/compare", "/history", "/contributors", "/contributors/admin", "/signup"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Hermetic: never depend on the operator's real .env.local values."""
    for key in [
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture()
def client():
    return TestClient(app)


def _configure(monkeypatch):
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_URL", URL)
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", ANON)


# ---------------------------------------------------------------------------
# /login page
# ---------------------------------------------------------------------------

def test_login_page_served_with_ui_and_no_store(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert r.headers.get("cache-control") == "no-store"
    html = r.text
    assert "CONTINUE WITH GITHUB" in html
    assert "github-btn" in html
    assert "login-form" in html
    assert "SIGN IN" in html
    assert 'href="/signup' in html  # cross-link to account creation
    assert "/static/auth.js" in html
    assert "supabase-js@2.115.0" in html  # the client library is pinned
    assert "logout-btn" in html
    # Admin auth must stay completely separate from this page.
    for forbidden in ["rizz_master_session", "RIZZ_MASTER_CODE", "service_role", "service-role"]:
        assert forbidden not in html, f"login page must not mention {forbidden}"


def test_signup_page_served_with_ui_and_no_store(client):
    r = client.get("/signup")
    assert r.status_code == 200
    assert r.headers.get("cache-control") == "no-store"
    html = r.text
    assert "CREATE ACCOUNT" in html
    assert "signup-form" in html
    assert "confirm-input" in html          # confirm-password field
    assert "CONTINUE WITH GITHUB" in html
    assert "Already have an account" in html
    assert 'href="/login' in html           # cross-link to sign-in


def test_login_page_never_embeds_the_anon_key(client, monkeypatch):
    _configure(monkeypatch)
    # The key is fetched at runtime from /api/config/supabase; the static
    # HTML must not contain it even when the env var is set.
    assert ANON not in client.get("/login").text


def test_login_page_mentions_rizz_master_separation(client):
    # Normal users and the Rizz Master admin panel are different areas.
    assert "Rizz Master" in client.get("/login").text


# ---------------------------------------------------------------------------
# Shared bootstrap across all pages
# ---------------------------------------------------------------------------

def test_all_pages_bootstrap_supabase_auth(client):
    # The OAuth callback returns to window.location.origin, which can be ANY
    # page — every page must restore the session, not just /login.
    for page in PAGES:
        html = client.get(page).text
        assert 'src="https://unpkg.com/@supabase/supabase-js@2.115.0/dist/umd/supabase.js"' in html, page
        assert 'src="/static/auth.js"' in html, page


def test_auth_js_is_served_and_safe(client):
    r = client.get("/static/auth.js")
    assert r.status_code == 200
    js = r.text
    assert "createClient" in js
    assert "signInWithOAuth" in js
    assert 'provider: "github"' in js
    assert "signOut" in js
    assert "authHeaders" in js          # server calls carry the real token
    assert "gate" in js                 # analysis/history gate helper
    assert "LOGIN TO" in js             # prompt copy
    assert "service_role" not in js and "SERVICE_ROLE" not in js


# ---------------------------------------------------------------------------
# Publishable config endpoint
# ---------------------------------------------------------------------------

def test_config_disabled_when_env_missing(client):
    r = client.get("/api/config/supabase")
    assert r.status_code == 200
    assert r.json() == {"enabled": False, "url": "", "anonKey": ""}


def test_config_returns_only_publishable_fields(client, monkeypatch):
    _configure(monkeypatch)
    r = client.get("/api/config/supabase")
    assert r.status_code == 200
    assert r.json() == {"enabled": True, "url": URL, "anonKey": ANON}


def test_config_never_leaks_service_role_key(client, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", SERVICE_SECRET)
    text = client.get("/api/config/supabase").text
    assert SERVICE_SECRET not in text
    assert "service_role" not in text
    assert "svc" not in text.lower()


# ---------------------------------------------------------------------------
# CSP lets the browser reach Supabase Auth (and only when configured)
# ---------------------------------------------------------------------------

def test_csp_connect_src_includes_supabase_when_configured(client, monkeypatch):
    _configure(monkeypatch)
    csp = client.get("/login").headers.get("content-security-policy", "")
    assert f"connect-src 'self' https://api.github.com {URL}" in csp
    assert "frame-ancestors 'none'" in csp  # existing policy intact


def test_csp_omits_supabase_when_not_configured(client):
    csp = client.get("/login").headers.get("content-security-policy", "")
    assert URL not in csp
    assert "connect-src 'self' https://api.github.com;" in csp


# ---------------------------------------------------------------------------
# Protected history API (server-side session verification + per-user rows)
# ---------------------------------------------------------------------------

def test_history_requires_bearer_token(client):
    # No session -> 401 before any network/store call happens.
    assert client.get("/api/history").status_code == 401
    assert client.post("/api/history", json={"owner": "o", "name": "n", "score": 50}).status_code == 401
    assert client.delete("/api/history/abc").status_code == 401


def test_history_rejects_malformed_bearer(client, monkeypatch):
    # A present-but-malformed header must not reach the store either.
    monkeypatch.setattr("user_history._verify_user", lambda token: (_ for _ in ()).throw(Exception("must not be called")))
    r = client.get("/api/history", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401
