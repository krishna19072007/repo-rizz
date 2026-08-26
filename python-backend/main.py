from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
