# Repo Rizz

**Your GitHub repo has a reputation. Let's check it.**

Repo Rizz analyzes a public GitHub repository and evaluates its engineering health across 9 dimensions:

- Code Quality
- Security
- Documentation
- Testing
- Architecture
- Maintainability
- Activity
- Community
- Resume Readiness

## Architecture

Repo Rizz uses a **Two-Server Architecture**:
1. **Frontend**: A Next.js application that renders the 3D radar and UI.
2. **Backend**: A Python FastAPI server that handles GitHub fetching, static analysis, scoring, and AI integration.

## Quick Start (Local Development)

You must start both the backend and the frontend to run the full application.

### 1. Start the Python Backend
Open a terminal in the `python-backend` folder:
```bash
cd python-backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000 --no-proxy-headers
```
*The backend will be running at http://localhost:8000* (`--no-proxy-headers` stops uvicorn from trusting spoofable `X-Forwarded-For` IPs, keeping the admin login rate limiter accurate; behind a real reverse proxy, drop the flag and set `TRUST_FORWARDED_FOR=true` in the backend `.env` instead)

### 2. Start the Next.js Frontend
Open a second terminal in the project root:
```bash
npm install
npm run dev
```
*Open [http://localhost:3000](http://localhost:3000) in your browser.*

## Environment Variables

### Frontend (`.env.local` in root)
| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | No | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | No | Supabase anonymous key |

### Backend (`python-backend/.env` — copy from `python-backend/.env.template`)
| Variable | Required | Description |
|----------|----------|-------------|
| `RIZZ_MASTER_CODE` | For admin panel | Secret code to access the Rizz Master admin panel |
| `GITHUB_TOKEN` | No | GitHub API token for higher rate limits |
| `GEMINI_API_KEY` | No | Google Gemini API key for AI insights |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | No | Optional Supabase persistence (SQLite is the default) |
| `COOKIE_SECURE` | No | Set `true` when serving over HTTPS |

### Features

- **Contributors** — a public team directory at `/contributors` with a secure Rizz Master admin panel (add / edit / delete / reorder / custom image uploads).

## Features

- **9-Dimension Analysis** — Comprehensive engineering health scoring
- **Evidence-Based** — Every score backed by concrete findings
- **Resume Readiness** — Know if your project is portfolio-ready
- **Rizz Verdict** — Fun, data-driven summary
- **3D Visualization** — Unique repo fingerprint
- **Demo Mode** — Full experience without API calls
- **Mobile Responsive** — Works on all devices
- **AI-Enhanced** — Optional Gemini-powered insights

## Tech Stack

- Next.js (App Router)
- React Three Fiber
- Python (FastAPI)
- Google Generative AI (Gemini)
- Supabase (optional)

## License

MIT
