"""
Normal-user analysis history (Supabase-backed, per authenticated user).

SECURITY MODEL
- Every route verifies the caller's Supabase access token SERVER-SIDE by
  calling GoTrue /userinfo. The user id comes from that verified response —
  never from the request body, headers, or query params.
- The row's user_id column is always set to the verified user id; a request
  can never read or delete another user's rows (id changes return 404).
- RLS on the `analyses` table (see supabase/migrations/) enforces the same
  rule for any direct client access.
- Completely separate from Rizz Master admin auth (admin_auth.py): a normal
  Supabase session grants zero admin power, and RIZZ_MASTER_CODE grants no
  user-history access.
"""

import os
import re
import logging

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("repo_rizz.user_history")

router = APIRouter()

OWNER_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
ID_RE = re.compile(r"^[0-9a-fA-F-]{36}$|^\d{1,19}$")


def _valid_history_id(history_id: str) -> bool:
    # Supabase ids are uuids; numeric ids can never exist there -> 404 fast.
    return bool(ID_RE.fullmatch(history_id or ""))


def _env(key: str) -> str:
    return (os.getenv(key) or "").strip()


def _auth_config():
    """URL + publishable (anon) key for GoTrue session verification."""
    url = _env("NEXT_PUBLIC_SUPABASE_URL") or _env("SUPABASE_URL")
    key = _env("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
    return {"url": url.rstrip("/"), "key": key}


def _service_config():
    """URL + service-role key for writing rows (bypasses RLS by design)."""
    return {"url": _env("SUPABASE_URL").rstrip("/"), "key": _env("SUPABASE_SERVICE_ROLE_KEY")}


async def _verify_user(token: str) -> str:
    """Return the authenticated Supabase user id, or raise HTTPException."""
    cfg = _auth_config()
    if not cfg["url"] or not cfg["key"]:
        raise HTTPException(status_code=503, detail="User accounts are not configured on this server.")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Modern GoTrue serves the session user at /auth/v1/user (the
            # legacy /userinfo endpoint 404s on current Supabase projects).
            r = await client.get(
                f"{cfg['url']}/auth/v1/user",
                headers={"apikey": cfg["key"], "Authorization": f"Bearer {token}"},
            )
            if r.status_code == 404:
                r = await client.get(
                    f"{cfg['url']}/auth/v1/userinfo",
                    headers={"apikey": cfg["key"], "Authorization": f"Bearer {token}"},
                )
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Could not verify session — try again.")
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    user_id = (r.json() or {}).get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return user_id


async def current_user(authorization: str = Header(default="")) -> str:
    """FastAPI dependency: extract the bearer token and verify it server-side."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return await _verify_user(token)


class HistoryPayload(BaseModel):
    # Fail closed: unknown fields (user_id smuggling, isAdmin flags, ...)
    # are rejected, never silently ignored.
    model_config = {"extra": "forbid"}

    owner: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    score: int = Field(ge=0, le=100)
    status: str = Field(default="", max_length=40)
    summary: str = Field(default="", max_length=1000)
    dimensions: dict = Field(default_factory=dict)
    rizz_verdict: str = Field(default="", max_length=2000)
    critical_count: int = Field(default=0, ge=0, le=1000)


def _validate_repo(owner: str, name: str):
    if not OWNER_NAME_RE.match(owner) or not OWNER_NAME_RE.match(name):
        raise HTTPException(status_code=422, detail="Invalid repository name.")


def _unavailable(detail: str = "Analysis history is not configured yet — run the analyses migration."):
    raise HTTPException(status_code=503, detail=detail)


async def _rest(method: str, path: str, **kwargs):
    """Supabase PostgREST call; maps config/table errors to a clean 503."""
    cfg = _service_config()
    if not cfg["url"] or not cfg["key"]:
        _unavailable()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.request(
                method,
                f"{cfg['url']}/rest/v1/{path}",
                headers={
                    "apikey": cfg["key"],
                    "Authorization": f"Bearer {cfg['key']}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                **kwargs,
            )
    except httpx.HTTPError:
        _unavailable()
    if r.status_code >= 400:
        body = r.text[:300]
        logger.warning("postgrest_%s_failed status=%s body=%s", method, r.status_code, body)
        if "42P01" in body or "PGRST205" in body:
            _unavailable()
        if r.status_code == 404:
            return None  # row-level 404 (delete/select of a missing id)
        _unavailable("Analysis history is unavailable right now.")
    try:
        return r.json()
    except ValueError:
        return []


# ---------------------------------------------------------------------------
# Public routes (all protected by current_user)
# ---------------------------------------------------------------------------

# Every route depends on current_user — the verified Supabase user id is
# injected by FastAPI and can never come from the client.

@router.post("/api/history")
async def save_history(payload: HistoryPayload, user_id: str = Depends(current_user)) -> dict:
    return await _insert(user_id, payload)


@router.get("/api/history")
async def list_history(user_id: str = Depends(current_user)) -> dict:
    return await _list(user_id)


@router.delete("/api/history/{history_id}")
async def delete_history(history_id: str, user_id: str = Depends(current_user)) -> dict:
    return await _delete(user_id, history_id)


# ---------------------------------------------------------------------------
# Store operations (kept as plain functions so tests can patch them)
# ---------------------------------------------------------------------------

async def _insert(user_id: str, payload: HistoryPayload) -> dict:
    _validate_repo(payload.owner, payload.name)
    row = {
        "user_id": user_id,  # verified server-side — never from the client
        "owner": payload.owner,
        "name": payload.name,
        "score": payload.score,
        "status": payload.status,
        "summary": payload.summary,
        "dimensions": payload.dimensions,
        "rizz_verdict": payload.rizz_verdict,
        "critical_count": payload.critical_count,
    }
    rows = await _rest("POST", "analyses", json=row)
    if not rows:
        _unavailable()
    return {"saved": True, "id": rows[0].get("id")}


async def _list(user_id: str) -> dict:
    rows = await _rest(
        "GET",
        f"analyses?user_id=eq.{user_id}&order=created_at.desc&limit=100"
        f"&select=id,owner,name,score,status,summary,dimensions,rizz_verdict,critical_count,created_at",
    )
    if rows is None:
        _unavailable()
    return {"history": rows or []}


async def _delete(user_id: str, history_id: str) -> dict:
    if not _valid_history_id(history_id):
        raise HTTPException(status_code=404, detail="Analysis not found.")
    rows = await _rest("DELETE", f"analyses?id=eq.{history_id}&user_id=eq.{user_id}")
    if rows is None or not rows:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return {"deleted": True}
