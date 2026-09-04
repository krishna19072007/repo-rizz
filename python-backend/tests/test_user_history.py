"""
Hermetic tests for the protected per-user analysis history API.

The Supabase PostgREST boundary (user_history._rest) and the session
verification dependency (user_history.current_user) are patched so the
suite never touches the live Supabase project. The real store functions
keep running, so validation (repo names, id shapes) is actually exercised.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import user_history
from main import app

VALID = {
    "owner": "octocat",
    "name": "hello-world",
    "score": 88,
    "status": "ready",
    "summary": "Great docs.",
    "dimensions": {"documentation": 90},
    "rizz_verdict": "Solid.",
    "critical_count": 2,
}
UUID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
                "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]:
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def authed(client):
    """Authenticated client with a deterministic fake current_user."""
    app.dependency_overrides[user_history.current_user] = lambda authorization="": "user-0001"
    client.headers.update({"Authorization": "Bearer token-from-override"})
    yield client
    app.dependency_overrides.clear()


def _no_network():
    async def no_network(*args, **kwargs):
        raise AssertionError("network boundary reached")
    return no_network


# ---------------------------------------------------------------------------
# Authentication / authorization
# ---------------------------------------------------------------------------

def test_history_requires_bearer_token(client):
    # No session -> 401 before any network/store call happens.
    assert client.get("/api/history").status_code == 401
    assert client.post("/api/history", json={"owner": "o", "name": "n", "score": 50}).status_code == 401
    assert client.delete("/api/history/abc").status_code == 401


def test_history_rejects_malformed_bearer(client):
    r = client.get("/api/history", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Save (POST)
# ---------------------------------------------------------------------------

def test_save_sets_verified_user_id(authed, monkeypatch):
    captured = {}

    async def fake_rest(method, path, **kwargs):
        captured["method"] = method
        captured["path"] = path
        captured["json"] = kwargs.get("json")
        return [{"id": "row-1"}]

    monkeypatch.setattr(user_history, "_rest", fake_rest)
    res = authed.post("/api/history", json=VALID)
    assert res.status_code == 200
    assert res.json() == {"saved": True, "id": "row-1"}
    # user_id comes from the verified session, never from the body.
    assert captured["json"]["user_id"] == "user-0001"


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID, "user_id": "user-0002"},        # smuggling a foreign id
        {**VALID, "isAdmin": True},               # frontend flag
        {**VALID, "owner": "../evil"},            # bad repo name
        {**VALID, "owner": "has space"},          # bad repo name
        {**VALID, "score": 101},                  # out of range
        {**VALID, "score": -1},
    ],
)
def test_save_rejects_invalid_payloads(authed, monkeypatch, payload):
    monkeypatch.setattr(user_history, "_rest", _no_network())
    res = authed.post("/api/history", json=payload)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# List (GET)
# ---------------------------------------------------------------------------

def test_list_returns_own_rows(authed, monkeypatch):
    rows = [{"id": UUID, "owner": "octocat", "name": "hello-world", "score": 88,
             "status": "ready", "summary": "s", "dimensions": {}, "rizz_verdict": "",
             "critical_count": 0, "created_at": "2026-09-04T00:00:00Z"}]

    async def fake_rest(method, path, **kwargs):
        assert "user_id=eq.user-0001" in path  # filtered to the verified user
        return rows

    monkeypatch.setattr(user_history, "_rest", fake_rest)
    res = authed.get("/api/history")
    assert res.status_code == 200
    assert res.json()["history"][0]["id"] == UUID


def test_list_unavailable_is_503(authed, monkeypatch):
    async def table_missing(method, path, **kwargs):
        raise HTTPException(status_code=503, detail="Analysis history is not configured yet.")

    monkeypatch.setattr(user_history, "_rest", table_missing)
    assert authed.get("/api/history").status_code == 503


# ---------------------------------------------------------------------------
# Delete (DELETE)
# ---------------------------------------------------------------------------

def test_delete_own_row(authed, monkeypatch):
    captured = {}

    async def fake_rest(method, path, **kwargs):
        captured["path"] = path
        return [{"id": UUID}]

    monkeypatch.setattr(user_history, "_rest", fake_rest)
    res = authed.delete(f"/api/history/{UUID}")
    assert res.status_code == 200
    assert f"id=eq.{UUID}" in captured["path"]
    assert "user_id=eq.user-0001" in captured["path"]


def test_delete_garbage_id_404_without_network(authed, monkeypatch):
    monkeypatch.setattr(user_history, "_rest", _no_network())
    assert authed.delete("/api/history/x").status_code == 404
    assert authed.delete("/api/history/abcdefghijklmnopq").status_code == 404
    assert authed.delete(f"/api/history/{'a' * 100}").status_code == 404


def test_delete_missing_row_404(authed, monkeypatch):
    async def not_found(method, path, **kwargs):
        return []  # PostgREST returns zero rows for a non-owned/missing id

    monkeypatch.setattr(user_history, "_rest", not_found)
    assert authed.delete(f"/api/history/{UUID}").status_code == 404


def test_verify_user_rejects_invalid_token(monkeypatch):
    async def fake_verify(token):
        raise HTTPException(status_code=401, detail="Invalid or expired session.")

    monkeypatch.setattr(user_history, "_verify_user", fake_verify)

    async def run():
        with pytest.raises(HTTPException) as exc:
            await user_history._verify_user("bogus")
        return exc.value.status_code

    import asyncio
    assert asyncio.run(run()) == 401
