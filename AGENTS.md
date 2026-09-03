# AGENTS.md

Session learnings for Repo Rizz — things not recoverable by reading the code alone.

## Architecture — as built vs. as documented
- Backend module map (post architecture pass): `python-backend/main.py` is a **composition root** — FastAPI app, middleware, the pre-existing `/analyze` engine API, static page routes — plus `app.include_router(auth_router)` / `include_router(contributors_router)`. Auth endpoints (login/logout/me) live in `admin_auth.py` as `auth_router`; contributor routes + Pydantic validation live in `contributors_api.py` (`router`, with `admin_guard` — one FastAPI dependency enforcing session+CSRF — and `_store_error` mapping 409/500). Persistence is `contributors_store.py` (also owns `is_duplicate_error`), secure files are `uploads.py`. New contributor/admin routes belong in `contributors_api.py`, not `main.py`.
- The "frontend" is static HTML/CSS/JS in `frontend/` served **by** the FastAPI backend (StaticFiles at `/static/` + explicit page routes in `python-backend/main.py`). There is no Next.js app; README's Next.js/Supabase claims are aspirational and root `.env.local` (`NEXT_PUBLIC_*`) is loaded but read by nothing.
- Frontend fetches are same-origin, so the CORS origin list (localhost:3000/8001) is only exercised if pages are hosted separately.
- The `.bat` launchers run the backend on **port 8001** (README says 8000) and pass `--no-proxy-headers` (see runtime gotcha below).
- `python-backend/.env` is the real config, but `main.py` also runs `load_dotenv("../.env.local")` — treat root `.env.local` as part of the backend's environment.

## Supabase is optional, not integrated
- No Supabase client code/migrations/keys existed anywhere before the Contributors feature; "Supabase (optional)" in the README described nothing real.
- The optional store activates only with `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` set **and** the `supabase` pip package installed (import is guarded; the line is commented out of `python-backend/requirements.txt`). Default persistence is SQLite in `python-backend/data/` (auto-created, git-ignored); uploaded images live in `python-backend/uploads/` (also git-ignored).

## Runtime gotchas
- **uvicorn's `proxy-headers` mode is ON by default and trusts loopback**: it rewrites `request.client` from the spoofable `X-Forwarded-For` header, silently defeating any per-IP rate limiting keyed on it. Run uvicorn with `--no-proxy-headers` (both .bat files and READMEs do now); the app only reads the header when `TRUST_FORWARDED_FOR=true`. FastAPI's TestClient does **not** apply uvicorn's rewrite, so in-process tests cannot catch this class of bug — verify rate limiting against a real uvicorn server.
- Admin sessions and rate-limit state are per-process, in-memory singletons (`python-backend/admin_auth.py`): a server restart logs out every session **and** resets the limiter. Both behaviors are intended and covered by tests.
- Root `.gitignore` line `.env*` also ignores `.env.template`; it needs explicit negations (`!.env.template`, `!python-backend/.env.template`) placed after that line.
- The multipart image-upload endpoint requires `python-multipart`; importing `main` fails without it.

## Testing
- Tests run from `python-backend/`: `python -m pytest tests/`. The test module sets `RIZZ_MASTER_CODE`/`COOKIE_SECURE` **before** importing `main`, and isolates each test to a temp DB via a monkeypatched `CONTRIBUTORS_DB_PATH` — this only works because the SQLite store reads the env var at construction time, not via an import-time default arg.
- `sqlite3.OperationalError: database is locked` or spurious 409s in pytest usually mean an orphaned `python -m pytest` process (e.g. from a timed-out run) still holds `python-backend/data/contributors.db`. Kill stray python.exe before re-running (`tasklist`; `wmic` may return nothing — use `powershell Get-CimInstance Win32_Process`), then delete `python-backend/data` and `python-backend/uploads`.
- `python-backend/__pycache__/*.pyc` files are **tracked in git**; running pytest/py_compile rewrites them, so run `git checkout -- python-backend/__pycache__/` before finishing to keep the diff clean.

## Frontend conventions
- Shared navbar/footer/brand-modal/chatbot are injected at runtime by `/static/app.js`; each page's navbar links are duplicated per-page HTML, so a navbar change touches every page, while a footer change is one edit in `app.js`.
- The lucide CDN has no `github` brand icon: `app.js` swaps `data-lucide="github"` for an inline SVG only for elements present at load. Dynamically-rendered github icons must embed that inline SVG directly or they render nothing and log a console warning.
- Backend CSP limits `img-src` to `'self' data: github.com avatars.githubusercontent.com` — avatar/image hotlinks must come from those origins.

## Windows tooling quirks
- Windows system `curl` cannot open Git Bash `/tmp` paths: `-F "image=@/tmp/x.png"` fails silently (empty body / HTTP 000). Use project-relative paths for multipart upload tests.
- Backgrounding a server with `&` inside a terminal command keeps the call running until timeout — launch the server, then run checks in separate commands. The listening PID from `netstat -ano | grep :PORT` differs from the shell `$!` PID; kill by the netstat PID.
