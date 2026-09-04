"""
Security tests for the Rizz Master admin API.

Covers: authentication, rate limiting, sessions, logout, CSRF,
authorization bypass attempts, input validation, and image uploads.

Env vars are set BEFORE importing main so the app boots with a known
RIZZ_MASTER_CODE and an isolated test database.
"""

import os
import time

os.environ["RIZZ_MASTER_CODE"] = "test-rizz-code"
os.environ["COOKIE_SECURE"] = "false"

import pytest
from fastapi.testclient import TestClient

from admin_auth import SESSION_COOKIE, sessions, login_rate_limiter
from contributors_store import reset_store_cache
from main import app

CODE = "test-rizz-code"
VALID_PAYLOAD = {
    "github_username": "octocat",
    "display_name": "Octo Cat",
    "role": "Core Engineer",
    "description": "Builds things.",
    "github_url": "https://github.com/octocat",
    "display_order": 0,
}

# Minimal valid PNG: signature + enough bytes to pass the sniffer.
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
NOT_IMAGE = b"this is definitely not an image file...." + b"x" * 64


@pytest.fixture(autouse=True)
def clean_state(tmp_path, monkeypatch):
    """Isolate sessions, rate limiter, and the database for every test."""
    # Tests must stay hermetic: force the SQLite store even when the
    # operator's .env configures Supabase (never hit a live database).
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.setenv("CONTRIBUTORS_DB_PATH", str(tmp_path / "test.db"))
    reset_store_cache()
    sessions.clear()
    login_rate_limiter.reset()
    yield
    reset_store_cache()
    sessions.clear()
    login_rate_limiter.reset()


@pytest.fixture()
def client():
    return TestClient(app)


def login(client, code=CODE):
    """Log in and return the CSRF token."""
    res = client.post("/api/admin/login", json={"code": code})
    assert res.status_code == 200, res.text
    return res.json()["csrf_token"]


def auth_headers(csrf):
    return {"X-CSRF-Token": csrf}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def test_login_success_creates_httponly_session_cookie(client):
    res = client.post("/api/admin/login", json={"code": CODE})
    assert res.status_code == 200
    body = res.json()
    assert body["authenticated"] is True
    assert body["csrf_token"]
    # Cookie must be HttpOnly and SameSite=Lax (not readable by JS)
    set_cookie = res.headers.get("set-cookie", "")
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()
    assert "rizz_master_session" in set_cookie


