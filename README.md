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
python -m uvicorn main:app --reload --port 8000
```
*The backend will be running at http://localhost:8000*

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

### Backend (`python-backend/.env`)
| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | No | GitHub API token for higher rate limits |
| `GEMINI_API_KEY` | No | Google Gemini API key for AI insights |

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
