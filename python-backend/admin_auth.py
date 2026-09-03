"""
Rizz Master admin authentication & session security.

Security model
--------------
- The Rizz Master code lives ONLY in the server environment (RIZZ_MASTER_CODE).
  It is never returned to the browser and never logged.
- Successful login creates a cryptographically random session token stored
  server-side (in memory). The browser only receives an HttpOnly cookie
  containing that random token.
- Every privileged endpoint independently verifies the session cookie and the
  session-bound CSRF token. Nothing on the client (localStorage, JS variables,
  request-body flags like {"isAdmin": true}) can grant admin rights.
- The login endpoint is rate-limited per IP to slow brute-force attempts.
"""

import os
import time
import logging
import secrets
import threading
from collections import deque

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("repo_rizz.admin")

# ---------------------------------------------------------------------------
# Session handling
# ---------------------------------------------------------------------------

SESSION_COOKIE = "rizz_master_session"
SESSION_TTL_SECONDS = 12 * 60 * 60  # 12 hours


class SessionStore:
    """In-memory session store.

    Sessions live only in this process, which is fine for a single-server
    student project. Logout deletes the session immediately, and expired
    sessions are rejected and pruned lazily.
    """

    def __init__(self):
        self._sessions = {}  # token -> {"csrf": str, "expires_at": float}
        self._lock = threading.Lock()

    def create(self) -> tuple[str, str]:
        """Create a session; returns (token, csrf_token)."""
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = {
                "csrf": csrf,
                "expires_at": time.time() + SESSION_TTL_SECONDS,
            }
        return token, csrf

    def get(self, token: str) -> dict | None:
        """Return the session dict if the token is valid and unexpired."""
        if not token:
            return None
        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                return None
            if session["expires_at"] < time.time():
                del self._sessions[token]  # expired -> invalidated
                return None
            return session

    def delete(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)

    def clear(self) -> None:
        """Drop all sessions (used by tests and for admin reset)."""
        with self._lock:
            self._sessions.clear()


sessions = SessionStore()


def cookie_is_secure() -> bool:
    """Secure cookies in production; plain http:// local dev uses non-secure."""
    return os.getenv("COOKIE_SECURE", "false").strip().lower() in ("1", "true", "yes")


def session_cookie_kwargs() -> dict:
    return {
        "key": SESSION_COOKIE,
        "httponly": True,      # JavaScript cannot read the session token
        "samesite": "lax",     # blocks most cross-site request forgery
        "secure": cookie_is_secure(),
        "path": "/",
        "max_age": SESSION_TTL_SECONDS,
    }


def require_admin(request: Request) -> dict:
    """Authorize a privileged request using the session cookie only.

    Returns the valid, unexpired session dict, or None when there is no
    session. This is the single gate every admin endpoint passes through.
    """
    token = request.cookies.get(SESSION_COOKIE)
    return sessions.get(token) if token else None


# ---------------------------------------------------------------------------
# Rizz Master code verification (constant-time)
# ---------------------------------------------------------------------------

def rizz_code_configured() -> bool:
    value = os.getenv("RIZZ_MASTER_CODE", "")
    return bool(value and value.strip())


def verify_rizz_code(attempt: str) -> bool:
    """Compare the submitted code with the server-side secret.

    secrets.compare_digest is constant-time, so response timing does not
    reveal how close an attempt was.
    """
    expected = os.getenv("RIZZ_MASTER_CODE", "")
    if not expected or not attempt:
        return False
    return secrets.compare_digest(attempt, expected)


# ---------------------------------------------------------------------------
# CSRF protection
# ---------------------------------------------------------------------------

CSRF_HEADER = "X-CSRF-Token"


def verify_csrf(request: Request, session: dict) -> bool:
    """Validate the session-bound CSRF token header.

    The token is generated at login, stored server-side inside the session,
    and must be echoed back in the X-CSRF-Token header for every state
    changing request. A cross-site attacker cannot read or set this header
    (CORS + SameSite cookie), so CSRF is blocked even if the session cookie
    is somehow sent.
    """
    submitted = request.headers.get(CSRF_HEADER, "")
    if not submitted or not session:
        return False
    return secrets.compare_digest(submitted, session["csrf"])



# ---------------------------------------------------------------------------
# Login rate limiting (per IP, in-memory)
# ---------------------------------------------------------------------------

