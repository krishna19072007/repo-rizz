# Repo Rizz — Frontend Preview Run Doc

## How to reproduce uncommitted artifacts

The `frontend/static/` directory must contain:
- `logo.png` — copy of `frontend/logo.png`
- `app.js` — copy of `frontend/app.js`
- `favicon.ico` — generated lime-colored favicon

If starting from a fresh checkout:
1. `mkdir -p frontend/static`
2. `cp frontend/logo.png frontend/static/logo.png`
3. `cp frontend/app.js frontend/static/app.js`
4. Generate `frontend/static/favicon.ico` (or copy from repo)

## How to run the frontend server

```bash
cd frontend && npx serve -l 3000 --no-clipboard
```

This serves the static HTML/CSS/JS version at `http://localhost:3000` with clean URL support (e.g. `/about` resolves to `about.html`).

### Windows detach

```bash
cd frontend && start //b npx.cmd serve -l 3000 --no-clipboard > ../.freebuff/serve.log 2>&1
```

**Important:** Do NOT use `serve -s` (SPA mode) — it serves `index.html` for all routes, breaking sub-pages.

## Pages

| Route | File | Description |
|-------|------|-------------|
| `/` | `index.html` | Landing page with hero, pipeline, radar, battle, CTA |
| `/about` | `about.html` | About page with project description |
| `/analyze` | `analyze.html` | Analysis results page (needs Python backend) |
| `/compare` | `compare.html` | Side-by-side repo comparison |
| `/history` | `history.html` | Analysis history (localStorage) |
| `/privacy` | `privacy.html` | Privacy policy placeholder |
| `/static/*` | `static/` | Logo, app.js, favicon |

## Backend dependency

The `/analyze` and `/compare` pages POST to `http://localhost:8000/analyze` (the Python backend). Start it separately:

```bash
cd python-backend && python -m uvicorn main:app --port 8000
```
