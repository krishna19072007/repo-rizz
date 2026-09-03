# Run Doc — Repo Rizz Preview

## How to Run

### Server: Python Backend (serves frontend + API)

```bash
cd python-backend
python -m uvicorn main:app --host 0.0.0.0 --port 3000
```

The Python backend (FastAPI/uvicorn) serves:
- **Frontend pages**: `/`, `/about`, `/analyze`, `/compare`, `/history`, `/privacy`
- **Static assets**: `/static/app.js`, `/static/logo.png`, `/static/favicon.ico`
- **API endpoints**: `POST /analyze`, `GET /health`

### Port
3000 (default)