class LoginRateLimiter:
    """Simple failure tracker.

    - Per-IP: after MAX_FAILURES failed attempts inside WINDOW_SECONDS the
      IP is blocked for LOCKOUT_SECONDS. Successful logins reset the
      per-IP counter.
    - Global: after MAX_GLOBAL_FAILURES failed attempts inside the window
      (across all IPs) login is blocked entirely until the window passes.
      This bounds brute-force attempts even if an attacker rotates IPs.
    This is intentionally simple: one server process, in-memory state.
    """

    def __init__(self, max_failures: int = 5, window_seconds: int = 900,
                 lockout_seconds: int = 900, max_global_failures: int = 20):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self.max_global_failures = max_global_failures
        self._failures: dict[str, deque] = {}
        self._all_failures: deque = deque()
        self._lock = threading.Lock()

    def _prune(self, ip: str, now: float):
        q = self._failures.get(ip)
        if q is None:
            return
        while q and now - q[0] > self.window_seconds:
            q.popleft()
        if not q:
            self._failures.pop(ip, None)

    def _prune_global(self, now: float):
        while self._all_failures and now - self._all_failures[0] > self.window_seconds:
            self._all_failures.popleft()

    def blocked(self, ip: str) -> bool:
        now = time.time()
        with self._lock:
            self._prune(ip, now)
            self._prune_global(now)
            if len(self._all_failures) >= self.max_global_failures:
                return True
            q = self._failures.get(ip)
            if q is None:
                return False
            # Any failure older than the lockout window no longer counts.
            if now - q[0] > self.lockout_seconds:
                return False
            return len(q) >= self.max_failures

    def record_failure(self, ip: str) -> None:
        now = time.time()
        with self._lock:
            self._prune(ip, now)
            self._prune_global(now)
            self._failures.setdefault(ip, deque()).append(now)
            self._all_failures.append(now)

    def record_success(self, ip: str) -> None:
        with self._lock:
            self._failures.pop(ip, None)

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()
            self._all_failures.clear()


login_rate_limiter = LoginRateLimiter()


def client_ip(request: Request) -> str:
    """Best-effort client IP for rate limiting.

    X-Forwarded-For is only trusted when explicitly configured via
    TRUST_FORWARDED_FOR=true (i.e. the server sits behind a reverse
    proxy). Otherwise the header is ignored so direct clients cannot
    spoof it to bypass the login rate limit.
    """
    trust_forwarded = os.getenv("TRUST_FORWARDED_FOR", "false").strip().lower() in (
        "1", "true", "yes"
    )
    if trust_forwarded:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# Admin auth HTTP API (login / logout / me)
# ---------------------------------------------------------------------------

auth_router = APIRouter()


class LoginRequest(BaseModel):
    # Fail closed: reject unknown fields (e.g. smuggled isAdmin flags).
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=512)


@auth_router.post("/api/admin/login")
def admin_login(req: LoginRequest, request: Request):
    ip = client_ip(request)

    # Rate limit: block IPs with too many recent failures.
    if login_rate_limiter.blocked(ip):
        logger.warning("admin_login_rate_limited ip=%s", ip)
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many attempts. Try again later."},
        )

    if not rizz_code_configured():
        logger.error("admin_login_unconfigured ip=%s", ip)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Rizz Master access is not configured. "
                          "Set RIZZ_MASTER_CODE in the backend .env file."
            },
        )

    if not verify_rizz_code(req.code):
        login_rate_limiter.record_failure(ip)
        logger.warning("admin_login_failure ip=%s", ip)
        # Generic message: never reveal whether the code was close.
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid credentials."},
        )

    login_rate_limiter.record_success(ip)
    token, csrf_token = sessions.create()
    logger.info("admin_login_success ip=%s", ip)

    response = JSONResponse(content={"authenticated": True, "csrf_token": csrf_token})
    response.set_cookie(**session_cookie_kwargs(), value=token)
    return response


@auth_router.post("/api/admin/logout")
def admin_logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        sessions.delete(token)
        logger.info("admin_logout ip=%s", client_ip(request))
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=cookie_is_secure(),
        httponly=True,
        samesite="lax",
    )
    return response


@auth_router.get("/api/admin/me")
def admin_me(request: Request):
    """Tells the frontend only 'authenticated or not' — never secrets."""
    session = require_admin(request)
    if session is None:
        return {"authenticated": False}
    return {"authenticated": True, "csrf_token": session["csrf"]}