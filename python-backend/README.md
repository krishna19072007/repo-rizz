# Repo Rizz - Python Backend

This is the FastAPI backend for Repo Rizz. It handles GitHub API orchestration, architectural analysis, engineering scoring, Gemini AI insights, and the Contributors / Rizz Master admin feature.

## Code layout

Each file owns one concern; `main.py` only composes them:

| Module | Owns |
|--------|------|
| `main.py` | App shell: middleware (CORS, security headers, body cap), the `/analyze` engine API, static page routes; mounts the two routers below |
| `admin_auth.py` | Admin auth: session store, constant-time code check, CSRF, rate limiter, and the `auth_router` (POST `/api/admin/login` \| `logout`, GET `/api/admin/me`) |
| `contributors_api.py` | Contributor HTTP layer: Pydantic validation models, the `admin_guard` dependency (session + CSRF), and every `/api/contributors`, `/api/admin/contributors`, `/api/uploads` route |
| `contributors_store.py` | Persistence only: SQLite (default) or Supabase (optional), plus `get_store()` and `is_duplicate_error()` |
| `uploads.py` | Secure avatar file handling: magic-byte sniffing, size cap, UUID names, safe serving/cleanup |

New contributor or admin routes go in `contributors_api.py` (auth routes in `admin_auth.py`), never in `main.py`.

## Windows Setup Instructions

Run the following commands in PowerShell to start the server locally:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000 --no-proxy-headers
```

`--no-proxy-headers` matters for security: it stops uvicorn from
rewriting the client IP from the `X-Forwarded-For` header, so the login
rate limiter always sees the real caller IP. If you run the backend
behind a reverse proxy that sets `X-Forwarded-For`, drop the flag and
set `TRUST_FORWARDED_FOR=true` in `.env` instead.

## Environment Variables

Copy `.env.template` to `.env` and fill in your keys:

- `RIZZ_MASTER_CODE`: **Required for the admin panel.** The secret code used to log in as "Rizz Master". It is read only by the server and is never sent to the browser. Set it to any strong passphrase.
- `GEMINI_API_KEY`: Required for AI insights and verdict generation.
- `GITHUB_TOKEN`: Optional, but highly recommended to avoid rate limiting.

Optional:

- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`: set both to store contributors in Supabase instead of the local SQLite database. Run the migration in `supabase/migrations/` first (the `supabase` package must also be installed: `pip install supabase`). Leave both empty for zero-config local storage.
- `COOKIE_SECURE`: set to `true` when serving over HTTPS so the admin session cookie is marked Secure.
- `TRUST_FORWARDED_FOR`: set to `true` ONLY when running behind a reverse proxy that sets `X-Forwarded-For`. Keep it unset (default) when clients connect directly — see the uvicorn note above.

## Contributors & Rizz Master

- **Public page:** `/contributors` — lists contributors from the database.
- **Admin login:** click `RIZZ-MASTER?` on the contributors page and enter the code from `RIZZ_MASTER_CODE`.
- **Persistence:** contributors are stored in `python-backend/data/contributors.db` (SQLite) by default, or in Supabase when configured.
- **Uploaded images:** stored in `python-backend/uploads/contributors/` with server-generated UUID filenames. Both directories are git-ignored.

### API endpoints

| Method | Route | Auth |
|--------|-------|------|
| GET | `/api/contributors` | public |
| POST | `/api/admin/login` | rate-limited |
| POST | `/api/admin/logout` | session |
| GET | `/api/admin/me` | session |
| POST | `/api/admin/contributors` | admin + CSRF |
| PUT | `/api/admin/contributors/{id}` | admin + CSRF |
| DELETE | `/api/admin/contributors/{id}` | admin + CSRF |
| POST | `/api/admin/contributors/{id}/image` | admin + CSRF |
| GET | `/api/uploads/{filename}` | public (validated names only) |

### Security model

- The Rizz Master code exists **only** in the server environment.
- Login issues an HttpOnly, SameSite=Lax session cookie backed by a server-side random session token. Nothing on the client can grant admin rights.
- Every state-changing endpoint independently verifies the session **and** a session-bound CSRF token.
- Login is rate-limited per IP (5 failures -> 15 minute block).
- Image uploads are validated server-side by magic bytes (PNG/JPG/GIF/WebP, max 2 MB); client filenames are ignored.
- If the database uses Supabase, Row Level Security is enabled so the public can only SELECT; writes happen through the service-role key behind the admin session.

## Tests

```powershell
python -m pytest tests/
```

The suite covers authentication, rate limiting, sessions, logout, CSRF, authorization bypass attempts, input validation, and image upload security.