def test_login_wrong_code_returns_generic_error(client):
    res = client.post("/api/admin/login", json={"code": "not-the-code"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials."
    assert "not-the-code" not in res.text  # never echo the attempt


def test_login_unconfigured_returns_503(client, monkeypatch):
    monkeypatch.delenv("RIZZ_MASTER_CODE", raising=False)
    res = client.post("/api/admin/login", json={"code": "anything"})
    assert res.status_code == 503


def test_login_rate_limited_after_repeated_failures(client):
    # 5 failures then block
    for _ in range(5):
        res = client.post("/api/admin/login", json={"code": "wrong"})
        assert res.status_code == 401
    res = client.post("/api/admin/login", json={"code": CODE})
    assert res.status_code == 429  # even the CORRECT code is rejected


def test_login_success_resets_failures(client):
    for _ in range(4):
        client.post("/api/admin/login", json={"code": "wrong"})
    assert client.post("/api/admin/login", json={"code": CODE}).status_code == 200
    # After success the counter resets — one more wrong attempt is 401 not 429
    assert client.post("/api/admin/login", json={"code": "wrong"}).status_code == 401


def test_rate_limit_global_cap_blocks_even_with_ip_rotation(monkeypatch):
    # Even if an attacker rotates identities, the total number of failures
    # in the window is capped globally, so login is blocked for everyone.
    from admin_auth import login_rate_limiter
    for i in range(20):
        login_rate_limiter.record_failure(f"10.0.0.{i}")
    assert login_rate_limiter.blocked("10.0.0.99") is True
    login_rate_limiter.reset()


def test_rate_limit_cannot_be_bypassed_with_spoofed_forwarded_for(client):
    # X-Forwarded-For must NOT be trusted by default: spoofing it with
    # different IPs must not reset the failure counter.
    for i in range(5):
        res = client.post(
            "/api/admin/login",
            json={"code": "wrong"},
            headers={"X-Forwarded-For": f"10.0.0.{i}"},
        )
        assert res.status_code == 401
    res = client.post(
        "/api/admin/login",
        json={"code": CODE},
        headers={"X-Forwarded-For": "10.0.0.99"},
    )
    assert res.status_code == 429


def test_me_reports_authenticated(client):
    assert client.get("/api/admin/me").json() == {"authenticated": False}
    csrf = login(client)
    body = client.get("/api/admin/me").json()
    assert body["authenticated"] is True
    assert body["csrf_token"] == csrf


def test_logout_invalidates_session(client):
    csrf = login(client)
    res = client.post("/api/admin/logout")
    assert res.status_code == 200
    assert client.get("/api/admin/me").json() == {"authenticated": False}
    # Old session token must be rejected after logout
    client.cookies.set(SESSION_COOKIE, client.cookies.get(SESSION_COOKIE) or "stale")
    assert client.get("/api/admin/me").json() == {"authenticated": False}


def test_expired_session_rejected(client):
    login(client)
    token = client.cookies.get(SESSION_COOKIE)
    sessions._sessions[token]["expires_at"] = time.time() - 10
    res = client.post(
        "/api/admin/contributors",
        json=VALID_PAYLOAD,
        headers=auth_headers("whatever"),
    )
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Authorization — every bypass attempt must fail
# ---------------------------------------------------------------------------

def test_anonymous_mutations_rejected(client):
    assert client.post("/api/admin/contributors", json=VALID_PAYLOAD).status_code == 401
    assert client.put("/api/admin/contributors/1", json=VALID_PAYLOAD).status_code == 401
    assert client.delete("/api/admin/contributors/1").status_code == 401
    assert (
        client.post(
            "/api/admin/contributors/1/image",
            files={"image": ("a.png", PNG_BYTES, "image/png")},
        ).status_code
        == 401
    )


def test_fake_admin_flag_does_not_grant_access(client):
    payload = {**VALID_PAYLOAD, "isAdmin": True}
    # 422 (extra field rejected) or 401 (no session) — either way: no access.
    res = client.post("/api/admin/contributors", json=payload)
    assert res.status_code in (401, 422)


def test_fake_cookie_rejected(client):
    client.cookies.set(SESSION_COOKIE, "forged-token-value")
    assert client.post("/api/admin/contributors", json=VALID_PAYLOAD).status_code == 401


def test_changing_contributor_id_does_not_bypass_auth(client):
    # Without a session, any id is rejected
    assert client.delete("/api/admin/contributors/999").status_code == 401
    # With a session, non-existent ids return 404 (never leak data)
    csrf = login(client)
    assert (
        client.delete(
            "/api/admin/contributors/999", headers=auth_headers(csrf)
        ).status_code
        == 404
    )


def test_out_of_range_ids_are_404_not_500(client):
    # SQLite INTEGER is 64-bit; binding larger ids used to raise OverflowError
    # -> 500. Out-of-range ids simply cannot exist -> 404.
    csrf = login(client)
    huge = str(2**80)
    assert (
        client.put(
            f"/api/admin/contributors/{huge}",
            json={"display_name": "X"},
            headers=auth_headers(csrf),
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/admin/contributors/{huge}", headers=auth_headers(csrf)
        ).status_code
        == 404
    )
    assert (
        client.put(
            "/api/admin/contributors/-5",
            json={"display_name": "X"},
            headers=auth_headers(csrf),
        ).status_code
        == 404
    )


def test_upload_to_out_of_range_id_404(client):
    csrf = login(client)
    res = client.post(
        f"/api/admin/contributors/{2**80}/image",
        files={"image": ("a.png", PNG_BYTES, "image/png")},
        headers=auth_headers(csrf),
    )
    assert res.status_code == 404


def test_authenticated_crud_flow(client):
    csrf = login(client)

    # create
    res = client.post(
        "/api/admin/contributors", json=VALID_PAYLOAD, headers=auth_headers(csrf)
    )
    assert res.status_code == 200
    contributor = res.json()["contributor"]
    cid = contributor["id"]
    assert contributor["github_username"] == "octocat"

    # public list sees it
    public = client.get("/api/contributors").json()["contributors"]
    assert any(c["id"] == cid for c in public)

    # update
    res = client.put(
        f"/api/admin/contributors/{cid}",
        json={"display_name": "Octo Cat II", "role": "Lead"},
        headers=auth_headers(csrf),
    )
    assert res.status_code == 200
    assert res.json()["contributor"]["display_name"] == "Octo Cat II"

    # delete
    res = client.delete(f"/api/admin/contributors/{cid}", headers=auth_headers(csrf))
    assert res.status_code == 200
    public = client.get("/api/contributors").json()["contributors"]
    assert not any(c["id"] == cid for c in public)


def test_duplicate_username_rejected(client):
    csrf = login(client)
    res = client.post(
        "/api/admin/contributors", json=VALID_PAYLOAD, headers=auth_headers(csrf)
    )
    assert res.status_code == 200
    res = client.post(
        "/api/admin/contributors", json=VALID_PAYLOAD, headers=auth_headers(csrf)
    )
    assert res.status_code == 409


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

def test_mutation_without_csrf_rejected(client):
    login(client)
    assert client.post("/api/admin/contributors", json=VALID_PAYLOAD).status_code == 403


def test_mutation_with_wrong_csrf_rejected(client):
    login(client)
    res = client.post(
        "/api/admin/contributors",
        json=VALID_PAYLOAD,
        headers=auth_headers("forged-csrf"),
    )
    assert res.status_code == 403


def test_upload_without_csrf_rejected(client):
    login(client)
    res = client.post(
        "/api/admin/contributors/1/image",
        files={"image": ("a.png", PNG_BYTES, "image/png")},
    )
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "field,value",
    [
        ("github_username", "bad username!"),
        ("github_username", ".."),
        ("github_username", ""),
        ("display_name", ""),
        ("display_name", "a" * 101),
        ("role", "r" * 81),
        ("description", "d" * 501),
        ("display_order", -1),
    ],
)
def test_invalid_contributor_data_rejected(client, field, value):
    csrf = login(client)
    payload = {**VALID_PAYLOAD, field: value}
    res = client.post(
        "/api/admin/contributors", json=payload, headers=auth_headers(csrf)
    )
    assert res.status_code == 422


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "http://github.com/octocat",
        "https://evil.com/octocat",
        "https://github.com/octocat?x=1",
        "https://user:pass@github.com/octocat",
    ],
)
def test_invalid_github_url_rejected(client, url):
    csrf = login(client)
    payload = {**VALID_PAYLOAD, "github_url": url}
    res = client.post(
        "/api/admin/contributors", json=payload, headers=auth_headers(csrf)
    )
    assert res.status_code == 422


