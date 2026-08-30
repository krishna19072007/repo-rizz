from fastapi import FastAPI, HTTPException
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

load_dotenv(); load_dotenv("../.env.local")

app = FastAPI()

import re
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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Ingest security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https://github.com https://avatars.githubusercontent.com; "
            "connect-src 'self' https://api.github.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "frame-ancestors 'none';"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

class AnalyzeRequest(BaseModel):
    owner: str
    name: str
    demo: bool = False

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Python backend is running"}

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
