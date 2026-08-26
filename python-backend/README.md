# Repo Rizz - Python Backend

This is the FastAPI backend for Repo Rizz. It handles GitHub API orchestration, architectural analysis, engineering scoring, and Gemini AI insights.

## Windows Setup Instructions

Run the following commands in PowerShell to start the server locally:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys:
- `GEMINI_API_KEY`: Required for AI insights and verdict generation.
- `GITHUB_TOKEN`: Optional, but highly recommended to avoid rate limiting.