@pytest.mark.parametrize(
    "extra",
    [
        {"avatar_url": "javascript:alert(1)"},
        {"avatar_url": "https://evil.example/x.png"},
        {"custom_avatar_url": "/api/uploads/fake.png"},
        {"isAdmin": True},
        {"rizz_master_code": "hunter2"},
    ],
)
def test_unknown_fields_rejected_not_silently_ignored(client, extra):
    # Models fail closed: fields outside the contract (avatar smuggling,
    # admin flags, secrets) must be rejected, never silently dropped.
    csrf = login(client)
    payload = {**VALID_PAYLOAD, **extra}
    res = client.post(
        "/api/admin/contributors", json=payload, headers=auth_headers(csrf)
    )
    assert res.status_code == 422
    # And the same for PUT
    cid = _create_contributor(client, csrf)
    res = client.put(
        f"/api/admin/contributors/{cid}",
        json={"display_name": "X", "custom_avatar_url": "/api/uploads/fake.png"},
        headers=auth_headers(csrf),
    )
    assert res.status_code == 422


def test_login_rejects_unknown_fields(client):
    res = client.post(
        "/api/admin/login", json={"code": CODE, "isAdmin": True}
    )
    assert res.status_code == 422


def test_github_url_defaults_to_profile(client):
    csrf = login(client)
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "github_url"}
    res = client.post(
        "/api/admin/contributors", json=payload, headers=auth_headers(csrf)
    )
    assert res.status_code == 200
    assert res.json()["contributor"]["github_url"] == "https://github.com/octocat"


# ---------------------------------------------------------------------------
# Image uploads
# ---------------------------------------------------------------------------

def _create_contributor(client, csrf):
    res = client.post(
        "/api/admin/contributors", json=VALID_PAYLOAD, headers=auth_headers(csrf)
    )
    return res.json()["contributor"]["id"]


