"""
Repo Rizz FastAPI backend — composition root.

This module owns the application shell:
- the FastAPI app and its middleware (CORS, security headers, body cap)
- the pre-existing /analyze engine API (GitHub + Gemini scoring)
- mounting the contributor + admin routers and the static frontend pages

Feature logic lives in dedicated modules:
- admin_auth        -> sessions, code check, CSRF, rate limit, login/logout/me
- contributors_api  -> contributor validation + routes (mounted below)
- contributors_store-> persistence (SQLite default / optional Supabase)
- uploads           -> secure avatar file handling
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from github import (
    fetch_analysis_input,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubServiceError,
    GitHubNetworkError
)
from engine import run_analysis
from dotenv import load_dotenv
import json
import os
import re
import logging

from admin_auth import auth_router, cookie_is_secure
from contributors_api import router as contributors_router
from user_history import router as user_history_router

load_dotenv(); load_dotenv("../.env.local")

def get_supabase_auth_config():
    """Publishable Supabase client config for normal (non-admin) user auth.

    Returns ONLY the anon/publishable key — never the service-role key from
    the backend .env — so this is safe to serve to any browser. The values
    come from the frontend .env.local (NEXT_PUBLIC_* = meant for clients).
    """
    url = (os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "").strip()
    anon_key = (os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY") or "").strip()
    return {"enabled": bool(url and anon_key), "url": url, "anonKey": anon_key}

def _content_security_policy() -> str:
    """CSP built per response so the Supabase project origin is only allowed
    when the operator has actually configured Supabase auth."""
    supabase_url = (get_supabase_auth_config()["url"] or "").rstrip("/")
    connect_src = "connect-src 'self' https://api.github.com"
    if supabase_url:
        # Supabase Auth (GoTrue) lives on the project URL — the browser must
        # be able to reach it for login/session refresh.
        connect_src += f" {supabase_url}"
    return (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https://github.com https://avatars.githubusercontent.com; "
        f"{connect_src}; "
        "font-src 'self' https://fonts.gstatic.com; "
        "frame-ancestors 'none';"
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("repo_rizz.api")

app = FastAPI()

from starlette.middleware.base import BaseHTTPMiddleware

OWNER_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")

def validate_repo_params(owner: str, name: str):
    if not owner or not name:
        raise HTTPException(status_code=400, detail="Owner and name parameters are required.")
    if len(owner) > 100 or len(name) > 100:
        raise HTTPException(status_code=400, detail="Owner and name parameters must be under 100 characters.")
    if not OWNER_NAME_RE.match(owner) or not OWNER_NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="Invalid characters in repository owner or name.")

# Add CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Ingest security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = _content_security_policy()
        # HSTS only when cookies are Secure (HTTPS deployments)
        if cookie_is_secure():
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Reject oversized request bodies early (defense in depth; the image
# upload endpoint additionally enforces its own 2 MB content cap).
class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    MAX_BYTES = 5 * 1024 * 1024

    async def dispatch(self, request, call_next):
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > self.MAX_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large."},
            )
        return await call_next(request)

app.add_middleware(MaxBodySizeMiddleware)

# Feature routers (see module docstrings for what each owns)
app.include_router(auth_router)
app.include_router(contributors_router)
app.include_router(user_history_router)

class AnalyzeRequest(BaseModel):
    owner: str
    name: str
    demo: bool = False

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Python backend is running"}

@app.get("/api/config/supabase")
async def supabase_client_config():
    """Publishable config for normal-user auth (GitHub OAuth / email).

    The anon key is public by design (NEXT_PUBLIC_*). The service-role key
    lives only in the backend .env and is never returned here.
    """
    return get_supabase_auth_config()

@app.get("/diagnostic/github")
async def diagnostic_github():
    token = os.getenv("GITHUB_TOKEN")
    return {
        "github_token_configured": bool(token and token.strip())
    }

@app.post("/analyze")
async def analyze_repo(req: AnalyzeRequest):
    validate_repo_params(req.owner, req.name)
    if req.demo:
        # Load demo data from result.json
        demo_path = os.path.join(os.path.dirname(__file__), "..", "result.json")
        try:
            with open(demo_path, "r", encoding="utf-8") as f:
                demo_data = json.load(f)
                return {"result": demo_data.get("result", demo_data), "demo": True}
        except Exception as e:
            print(f"Failed to load demo data: {e}")
            raise HTTPException(status_code=500, detail="Demo data unavailable")

    try:
        input_data = await fetch_analysis_input(req.owner, req.name)
        result = await run_analysis(input_data)
        return {"result": result}
    except GitHubRateLimitError as e:
        return JSONResponse(
            status_code=403,
            content={"error": "GITHUB_RATE_LIMIT", "message": str(e)}
        )
    except GitHubNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error": "GITHUB_NOT_FOUND", "message": str(e)}
        )
    except GitHubNetworkError as e:
        return JSONResponse(
            status_code=503,
            content={"error": "GITHUB_NETWORK_ERROR", "message": str(e)}
        )
    except GitHubServiceError as e:
        return JSONResponse(
            status_code=500,
            content={"error": "GITHUB_SERVICE_ERROR", "message": str(e)}
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred during repository analysis.")

@app.get("/diagnostic/analyze")
async def diagnostic_analyze(owner: str, name: str):
    validate_repo_params(owner, name)
    try:
        from github import fetch_analysis_input
        input_data = await fetch_analysis_input(owner, name)
        tree = input_data.get("tree", [])
        return {
            "owner": owner,
            "name": name,
            "tree_size": len(tree),
            "tree_sample": [t.get("path") for t in tree[:25]],
            "important_files_found": list(input_data.get("importantFiles", {}).keys()),
            "has_package_json": bool(input_data.get("packageJson")),
            "has_readme": bool(input_data.get("readme")),
            "has_license": bool(input_data.get("license")),
            "languages": input_data.get("languages", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred during diagnostic analysis.")


# Mount static files and page routes
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("../frontend/index.html")

@app.get("/about")
async def serve_about():
    return FileResponse("../frontend/about.html")

@app.get("/analyze")
async def serve_analyze():
    return FileResponse("../frontend/analyze.html")

@app.get("/compare")
async def serve_compare():
    return FileResponse("../frontend/compare.html")

@app.get("/history")
async def serve_history():
    return FileResponse("../frontend/history.html")

@app.get("/privacy")
async def serve_privacy():
    return FileResponse("../frontend/privacy.html")

@app.get("/login")
async def serve_login():
    # Normal-user login (Supabase GitHub OAuth / email + password). This is
    # separate from Rizz Master admin auth at /contributors/admin.
    # no-store so a stale cached copy of an auth page can never resurface.
    return FileResponse("../frontend/login.html", headers={"Cache-Control": "no-store"})

@app.get("/signup")
async def serve_signup():
    # Normal-user account creation (Supabase email + password / GitHub OAuth).
    return FileResponse("../frontend/signup.html", headers={"Cache-Control": "no-store"})

@app.get("/contributors")
async def serve_contributors():
    # Public directory page — never shows admin controls and never checks
    # the admin session. Management UI lives at /contributors/admin.
    return FileResponse("../frontend/contributors.html", headers={"Cache-Control": "no-store"})

@app.get("/contributors/admin")
async def serve_contributors_admin():
    # Rizz Master management page. The HTML is static; every privileged
    # action is authorized server-side by the admin session + CSRF.
    # no-store keeps a stale cached copy (the old build carried admin UI
    # on the public URL) from ever resurfacing.
    return FileResponse("../frontend/contributors_admin.html", headers={"Cache-Control": "no-store"})