def test_image_upload_roundtrip(client):
    csrf = login(client)
    cid = _create_contributor(client, csrf)
    res = client.post(
        f"/api/admin/contributors/{cid}/image",
        files={"image": ("anything.png", PNG_BYTES, "image/png")},
        headers=auth_headers(csrf),
    )
    assert res.status_code == 200
    url = res.json()["contributor"]["custom_avatar_url"]
    # URL must be a server-generated UUID name — the client filename is ignored
    import re
    assert re.fullmatch(r"/api/uploads/[0-9a-f]{32}\.png", url)
    # The file is publicly fetchable
    assert client.get(url).status_code == 200


def test_upload_oversized_image_rejected(client):
    csrf = login(client)
    cid = _create_contributor(client, csrf)
    big = PNG_BYTES + b"\x00" * (2 * 1024 * 1024)  # > 2 MB
    res = client.post(
        f"/api/admin/contributors/{cid}/image",
        files={"image": ("big.png", big, "image/png")},
        headers=auth_headers(csrf),
    )
    assert res.status_code == 400
    assert "too large" in res.json()["detail"].lower()


def test_upload_invalid_image_rejected(client):
    csrf = login(client)
    cid = _create_contributor(client, csrf)
    res = client.post(
        f"/api/admin/contributors/{cid}/image",
        files={"image": ("evil.png", NOT_IMAGE, "image/png")},
        headers=auth_headers(csrf),
    )
    assert res.status_code == 400


def test_upload_path_traversal_filename_safe(client):
    csrf = login(client)
    cid = _create_contributor(client, csrf)
    res = client.post(
        f"/api/admin/contributors/{cid}/image",
        files={"image": ("../../../../evil.png", PNG_BYTES, "image/png")},
        headers=auth_headers(csrf),
    )
    assert res.status_code == 200
    url = res.json()["contributor"]["custom_avatar_url"]
    assert "../" not in url and "evil" not in url


def test_upload_to_missing_contributor_404(client):
    csrf = login(client)
    res = client.post(
        "/api/admin/contributors/4242/image",
        files={"image": ("a.png", PNG_BYTES, "image/png")},
        headers=auth_headers(csrf),
    )
    assert res.status_code == 404


def test_upload_endpoint_rejects_bad_filename(client):
    res = client.get("/api/uploads/..%2F..%2Fmain.py")
    assert res.status_code == 404
    res = client.get("/api/uploads/nothex.png")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Page routing: /contributors (public) vs /contributors/admin (admin UI)
# ---------------------------------------------------------------------------

def test_public_contributors_page_has_no_admin_controls(client):
    # The public directory must never contain admin UI, even as markup.
    r = client.get("/contributors")
    assert r.status_code == 200
    html = r.text
    assert "Meet the people building Repo Rizz." in html
    assert "contributors-grid" in html
    for forbidden in [
        "rizz-master", "RIZZ-MASTER?", "login-form", "login-code",
        "admin-panel", "admin-view", "add-contributor-btn",
        "logout-btn", "ADD CONTRIBUTOR", "data-edit-id",
    ]:
        assert forbidden not in html, f"public page must not contain {forbidden}"


def test_admin_page_route_serves_management_ui(client):
    # /contributors/admin is a static UI page; its privileged actions are
    # still authorized server-side by the admin session + CSRF.
    r = client.get("/contributors/admin")
    assert r.status_code == 200
    html = r.text
    assert "Rizz Master Access" in html          # login view
    assert "admin-view" in html                  # panel view
    assert "add-contributor-btn" in html
    assert "logout-btn" in html


def test_public_contributors_requires_no_auth(client):
    res = client.get("/api/contributors")
    assert res.status_code == 200
    assert "contributors" in res.json()


def test_public_contributors_expose_no_secrets(client):
    csrf = login(client)
    client.post(
        "/api/admin/contributors", json=VALID_PAYLOAD, headers=auth_headers(csrf)
    )
    row = client.get("/api/contributors").json()["contributors"][0]
    allowed = {
        "id", "github_username", "display_name", "github_url", "role",
        "description", "avatar_url", "custom_avatar_url", "display_order",
        "created_at", "updated_at",
    }
    assert set(row.keys()) <= allowed
    text = client.get("/api/contributors").text
    assert "RIZZ_MASTER_CODE" not in text
    assert "service" not in text.lower() or "service" not in row.keys()


def test_oversized_request_body_rejected(client):
    huge = {"owner": "x", "name": "y", "padding": "a" * (6 * 1024 * 1024)}
    res = client.post("/analyze", json=huge)
    assert res.status_code == 413